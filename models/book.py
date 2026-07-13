from database import Database


class Book:
    def __init__(self):
        self.db = Database()

    def add_book(self, title, author, isbn, publisher=None, publication_year=None,
                 category=None, total_copies=1, description=None, language='English',
                 pages=None, shelf_location=None):
        cover_url = self._get_cover(isbn)
        q = """INSERT INTO books
               (title, author, isbn, publisher, publication_year, category,
                total_copies, available_copies, cover_url, description, language, pages, shelf_location)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        return self.db.execute_query(q, (title, author, isbn, publisher, publication_year,
                                         category, total_copies, total_copies, cover_url,
                                         description, language, pages, shelf_location))

    def _get_cover(self, isbn):
        """Build Open Library cover URL from ISBN (no API call needed)."""
        if isbn:
            clean = isbn.replace('-', '').replace(' ', '')
            if clean:
                return f"https://covers.openlibrary.org/b/isbn/{clean}-M.jpg"
        return None

    def get_all_books(self):
        q = "SELECT * FROM books ORDER BY created_at DESC"
        return self.db.execute_query(q, fetch=True)

    def get_book_by_id(self, book_id):
        q = "SELECT * FROM books WHERE id = %s"
        rows = self.db.execute_query(q, (book_id,), fetch=True)
        return rows[0] if rows else None

    def update_book(self, book_id, title, author, isbn, publisher=None,
                    publication_year=None, category=None, total_copies=None,
                    description=None, language=None, pages=None, shelf_location=None):
        current = self.get_book_by_id(book_id)
        if not current:
            return False
        if total_copies and int(total_copies) != current['total_copies']:
            diff = int(total_copies) - current['total_copies']
            new_avail = max(0, current['available_copies'] + diff)
        else:
            total_copies = current['total_copies']
            new_avail = current['available_copies']
        cover_url = self._get_cover(isbn) if isbn != current['isbn'] else current.get('cover_url')
        q = """UPDATE books SET title=%s, author=%s, isbn=%s, publisher=%s,
               publication_year=%s, category=%s, total_copies=%s, available_copies=%s,
               cover_url=%s, description=%s, language=%s, pages=%s, shelf_location=%s
               WHERE id=%s"""
        self.db.execute_query(q, (title, author, isbn, publisher, publication_year,
                                   category, total_copies, new_avail, cover_url,
                                   description, language, pages, shelf_location, book_id))
        return True

    def delete_book(self, book_id):
        self.db.execute_query("DELETE FROM books WHERE id=%s", (book_id,))
        return True

    def search_books(self, term, category=None, available_only=False):
        conditions = ["(title LIKE %s OR author LIKE %s OR isbn LIKE %s OR category LIKE %s)"]
        pattern = f"%{term}%"
        params = [pattern, pattern, pattern, pattern]
        if category:
            conditions.append("category = %s")
            params.append(category)
        if available_only:
            conditions.append("available_copies > 0")
        q = f"SELECT * FROM books WHERE {' AND '.join(conditions)} ORDER BY title ASC"
        return self.db.execute_query(q, tuple(params), fetch=True)

    def get_categories(self):
        q = "SELECT DISTINCT category FROM books WHERE category IS NOT NULL ORDER BY category"
        rows = self.db.execute_query(q, fetch=True)
        return [r['category'] for r in rows]

    def get_recently_added(self, limit=5):
        q = "SELECT * FROM books ORDER BY created_at DESC LIMIT %s"
        return self.db.execute_query(q, (limit,), fetch=True)