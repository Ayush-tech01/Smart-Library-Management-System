from flask import (Flask, render_template, request, jsonify,
                   redirect, url_for, flash, session)
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)
from functools import wraps
from datetime import datetime

from config import Config
from models.user import UserModel
from models.book import Book
from models.member import Member
from models.transaction import Transaction
from models.review import ReviewModel
from models.reservation import ReservationModel
from models.wishlist import WishlistModel
from models.notification import NotificationModel
from models.analytics import AnalyticsModel
from models.book_request import BookRequestModel

# ── App setup ──────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config.from_object(Config)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

# ── Model instances ────────────────────────────────────────────────────────
user_model      = UserModel()
book_model      = Book()
member_model    = Member()
txn_model       = Transaction()
review_model    = ReviewModel()
reservation_model = ReservationModel()
wishlist_model  = WishlistModel()
notif_model     = NotificationModel()
analytics_model = AnalyticsModel()
request_model   = BookRequestModel()


@login_manager.user_loader
def load_user(user_id):
    return user_model.get_by_id(int(user_id))


# ── Custom decorators ──────────────────────────────────────────────────────
def staff_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_staff:
            flash('Access restricted to library staff.', 'danger')
            return redirect(url_for('portal'))
        return f(*args, **kwargs)
    return login_required(decorated)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return login_required(decorated)


# ── Context processor (inject unread count globally) ───────────────────────
@app.context_processor
def inject_globals():
    unread = 0
    if current_user.is_authenticated:
        unread = notif_model.get_unread_count(current_user.id)
    return dict(unread_notifications=unread, now=datetime.now())


# ══════════════════════════════════════════════════════════════════════════
# AUTH ROUTES
# ══════════════════════════════════════════════════════════════════════════
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard') if current_user.is_staff else url_for('portal'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))
        user = user_model.get_by_email(email)
        if user and user.check_password(password):
            login_user(user, remember=remember)
            user_model.update_last_login(user.id)
            flash(f'Welcome back, {user.name}! 👋', 'success')
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard') if user.is_staff else url_for('portal'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        phone    = request.form.get('phone', '').strip()
        if user_model.email_exists(email):
            flash('An account with this email already exists.', 'danger')
            return render_template('register.html')
        # Create member record first
        member_id = member_model.add_member(name, email, phone)
        # Create user linked to member
        user_model.create(name, email, password, role='member', member_id=member_id)
        flash('Account created! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ══════════════════════════════════════════════════════════════════════════
# DASHBOARD & ANALYTICS (staff only)
# ══════════════════════════════════════════════════════════════════════════
@app.route('/dashboard')
@staff_required
def dashboard():
    stats   = analytics_model.get_summary_stats()
    recent  = txn_model.get_all_transactions()[:8]
    overdue = txn_model.get_overdue_books()[:5]
    new_books = book_model.get_recently_added(5)
    pending_requests = request_model.count_pending()
    return render_template('dashboard.html', stats=stats, recent=recent,
                           overdue=overdue, new_books=new_books,
                           pending_requests=pending_requests)


@app.route('/analytics')
@staff_required
def analytics():
    return render_template('analytics.html')


@app.route('/analytics/data')
@staff_required
def analytics_data():
    return jsonify({
        'monthly_issues':      analytics_model.get_monthly_issues(),
        'category_dist':       analytics_model.get_category_distribution(),
        'top_books':           analytics_model.get_top_books(),
        'monthly_members':     analytics_model.get_monthly_members(),
        'fine_summary':        analytics_model.get_fine_summary(),
        'overdue_by_category': analytics_model.get_overdue_by_category(),
        'daily_activity':      analytics_model.get_daily_activity(),
    })


# ══════════════════════════════════════════════════════════════════════════
# BOOKS
# ══════════════════════════════════════════════════════════════════════════
@app.route('/books')
@login_required
def books():
    q        = request.args.get('q', '')
    category = request.args.get('category', '')
    avail    = request.args.get('available', '')
    if q or category or avail:
        all_books = book_model.search_books(q, category or None, avail == '1')
    else:
        all_books = book_model.get_all_books()
    categories = book_model.get_categories()
    ratings    = review_model.get_all_ratings()
    wishlisted = wishlist_model.get_wishlisted_ids(current_user.id) if current_user.is_member else set()
    return render_template('books.html', books=all_books, categories=categories,
                           ratings=ratings, wishlisted=wishlisted,
                           search=q, sel_category=category)


@app.route('/books/<int:book_id>')
@login_required
def book_detail(book_id):
    book = book_model.get_book_by_id(book_id)
    if not book:
        flash('Book not found.', 'danger')
        return redirect(url_for('books'))
    reviews       = review_model.get_by_book(book_id)
    avg, count    = review_model.get_avg_rating(book_id)
    user_review   = review_model.get_user_review(book_id, current_user.id)
    is_wishlisted = wishlist_model.is_wishlisted(current_user.id, book_id)
    members       = member_model.get_all_members() if current_user.is_staff else []
    return render_template('book_detail.html', book=book, reviews=reviews,
                           avg=avg, review_count=count,
                           user_review=user_review, is_wishlisted=is_wishlisted,
                           members=members)


@app.route('/books/add', methods=['POST'])
@staff_required
def add_book():
    d = request.form
    try:
        book_model.add_book(
            d['title'], d['author'], d['isbn'],
            d.get('publisher'), d.get('publication_year'),
            d.get('category'), int(d.get('total_copies', 1)),
            d.get('description'), d.get('language', 'English'),
            d.get('pages') or None, d.get('shelf_location')
        )
        flash('Book added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding book: {e}', 'danger')
    return redirect(url_for('books'))


@app.route('/books/update/<int:book_id>', methods=['POST'])
@staff_required
def update_book(book_id):
    d = request.form
    try:
        book_model.update_book(
            book_id, d['title'], d['author'], d['isbn'],
            d.get('publisher'), d.get('publication_year'),
            d.get('category'), d.get('total_copies') or None,
            d.get('description'), d.get('language'),
            d.get('pages') or None, d.get('shelf_location')
        )
        flash('Book updated successfully!', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    return redirect(url_for('books'))


@app.route('/books/delete/<int:book_id>')
@staff_required
def delete_book(book_id):
    try:
        book_model.delete_book(book_id)
        flash('Book deleted.', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    return redirect(url_for('books'))


@app.route('/books/search')
@login_required
def search_books():
    term = request.args.get('q', '')
    return jsonify(book_model.search_books(term))


@app.route('/books/<int:book_id>/json')
@login_required
def get_book_json(book_id):
    book = book_model.get_book_by_id(book_id)
    return (jsonify(book) if book else jsonify({'error': 'Not found'}), 200 if book else 404)


# ══════════════════════════════════════════════════════════════════════════
# REVIEWS
# ══════════════════════════════════════════════════════════════════════════
@app.route('/books/<int:book_id>/review', methods=['POST'])
@login_required
def add_review(book_id):
    rating = int(request.form.get('rating', 0))
    text   = request.form.get('review_text', '').strip()
    if not 1 <= rating <= 5:
        flash('Please select a rating (1–5 stars).', 'warning')
        return redirect(url_for('book_detail', book_id=book_id))
    review_model.add_review(book_id, current_user.id, rating, text or None)
    flash('Review submitted!', 'success')
    return redirect(url_for('book_detail', book_id=book_id))


@app.route('/reviews/delete/<int:review_id>', methods=['POST'])
@staff_required
def delete_review(review_id):
    review_model.delete(review_id)
    flash('Review removed.', 'success')
    return redirect(request.referrer or url_for('books'))


# ══════════════════════════════════════════════════════════════════════════
# MEMBERS
# ══════════════════════════════════════════════════════════════════════════
@app.route('/members')
@staff_required
def members():
    all_members = member_model.get_all_members()
    return render_template('members.html', members=all_members)


@app.route('/members/add', methods=['POST'])
@staff_required
def add_member():
    d = request.form
    try:
        email = d['email'].strip()
        if user_model.email_exists(email):
            flash('A user with this email already exists.', 'danger')
            return redirect(url_for('members'))
        member_id = member_model.add_member(d['name'], email, d.get('phone'))
        # Optionally create a login account for them
        if d.get('create_account') and d.get('temp_password'):
            user_model.create(d['name'], email, d['temp_password'], 'member', member_id)
        flash('Member added successfully!', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    return redirect(url_for('members'))


@app.route('/members/update/<int:member_id>', methods=['POST'])
@staff_required
def update_member(member_id):
    d = request.form
    try:
        member_model.update_member(member_id, d['name'], d['email'],
                                   d.get('phone'), d.get('status', 'active'))
        flash('Member updated!', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    return redirect(url_for('members'))


@app.route('/members/delete/<int:member_id>')
@staff_required
def delete_member(member_id):
    try:
        member_model.delete_member(member_id)
        flash('Member deleted.', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    return redirect(url_for('members'))


@app.route('/members/<int:member_id>/json')
@staff_required
def get_member_json(member_id):
    m = member_model.get_member_by_id(member_id)
    return (jsonify(m) if m else jsonify({'error': 'Not found'}), 200 if m else 404)


# ══════════════════════════════════════════════════════════════════════════
# TRANSACTIONS
# ══════════════════════════════════════════════════════════════════════════
@app.route('/transactions')
@staff_required
def transactions():
    all_txns = txn_model.get_all_transactions()
    books    = book_model.get_all_books()
    all_members = member_model.get_all_members()
    overdue_txns = txn_model.get_overdue_books()
    return render_template('transactions.html', transactions=all_txns,
                           books=books, members=all_members, overdue_transactions=overdue_txns)


@app.route('/transactions/issue', methods=['POST'])
@staff_required
def issue_book():
    d = request.form
    success, message = txn_model.issue_book(
        int(d['book_id']), int(d['member_id']), int(d.get('days', 14))
    )
    if success:
        # If member has a user account, notify them
        member = member_model.get_member_by_id(int(d['member_id']))
        if member:
            user = user_model.get_by_email(member['email'])
            if user:
                book = book_model.get_book_by_id(int(d['book_id']))
                notif_model.create(user.id, '📖 Book Issued',
                    f'"{book["title"]}" has been issued to you. Please return by the due date.',
                    'info')
    return jsonify({'success': success, 'message': message})


@app.route('/transactions/return/<int:txn_id>', methods=['GET', 'POST'])
@staff_required
def return_book(txn_id):
    method  = request.form.get('payment_method')
    result  = txn_model.return_book(txn_id, method)
    success, message = result[0], result[1]
    book_id = result[2] if success and len(result) > 2 else None
    if success and book_id:
        reservation_model.notify_next(book_id, notif_model)
    return jsonify({'success': success, 'message': message})


@app.route('/transactions/fine/pay/<int:txn_id>', methods=['POST'])
@staff_required
def pay_fine(txn_id):
    method = request.form.get('method', 'cash')
    txn_model.mark_fine_paid(txn_id, method)
    flash('Fine marked as paid.', 'success')
    return redirect(url_for('transactions'))


@app.route('/transactions/overdue')
@staff_required
def overdue_transactions():
    return jsonify(txn_model.get_overdue_books())


# ══════════════════════════════════════════════════════════════════════════
# RESERVATIONS
# ══════════════════════════════════════════════════════════════════════════
@app.route('/reservations')
@login_required
def reservations():
    if current_user.is_staff:
        all_res = reservation_model.get_all()
        return render_template('reservations.html', reservations=all_res, is_staff=True)
    else:
        my_res = reservation_model.get_by_member(current_user.id)
        return render_template('reservations.html', reservations=my_res, is_staff=False)


@app.route('/reservations/add', methods=['POST'])
@login_required
def add_reservation():
    book_id = int(request.form.get('book_id'))
    if not current_user.member_id:
        return jsonify({'success': False, 'message': 'No linked member account.'})
    success, message = reservation_model.reserve(book_id, current_user.id, current_user.member_id)
    return jsonify({'success': success, 'message': message})


@app.route('/reservations/cancel/<int:res_id>', methods=['POST'])
@login_required
def cancel_reservation(res_id):
    uid = None if current_user.is_staff else current_user.id
    success, message = reservation_model.cancel(res_id, uid)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('reservations'))


# ══════════════════════════════════════════════════════════════════════════
# WISHLIST
# ══════════════════════════════════════════════════════════════════════════
@app.route('/wishlist')
@login_required
def wishlist():
    items = wishlist_model.get_by_user(current_user.id)
    ratings = review_model.get_all_ratings()
    return render_template('wishlist.html', items=items, ratings=ratings)


@app.route('/wishlist/toggle/<int:book_id>', methods=['POST'])
@login_required
def toggle_wishlist(book_id):
    added = wishlist_model.toggle(current_user.id, book_id)
    return jsonify({'success': True, 'added': added,
                    'message': 'Added to wishlist' if added else 'Removed from wishlist'})


# ══════════════════════════════════════════════════════════════════════════
# NOTIFICATIONS
# ══════════════════════════════════════════════════════════════════════════
@app.route('/notifications')
@login_required
def notifications():
    notifs = notif_model.get_by_user(current_user.id)
    notif_model.mark_read(current_user.id)
    return render_template('notifications.html', notifications=notifs)


@app.route('/notifications/delete/<int:notif_id>', methods=['POST'])
@login_required
def delete_notification(notif_id):
    notif_model.delete(notif_id, current_user.id)
    return jsonify({'success': True})


# ══════════════════════════════════════════════════════════════════════════
# BOOK REQUESTS
# ══════════════════════════════════════════════════════════════════════════
@app.route('/book-requests')
@login_required
def book_requests():
    if current_user.is_staff:
        reqs = request_model.get_all()
    else:
        reqs = request_model.get_by_user(current_user.id)
    return render_template('book_requests.html', requests=reqs, is_staff=current_user.is_staff)


@app.route('/book-requests/new', methods=['POST'])
@login_required
def new_book_request():
    d = request.form
    request_model.create(current_user.id, d['title'], d.get('author'),
                         d.get('isbn'), d.get('reason'))
    notif_model.broadcast_to_staff(
        '📋 New Book Request',
        f'{current_user.name} requested: "{d["title"]}"',
        user_model, 'info'
    )
    flash('Book request submitted!', 'success')
    return redirect(url_for('book_requests'))


@app.route('/book-requests/update/<int:req_id>', methods=['POST'])
@staff_required
def update_book_request(req_id):
    status = request.form.get('status')
    note   = request.form.get('admin_note', '')
    request_model.update_status(req_id, status, note)
    flash(f'Request marked as {status}.', 'success')
    return redirect(url_for('book_requests'))


# ══════════════════════════════════════════════════════════════════════════
# MEMBER PORTAL & PROFILE
# ══════════════════════════════════════════════════════════════════════════
@app.route('/portal')
@login_required
def portal():
    if current_user.is_staff:
        return redirect(url_for('dashboard'))
    if not current_user.member_id:
        flash('No member profile linked to your account.', 'warning')
        return redirect(url_for('books'))
    txns        = txn_model.get_member_transactions(current_user.member_id)
    active      = [t for t in txns if t['status'] == 'issued']
    history     = [t for t in txns if t['status'] == 'returned']
    overdue     = [t for t in active if t['due_date'] < datetime.now().date()]
    my_res      = reservation_model.get_by_member(current_user.id)
    wl_count    = wishlist_model.count_by_user(current_user.id)
    member_info = member_model.get_member_by_id(current_user.member_id)
    return render_template('portal.html', active=active, history=history,
                           overdue=overdue, reservations=my_res,
                           wl_count=wl_count, member=member_info)


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update_info':
            name  = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            user_model.update_profile(current_user.id, name, email)
            if current_user.member_id:
                member_model.update_member(current_user.member_id, name, email,
                                           request.form.get('phone'))
            flash('Profile updated!', 'success')
        elif action == 'change_password':
            old = request.form.get('old_password')
            new = request.form.get('new_password')
            if current_user.check_password(old):
                user_model.change_password(current_user.id, new)
                flash('Password changed successfully!', 'success')
            else:
                flash('Incorrect current password.', 'danger')
        return redirect(url_for('profile'))
    member_info = member_model.get_member_by_id(current_user.member_id) if current_user.member_id else None
    return render_template('profile.html', member=member_info)


# ══════════════════════════════════════════════════════════════════════════
# USERS MANAGEMENT (admin only)
# ══════════════════════════════════════════════════════════════════════════
@app.route('/users')
@admin_required
def manage_users():
    all_users = user_model.get_all()
    return render_template('users.html', users=all_users)


@app.route('/users/toggle/<int:user_id>', methods=['POST'])
@admin_required
def toggle_user(user_id):
    if user_id == current_user.id:
        return jsonify({'success': False, 'message': "You can't deactivate yourself."})
    user_model.toggle_active(user_id)
    return jsonify({'success': True})


if __name__ == '__main__':
    user_model.seed_admin()
    app.run(debug=True)