from database import Database


class ReservationModel:
    def __init__(self):
        self.db = Database()

    def reserve(self, book_id, user_id, member_id):
        # Prevent duplicate active reservations
        check = """SELECT id FROM reservations
                   WHERE book_id=%s AND user_id=%s AND status IN ('pending','ready')"""
        if self.db.execute_query(check, (book_id, user_id), fetch=True):
            return False, "You already have an active reservation for this book."
        q = """INSERT INTO reservations (book_id, user_id, member_id)
               VALUES (%s, %s, %s)"""
        self.db.execute_query(q, (book_id, user_id, member_id))
        return True, "Book reserved successfully. You'll be notified when it's available."

    def cancel(self, reservation_id, user_id=None):
        if user_id:
            q = "UPDATE reservations SET status='cancelled' WHERE id=%s AND user_id=%s"
            self.db.execute_query(q, (reservation_id, user_id))
        else:
            q = "UPDATE reservations SET status='cancelled' WHERE id=%s"
            self.db.execute_query(q, (reservation_id,))
        return True, "Reservation cancelled."

    def get_by_member(self, user_id):
        q = """SELECT r.*, b.title AS book_title, b.author, b.cover_url
               FROM reservations r
               JOIN books b ON r.book_id = b.id
               WHERE r.user_id = %s
               ORDER BY r.reserved_at DESC"""
        return self.db.execute_query(q, (user_id,), fetch=True)

    def get_all(self):
        q = """SELECT r.*, b.title AS book_title, b.author,
                      m.name AS member_name, u.email AS member_email
               FROM reservations r
               JOIN books b ON r.book_id = b.id
               JOIN members m ON r.member_id = m.id
               JOIN users u ON r.user_id = u.id
               ORDER BY r.reserved_at DESC"""
        return self.db.execute_query(q, fetch=True)

    def get_pending_for_book(self, book_id):
        q = """SELECT r.*, u.name AS user_name, u.email AS user_email
               FROM reservations r
               JOIN users u ON r.user_id = u.id
               WHERE r.book_id = %s AND r.status = 'pending'
               ORDER BY r.reserved_at ASC"""
        return self.db.execute_query(q, (book_id,), fetch=True)

    def notify_next(self, book_id, notification_model):
        """Mark first-in-queue reservation as 'ready' and send notification."""
        pending = self.get_pending_for_book(book_id)
        if pending:
            first = pending[0]
            q = "UPDATE reservations SET status='ready', notified_at=NOW() WHERE id=%s"
            self.db.execute_query(q, (first['id'],))
            notification_model.create(
                first['user_id'],
                '📚 Your Reserved Book is Available!',
                f'Good news! A copy of a book you reserved is now available. Please visit the library within 3 days to collect it.',
                'success'
            )

    def fulfill(self, reservation_id):
        q = "UPDATE reservations SET status='fulfilled' WHERE id=%s"
        self.db.execute_query(q, (reservation_id,))

    def count_pending(self):
        q = "SELECT COUNT(*) AS cnt FROM reservations WHERE status='pending'"
        r = self.db.execute_query(q, fetch=True)
        return r[0]['cnt'] if r else 0
