from database import Database


class WishlistModel:
    def __init__(self):
        self.db = Database()

    def toggle(self, user_id, book_id):
        if self.is_wishlisted(user_id, book_id):
            self.db.execute_query("DELETE FROM wishlist WHERE user_id=%s AND book_id=%s", (user_id, book_id))
            return False  # removed
        else:
            self.db.execute_query("INSERT IGNORE INTO wishlist (user_id, book_id) VALUES (%s,%s)", (user_id, book_id))
            return True  # added

    def is_wishlisted(self, user_id, book_id):
        q = "SELECT id FROM wishlist WHERE user_id=%s AND book_id=%s"
        return bool(self.db.execute_query(q, (user_id, book_id), fetch=True))

    def get_by_user(self, user_id):
        q = """SELECT w.*, b.title, b.author, b.category, b.available_copies,
                      b.cover_url, b.isbn
               FROM wishlist w
               JOIN books b ON w.book_id = b.id
               WHERE w.user_id = %s
               ORDER BY w.added_at DESC"""
        return self.db.execute_query(q, (user_id,), fetch=True)

    def get_wishlisted_ids(self, user_id):
        q = "SELECT book_id FROM wishlist WHERE user_id=%s"
        rows = self.db.execute_query(q, (user_id,), fetch=True)
        return {r['book_id'] for r in rows}

    def count_by_user(self, user_id):
        q = "SELECT COUNT(*) AS cnt FROM wishlist WHERE user_id=%s"
        r = self.db.execute_query(q, (user_id,), fetch=True)
        return r[0]['cnt'] if r else 0
