from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Music, Attendance, Message
import os

app = Flask(__name__)
import os

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///choir.db')
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_admins():
    admins = [
        {'username': 'eyuelg', 'password': 'choir2123'},
        {'username': 'yegetaa', 'password': 'choir3212'},
        {'username': 'fiker', 'password': 'choir6712'},
        {'username': 'lidiya', 'password': 'choir6745'}
    ]
    for admin in admins:
        if not User.query.filter_by(username=admin['username']).first():
            user = User(username=admin['username'], role='admin', voice_part='Normal')
            user.set_password(admin['password'])
            db.session.add(user)
    db.session.commit()

with app.app_context():
    db.create_all()
    init_admins()

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('member_home'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    if User.query.filter_by(username=username).first():
        flash('Username exists')
        return redirect(url_for('login'))
    user = User(username=username, role='member', voice_part='Normal')
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return redirect(url_for('member_home'))

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    old_password = request.form['old_password']
    new_password = request.form['new_password']
    if current_user.check_password(old_password):
        current_user.set_password(new_password)
        db.session.commit()
        flash('Password changed')
    else:
        flash('Invalid old password')
    return redirect(request.referrer)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('member_home'))
    members = User.query.filter_by(role='member').all()
    musics = Music.query.all()
    messages = Message.query.order_by(Message.timestamp.desc()).all()
    attendances = Attendance.query.filter_by(date=db.func.current_date()).all()
    return render_template('admin/dashboard.html', members=members, musics=musics, messages=messages, attendances=attendances)

@app.route('/admin/assign_voice/<int:user_id>/<voice>')
@login_required
def assign_voice(user_id, voice):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'})
    user = User.query.get(user_id)
    if user:
        user.voice_part = voice
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/toggle_attendance/<int:user_id>', methods=['POST'])
@login_required
def toggle_attendance(user_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'})
    attendance = Attendance.query.filter_by(user_id=user_id, date=db.func.current_date()).first()
    if not attendance:
        attendance = Attendance(user_id=user_id, present=False)
        db.session.add(attendance)
    attendance.present = not attendance.present
    db.session.commit()
    return jsonify({'present': attendance.present})

@app.route('/admin/send_message', methods=['POST'])
@login_required
def send_message():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'})
    content = request.form['content']
    voice_part = request.form.get('voice_part')
    message = Message(content=content, voice_part=voice_part)
    db.session.add(message)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_music', methods=['POST'])
@login_required
def add_music():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'})
    title = request.form['title']
    link = request.form['link']
    voice_part = request.form['voice_part']
    music = Music(title=title, link=link, voice_part=voice_part)
    db.session.add(music)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/member/home')
@login_required
def member_home():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    musics = Music.query.filter((Music.voice_part == current_user.voice_part) | (Music.voice_part == 'All')).all()
    messages = Message.query.filter((Message.voice_part == current_user.voice_part) | (Message.voice_part.is_(None))).order_by(Message.timestamp.desc()).limit(10).all()
    attendance_count = Attendance.query.filter_by(user_id=current_user.id, present=True).count()
    total_rehearsals = Attendance.query.filter_by(user_id=current_user.id).count()
    progress = (attendance_count / total_rehearsals * 100) if total_rehearsals > 0 else 0
    return render_template('member/home.html', musics=musics, messages=messages, progress=progress, voice_part=current_user.voice_part)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
