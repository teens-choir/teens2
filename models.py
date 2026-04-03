from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='member')  # 'admin' or 'member'
    voice_part = db.Column(db.String(50), nullable=False, default='Normal')  # 'Soprano', 'Alto', 'Normal'

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Music(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    link = db.Column(db.String(500), nullable=False)  # URL to PDF/MP3
    voice_part = db.Column(db.String(50), nullable=False)  # 'Soprano', 'Alto', 'Normal', or 'All'

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=db.func.current_date())  # Assuming one per day; adjust for sessions
    present = db.Column(db.Boolean, default=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    voice_part = db.Column(db.String(50), nullable=True)  # 'Soprano', 'Alto', 'Normal', or None for all
    timestamp = db.Column(db.DateTime, default=db.func.now())
