from datetime import datetime

from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_deceased = db.Column(db.Boolean, default=False)

    accounts = db.relationship("Account", backref="user", lazy=True)
    trusted_contacts = db.relationship("TrustedContact", backref="user", lazy=True)
    execution_logs = db.relationship("ExecutionLog", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    identifier = db.Column(db.String(120), nullable=False)
    action = db.Column(db.String(80), nullable=False)  # delete, memorialize, archive, none
    notes = db.Column(db.Text)
    status = db.Column(db.String(40), default="active")

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    logs = db.relationship("ExecutionLog", backref="account", lazy=True)


class TrustedContact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    relationship = db.Column(db.String(80))
    email = db.Column(db.String(120), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


class ExecutionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey("account.id"), nullable=True)
    action_taken = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
