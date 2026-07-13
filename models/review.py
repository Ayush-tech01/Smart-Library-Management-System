from database import Database


class ReviewModel:
    def __init__(self):
        self.db = Database()

    def add_review(self, book_id, user_id, rating, review_text=None):
        q = """INSERT INTO reviews (book_id, user_id, rating, review_text)
               VALUES (%s, %s, %s, %s)
               ON DUPLICATE KEY UPDATE rating = %s, review_text = %s"""
        return self.db.execute_query(q, (book_id, user_id, rating, review_text, rating, review_text))

    def get_by_book(self, book_id):
        q = """SELECT r.*, u.name AS user_name, u.avatar_color
               FROM reviews r
               JOIN users u ON r.user_id = u.id
               WHERE r.book_id = %s
               ORDER BY r.created_at DESC"""
        return self.db.execute_query(q, (book_id,), fetch=True)

    def get_avg_rating(self, book_id):
        q = "SELECT AVG(rating) AS avg_rating, COUNT(*) AS total FROM reviews WHERE book_id = %s"
        result = self.db.execute_query(q, (book_id,), fetch=True)
        if result and result[0]['avg_rating']:
            return round(float(result[0]['avg_rating']), 1), result[0]['total']
        return 0.0, 0

    def get_user_review(self, book_id, user_id):
        q = "SELECT * FROM reviews WHERE book_id = %s AND user_id = %s"
        rows = self.db.execute_query(q, (book_id, user_id), fetch=True)
        return rows[0] if rows else None

    def delete(self, review_id):
        q = "DELETE FROM reviews WHERE id = %s"
        self.db.execute_query(q, (review_id,))

    def get_all_ratings(self):
        """Returns avg rating per book_id — used in book listings."""
        q = """SELECT book_id, ROUND(AVG(rating),1) AS avg_rating, COUNT(*) AS review_count
               FROM reviews GROUP BY book_id"""
        rows = self.db.execute_query(q, fetch=True)
        return {r['book_id']: {'avg': r['avg_rating'], 'count': r['review_count']} for r in rows}
