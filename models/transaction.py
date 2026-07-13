from database import Database
from datetime import datetime, timedelta


class Transaction:
    def __init__(self):
        self.db = Database()

    def issue_book(self, book_id, member_id, days=14):
        q = "SELECT available_copies FROM books WHERE id=%s"
        book = self.db.execute_query(q, (book_id,), fetch=True)
        if not book or book[0]['available_copies'] <= 0:
            return False, "Book not available for issue."

        issue_date = datetime.now().date()
        due_date = issue_date + timedelta(days=days)
        try:
            tid = self.db.execute_query(
                "INSERT INTO transactions (book_id,member_id,issue_date,due_date,status) VALUES(%s,%s,%s,%s,'issued')",
                (book_id, member_id, issue_date, due_date)
            )
            self.db.execute_query("UPDATE books SET available_copies=available_copies-1 WHERE id=%s", (book_id,))
            return True, f"Book issued. Due: {due_date}. Transaction #{tid}"
        except Exception as e:
            return False, str(e)

    def return_book(self, transaction_id, payment_method=None):
        rows = self.db.execute_query(
            "SELECT * FROM transactions WHERE id=%s AND status!='returned'",
            (transaction_id,), fetch=True
        )
        if not rows:
            return False, "Transaction not found or already returned."
        txn = rows[0]
        return_date = datetime.now().date()
        fine = 0
        if return_date > txn['due_date']:
            fine = (return_date - txn['due_date']).days * 10  # ₹10/day

        fine_paid = fine == 0  # No fine means auto-paid
        self.db.execute_query(
            "UPDATE transactions SET return_date=%s, fine_amount=%s, status='returned', fine_paid=%s, payment_method=%s WHERE id=%s",
            (return_date, fine, fine_paid, payment_method, transaction_id)
        )
        self.db.execute_query(
            "UPDATE books SET available_copies=available_copies+1 WHERE id=%s",
            (txn['book_id'],)
        )
        msg = f"Book returned. Fine: ₹{fine}" if fine > 0 else "Book returned successfully."
        return True, msg, txn['book_id']

    def mark_fine_paid(self, transaction_id, method='cash'):
        self.db.execute_query(
            "UPDATE transactions SET fine_paid=TRUE, payment_method=%s WHERE id=%s",
            (method, transaction_id)
        )
        return True

    def get_all_transactions(self):
        q = """SELECT t.*, b.title AS book_title, b.cover_url,
                      m.name AS member_name, m.email AS member_email
               FROM transactions t
               JOIN books b ON t.book_id=b.id
               JOIN members m ON t.member_id=m.id
               ORDER BY t.created_at DESC"""
        return self.db.execute_query(q, fetch=True)

    def get_member_transactions(self, member_id):
        q = """SELECT t.*, b.title AS book_title, b.author, b.category, b.cover_url
               FROM transactions t
               JOIN books b ON t.book_id=b.id
               WHERE t.member_id=%s ORDER BY t.created_at DESC"""
        return self.db.execute_query(q, (member_id,), fetch=True)

    def get_overdue_books(self):
        q = """SELECT t.*, b.title AS book_title, m.name AS member_name,
                      m.email AS member_email,
                      DATEDIFF(CURDATE(), t.due_date) AS days_overdue
               FROM transactions t
               JOIN books b ON t.book_id=b.id
               JOIN members m ON t.member_id=m.id
               WHERE t.due_date<CURDATE() AND t.status='issued'
               ORDER BY t.due_date ASC"""
        return self.db.execute_query(q, fetch=True)

    def get_transaction_by_id(self, txn_id):
        q = """SELECT t.*, b.title AS book_title, m.name AS member_name
               FROM transactions t
               JOIN books b ON t.book_id=b.id
               JOIN members m ON t.member_id=m.id
               WHERE t.id=%s"""
        rows = self.db.execute_query(q, (txn_id,), fetch=True)
        return rows[0] if rows else None