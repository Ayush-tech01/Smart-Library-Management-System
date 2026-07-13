from database import Database


class NotificationModel:
    def __init__(self):
        self.db = Database()

    def create(self, user_id, title, message, notif_type='info'):
        q = """INSERT INTO notifications (user_id, title, message, type)
               VALUES (%s, %s, %s, %s)"""
        return self.db.execute_query(q, (user_id, title, message, notif_type))

    def get_by_user(self, user_id, limit=50):
        q = """SELECT * FROM notifications WHERE user_id=%s
               ORDER BY created_at DESC LIMIT %s"""
        return self.db.execute_query(q, (user_id, limit), fetch=True)

    def get_unread_count(self, user_id):
        q = "SELECT COUNT(*) AS cnt FROM notifications WHERE user_id=%s AND is_read=FALSE"
        r = self.db.execute_query(q, (user_id,), fetch=True)
        return r[0]['cnt'] if r else 0

    def mark_read(self, user_id):
        q = "UPDATE notifications SET is_read=TRUE WHERE user_id=%s AND is_read=FALSE"
        self.db.execute_query(q, (user_id,))

    def mark_one_read(self, notif_id, user_id):
        q = "UPDATE notifications SET is_read=TRUE WHERE id=%s AND user_id=%s"
        self.db.execute_query(q, (notif_id, user_id))

    def delete(self, notif_id, user_id):
        q = "DELETE FROM notifications WHERE id=%s AND user_id=%s"
        self.db.execute_query(q, (notif_id, user_id))

    def broadcast_to_staff(self, title, message, user_model, notif_type='info'):
        """Send a notification to all admin/librarian users."""
        users = user_model.get_all()
        for u in users:
            if u['role'] in ('admin', 'librarian'):
                self.create(u['id'], title, message, notif_type)
