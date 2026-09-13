import bcrypt
from flask_login import UserMixin

from ..extensions import db, login_manager

# admin      — everything, including money and settings
# assistant  — day to day: bookings, orders, the menu, photos. No money screens,
#              no user accounts, no site settings.
# therapist  — their own schedule and nothing else.
ROLES = ["admin", "assistant", "therapist"]
ROLE_LABELS = {
    "admin": "Owner / manager — full access",
    "assistant": "Assistant — bookings, orders and content, no money screens",
    "therapist": "Therapist — sees only their own schedule",
}


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(12), nullable=False, default="admin")
    name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True)
    pw_hash = db.Column(db.String(80), nullable=False)
    # A therapist login is tied to the therapist it belongs to, so the
    # schedule screen knows whose bookings to show.
    therapist_id = db.Column(db.Integer, db.ForeignKey("therapists.id"))
    is_active_flag = db.Column(db.Boolean, default=True)

    therapist = db.relationship("Therapist")

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

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_staff(self):
        """Can reach the day-to-day admin screens."""
        return self.role in ("admin", "assistant")


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
