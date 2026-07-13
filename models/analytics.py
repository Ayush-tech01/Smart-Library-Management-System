from database import Database


class AnalyticsModel:
    def __init__(self):
        self.db = Database()

    def get_monthly_issues(self, months=6):
        q = """SELECT DATE_FORMAT(issue_date,'%%Y-%%m') AS month,
                      COUNT(*) AS count
               FROM transactions
               WHERE issue_date >= DATE_SUB(CURDATE(), INTERVAL %s MONTH)
               GROUP BY month ORDER BY month ASC"""
        return self.db.execute_query(q, (months,), fetch=True)

    def get_category_distribution(self):
        q = """SELECT COALESCE(category,'Uncategorized') AS category,
                      COUNT(*) AS count
               FROM books GROUP BY category ORDER BY count DESC LIMIT 10"""
        return self.db.execute_query(q, fetch=True)

    def get_top_books(self, limit=8):
        q = """SELECT b.title, b.author, COUNT(t.id) AS borrow_count
               FROM books b
               LEFT JOIN transactions t ON b.id = t.book_id
               GROUP BY b.id ORDER BY borrow_count DESC LIMIT %s"""
        return self.db.execute_query(q, (limit,), fetch=True)

    def get_monthly_members(self, months=6):
        q = """SELECT DATE_FORMAT(membership_date,'%%Y-%%m') AS month,
                      COUNT(*) AS count
               FROM members
               WHERE membership_date >= DATE_SUB(CURDATE(), INTERVAL %s MONTH)
               GROUP BY month ORDER BY month ASC"""
        return self.db.execute_query(q, (months,), fetch=True)

    def get_fine_summary(self):
        q = """SELECT
                  SUM(fine_amount) AS total_fines,
                  SUM(CASE WHEN fine_paid=TRUE THEN fine_amount ELSE 0 END) AS collected,
                  SUM(CASE WHEN fine_paid=FALSE AND fine_amount>0 THEN fine_amount ELSE 0 END) AS pending
               FROM transactions WHERE status='returned'"""
        rows = self.db.execute_query(q, fetch=True)
        return rows[0] if rows else {'total_fines': 0, 'collected': 0, 'pending': 0}

    def get_daily_activity(self, days=30):
        q = """SELECT DATE(issue_date) AS day, COUNT(*) AS issues
               FROM transactions
               WHERE issue_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
               GROUP BY day ORDER BY day ASC"""
        return self.db.execute_query(q, (days,), fetch=True)

    def get_overdue_by_category(self):
        q = """SELECT COALESCE(b.category,'Uncategorized') AS category,
                      COUNT(*) AS count
               FROM transactions t
               JOIN books b ON t.book_id = b.id
               WHERE t.due_date < CURDATE() AND t.status='issued'
               GROUP BY category ORDER BY count DESC"""
        return self.db.execute_query(q, fetch=True)

    def get_summary_stats(self):
        """Quick stats for dashboard cards including month-on-month changes."""
        q = """SELECT
            (SELECT COUNT(*) FROM books) AS total_books,
            (SELECT COUNT(*) FROM members WHERE status='active') AS total_members,
            (SELECT COUNT(*) FROM transactions WHERE status='issued') AS issued_books,
            (SELECT COUNT(*) FROM transactions WHERE due_date < CURDATE() AND status='issued') AS overdue_books,
            (SELECT COUNT(*) FROM reservations WHERE status='pending') AS pending_reservations,
            (SELECT COALESCE(SUM(fine_amount),0) FROM transactions WHERE fine_paid=FALSE AND fine_amount>0) AS pending_fines,
            (SELECT COUNT(*) FROM transactions WHERE MONTH(issue_date)=MONTH(CURDATE()) AND YEAR(issue_date)=YEAR(CURDATE())) AS issues_this_month,
            (SELECT COUNT(*) FROM transactions WHERE MONTH(issue_date)=MONTH(DATE_SUB(CURDATE(),INTERVAL 1 MONTH)) AND YEAR(issue_date)=YEAR(DATE_SUB(CURDATE(),INTERVAL 1 MONTH))) AS issues_last_month
        """
        rows = self.db.execute_query(q, fetch=True)
        return rows[0] if rows else {}
