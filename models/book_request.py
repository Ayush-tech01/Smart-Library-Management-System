from database import Database


class BookRequestModel:
    def __init__(self):
        self.db = Database()

    def create(self, user_id, title, author=None, isbn=None, reason=None):
        q = """INSERT INTO book_requests (user_id, title, author, isbn, reason)
               VALUES (%s, %s, %s, %s, %s)"""
        return self.db.execute_query(q, (user_id, title, author, isbn, reason))

    def get_all(self):
        q = """SELECT br.*, u.name AS user_name, u.email AS user_email
               FROM book_requests br
               JOIN users u ON br.user_id = u.id
               ORDER BY br.created_at DESC"""
        return self.db.execute_query(q, fetch=True)

    def get_by_user(self, user_id):
        q = """SELECT * FROM book_requests WHERE user_id=%s
               ORDER BY created_at DESC"""
        return self.db.execute_query(q, (user_id,), fetch=True)

    def update_status(self, request_id, status, admin_note=None):
        q = "UPDATE book_requests SET status=%s, admin_note=%s WHERE id=%s"
        self.db.execute_query(q, (status, admin_note, request_id))

    def count_pending(self):
        q = "SELECT COUNT(*) AS cnt FROM book_requests WHERE status='pending'"
        r = self.db.execute_query(q, fetch=True)
        return r[0]['cnt'] if r else 0
