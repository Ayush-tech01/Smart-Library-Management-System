from database import Database
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class User:
    """Represents an authenticated user. Compatible with Flask-Login."""

    # Flask-Login interface
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return self._is_active

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    # Convenience role checks
    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_staff(self):
        return self.role in ('admin', 'librarian')

    @property
    def is_member(self):
        return self.role == 'member'

    @property
    def avatar_initial(self):
        return self.name[0].upper() if self.name else 'U'

    @classmethod
    def from_dict(cls, data):
        """Build a User instance from a database row dict."""
        u = cls()
        u.id = data['id']
        u.name = data['name']
        u.email = data['email']
        u.password_hash = data['password_hash']
        u.role = data['role']
        u.member_id = data.get('member_id')
        u.avatar_color = data.get('avatar_color') or '#2d6a4f'
        u._is_active = bool(data.get('is_active', True))
        u.last_login = data.get('last_login')
        u.created_at = data.get('created_at')
        return u
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class UserModel:
    """Database operations for users."""

    def __init__(self):
        self.db = Database()

    def create(self, name, email, password, role='member', member_id=None):
        pw = generate_password_hash(password)
        q = """INSERT INTO users (name, email, password_hash, role, member_id)
               VALUES (%s, %s, %s, %s, %s)"""
        return self.db.execute_query(q, (name, email, pw, role, member_id))

    def get_by_email(self, email):
        q = "SELECT * FROM users WHERE email = %s AND is_active = TRUE"
        rows = self.db.execute_query(q, (email,), fetch=True)
        return User.from_dict(rows[0]) if rows else None

    def get_by_id(self, user_id):
        q = "SELECT * FROM users WHERE id = %s"
        rows = self.db.execute_query(q, (user_id,), fetch=True)
        return User.from_dict(rows[0]) if rows else None

    def email_exists(self, email):
        q = "SELECT id FROM users WHERE email = %s"
        return bool(self.db.execute_query(q, (email,), fetch=True))

    def update_last_login(self, user_id):
        q = "UPDATE users SET last_login = %s WHERE id = %s"
        self.db.execute_query(q, (datetime.now(), user_id))

    def get_all(self):
        q = """SELECT id, name, email, role, is_active, created_at, last_login, member_id
               FROM users ORDER BY created_at DESC"""
        return self.db.execute_query(q, fetch=True)

    def toggle_active(self, user_id):
        q = "UPDATE users SET is_active = NOT is_active WHERE id = %s"
        self.db.execute_query(q, (user_id,))

    def update_profile(self, user_id, name, email):
        q = "UPDATE users SET name = %s, email = %s WHERE id = %s"
        self.db.execute_query(q, (name, email, user_id))

    def change_password(self, user_id, new_password):
        pw = generate_password_hash(new_password)
        q = "UPDATE users SET password_hash = %s WHERE id = %s"
        self.db.execute_query(q, (pw, user_id))

    def seed_admin(self):
        """Auto-create the default admin if none exists."""
        q = "SELECT id FROM users WHERE role = 'admin' LIMIT 1"
        if not self.db.execute_query(q, fetch=True):
            self.create('Library Admin', 'admin@library.com', 'Admin@2024', 'admin')
            print("[OK] Default admin seeded: admin@library.com / Admin@2024")
