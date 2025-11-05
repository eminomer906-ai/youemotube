import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime

# --- DİZİN AYARLARI ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Flask uygulaması
app = Flask(__name__)
app.secret_key = "youemotube_super_secret_2025"

# --- KLASÖRLER ---
video_folder = os.path.join(STATIC_DIR, "videos")
avatar_folder = os.path.join(STATIC_DIR, "avatars")

# Klasör yoksa oluştur
for folder in [video_folder, avatar_folder]:
    if not os.path.exists(folder):
        os.makedirs(folder)

app.config['VIDEO_FOLDER'] = video_folder
app.config['AVATAR_FOLDER'] = avatar_folder
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'youemotube.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- DATABASE ---
db = SQLAlchemy(app)

# --- MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    username = db.Column(db.String(100), nullable=True)
    avatar = db.Column(db.String(300), nullable=True)
    followers = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text, nullable=True)
    filename = db.Column(db.String(300), nullable=False)
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    views = db.Column(db.Integer, default=0)
    likes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploader = db.relationship('User', backref='videos')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('video.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    video = db.relationship('Video', backref='comments')
    user = db.relationship('User')

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    channel_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# --- INITIAL SETUP ---
with app.app_context():
    db.create_all()
    admin_email = "eminomer906@gmail.com"
    admin = User.query.filter_by(email=admin_email).first()
    if not admin:
        admin = User(email=admin_email, username="Admin", is_admin=True)
        db.session.add(admin)
        db.session.commit()

# --- HELPERS ---
def current_user():
    email = session.get('user_email')
    if not email:
        return None
    return User.query.filter_by(email=email).first()

# --- ROUTES ---
@app.route('/')
def index():
    q = request.args.get('q','').strip()
    if q:
        videos = Video.query.filter(Video.title.ilike(f"%{q}%")).order_by(Video.created_at.desc()).all()
    else:
        videos = Video.query.order_by(Video.created_at.desc()).all()
    user = current_user()
    return render_template('index.html', videos=videos, user=user, q=q)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email','').strip().lower()
        if not email.endswith('@gmail.com'):
            flash("✔️ Sadece Gmail adresi ile kayıt olunabilir.")
            return redirect(url_for('register'))
        existing = User.query.filter_by(email=email).first()
        if existing:
            session['user_email'] = existing.email
            flash("Giriş yapıldı.")
            return redirect(url_for('index'))
        username = email.split('@')[0]
        user = User(email=email, username=username)
        db.session.add(user)
        db.session.commit()
        session['user_email'] = user.email
        flash("Hesap oluşturuldu ve giriş yapıldı.")
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email','').strip().lower()
        password = request.form.get('password','').strip()
        if email == "eminomer906@gmail.com" and password == "emin1234sensin":
            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(email=email, username="Admin", is_admin=True)
                db.session.add(user)
                db.session.commit()
            session['user_email'] = user.email
            flash("Admin olarak giriş yapıldı.")
            return redirect(url_for('index'))
        if not email.endswith('@gmail.com'):
            flash("Lütfen Gmail adresi girin.")
            return redirect(url_for('login'))
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email, username=email.split('@')[0])
            db.session.add(user)
            db.session.commit()
        session['user_email'] = user.email
        flash("Giriş başarılı.")
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_email', None)
    flash("Çıkış yapıldı.")
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET','POST'])
def upload():
    user = current_user()
    if not user:
        flash("Video yüklemek için giriş yapın.")
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form.get('title','').strip()
        description = request.form.get('description','').strip()
        file = request.files.get('video')
        if not title:
            flash("Video başlığı gerekli.")
            return redirect(url_for('upload'))
        if not file or file.filename == '':
            flash("Video dosyası seçin.")
            return redirect(url_for('upload'))
        filename = secure_filename(f"{int(datetime.utcnow().timestamp())}_{file.filename}")
        save_path = os.path.join(app.config['VIDEO_FOLDER'], filename)
        file.save(save_path)
        video = Video(title=title, description=description, filename=filename, uploader_id=user.id)
        db.session.add(video)
        db.session.commit()
        flash("Video başarıyla yüklendi.")
        return redirect(url_for('view_video', video_id=video.id))
    return render_template('upload.html', user=user)

@app.route('/video/<int:video_id>', methods=['GET','POST'])
def view_video(video_id):
    video = Video.query.get_or_404(video_id)
    if request.method == 'GET':
        video.views += 1
        db.session.commit()
    user = current_user()
    if request.method == 'POST':
        if not user:
            flash("Yorum yapmak için giriş yapın.")
            return redirect(url_for('login'))
        text = request.form.get('comment','').strip()
        if text:
            comment = Comment(video_id=video.id, user_id=user.id, text=text)
            db.session.add(comment)
            db.session.commit()
            flash("Yorum eklendi.")
            return redirect(url_for('view_video', video_id=video.id))
    comments = Comment.query.filter_by(video_id=video.id).order_by(Comment.created_at.asc()).all()
    return render_template('view_video.html', video=video, user=user, comments=comments)

@app.route('/profile', methods=['GET','POST'])
def profile():
    user = current_user()
    if not user:
        flash("Profil görüntülemek için giriş yapın.")
        return redirect(url_for('login'))
    if request.method == 'POST':
        avatar = request.files.get('avatar')
        if avatar and avatar.filename:
            fn = secure_filename(f"{int(datetime.utcnow().timestamp())}_{avatar.filename}")
            path = os.path.join(app.config['AVATAR_FOLDER'], fn)
            avatar.save(path)
            user.avatar = fn
            db.session.commit()
            flash("Profil resmi güncellendi.")
            return redirect(url_for('profile'))
    user_videos = Video.query.filter_by(uploader_id=user.id).order_by(Video.created_at.desc()).all()
    return render_template('profile.html', user=user, user_videos=user_videos)

# --- Buy Subscription Route ---
@app.route('/buy_subscription')
def buy_subscription():
    user = current_user()
    message = "GELİŞME AŞAMASINDA"
    return render_template('buy_subscription.html', user=user, message=message)

# --- Statik dosya rotaları ---
@app.route('/static/videos/<path:filename>')
def serve_video(filename):
    return send_from_directory(app.config['VIDEO_FOLDER'], filename)

@app.route('/static/avatars/<path:filename>')
def serve_avatar(filename):
    return send_from_directory(app.config['AVATAR_FOLDER'], filename)

# --- RUN (Render uyumlu) ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))  # Render PORT al, yoksa 8080
    app.run(host="0.0.0.0", port=port, debug=True)
