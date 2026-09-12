import bcrypt
from flask_login import UserMixin
from ..extensions import db, login_manager


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(10), nullable=False, default="admin")  # admin | staff
    name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True)
    pw_hash = db.Column(db.String(80), nullable=False)
    is_active_flag = db.Column(db.Boolean, default=True)

    def set_password(self, pw: str):
        self.pw_hash = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

    def check_password(self, pw: str) -> bool:
        try:
            return bcrypt.checkpw(pw.encode(), self.pw_hash.encode())
        except ValueError:
            return False

    @property
    def is_active(self):
        return self.is_active_flag


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
