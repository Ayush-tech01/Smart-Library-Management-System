from database import Database
from datetime import datetime


class Member:
    def __init__(self):
        self.db = Database()

    def add_member(self, name, email, phone=None, address=None):
        q = """INSERT INTO members (name, email, phone, membership_date)
               VALUES (%s, %s, %s, %s)"""
        return self.db.execute_query(q, (name, email, phone, datetime.now().date()))

    def get_all_members(self):
        q = "SELECT * FROM members ORDER BY created_at DESC"
        return self.db.execute_query(q, fetch=True)

    def get_member_by_id(self, member_id):
        q = "SELECT * FROM members WHERE id = %s"
        rows = self.db.execute_query(q, (member_id,), fetch=True)
        return rows[0] if rows else None

    def get_member_by_email(self, email):
        q = "SELECT * FROM members WHERE email = %s"
        rows = self.db.execute_query(q, (email,), fetch=True)
        return rows[0] if rows else None

    def update_member(self, member_id, name, email, phone=None, status=None):
        q = """UPDATE members SET name=%s, email=%s, phone=%s, status=%s WHERE id=%s"""
        self.db.execute_query(q, (name, email, phone, status or 'active', member_id))
        return True

    def delete_member(self, member_id):
        self.db.execute_query("DELETE FROM members WHERE id=%s", (member_id,))
        return True

    def get_member_stats(self, member_id):
        """Returns borrow counts and fine total for a specific member."""
        q = """SELECT
            COUNT(*) AS total_borrows,
            SUM(CASE WHEN status='issued' THEN 1 ELSE 0 END) AS active_borrows,
            SUM(CASE WHEN due_date < CURDATE() AND status='issued' THEN 1 ELSE 0 END) AS overdue,
            COALESCE(SUM(CASE WHEN fine_paid=FALSE THEN fine_amount ELSE 0 END),0) AS pending_fine
            FROM transactions WHERE member_id=%s"""
        rows = self.db.execute_query(q, (member_id,), fetch=True)
        return rows[0] if rows else {}