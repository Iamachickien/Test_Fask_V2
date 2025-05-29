from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
import pytz
import os

# Cấu hình múi giờ Việt Nam
vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key')
database_url = os.getenv('DATABASE_URL', 'postgresql://user:password@db:5432/esp32_db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql+psycopg2://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Định nghĩa model cho lịch sử
class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(10), nullable=False)

# Định nghĩa model cho người dùng
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(20), default='user')

# Tạo database và tài khoản admin mặc định
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        hashed_password = bcrypt.generate_password_hash('12345678').decode('utf-8')
        admin = User(username='admin', password=hashed_password, role='admin')
        db.session.add(admin)
        db.session.commit()

led_status = "OFF"
esp_status = "Hello"

@app.route('/')
def index():
    if 'username' in session:
        return render_template("index.html", status=esp_status, User=User)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session['username'] = username
            return redirect(url_for('index'))
        return render_template("login.html", error="Tên đăng nhập hoặc mật khẩu không đúng")
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/set-command/<cmd>')
def set_command(cmd):
    global led_status
    if cmd.upper() in ["ON", "OFF"]:
        led_status = cmd.upper()
        return f"Command set to {led_status}"
    return "Invalid command", 400

@app.route('/get-command')
def get_command():
    return led_status

@app.route('/report-status', methods=['POST'])
def report_status():
    global esp_status
    data = request.get_json()
    status = data.get("status")
    if status not in ["ON", "OFF"]:
        return "Invalid status", 400
    if status != esp_status:
        timestamp = datetime.now(vietnam_tz).strftime("%Y-%m-%d %H:%M:%S")
        esp_status = status
        new_entry = History(timestamp=timestamp, status=status)
        db.session.add(new_entry)
        db.session.commit()
        if History.query.count() > 100:
            oldest = History.query.order_by(History.timestamp.asc()).first()
            db.session.delete(oldest)
            db.session.commit()
        print(f"[{timestamp}] ESP32 reported: {status}")
    return "Status handled", 200

@app.route('/get-real-status')
def get_real_status():
    return esp_status

@app.route('/history')
def view_history():
    logs = History.query.order_by(History.timestamp.desc()).limit(100).all()
    return render_template("history.html", logs=logs)

@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if new_password != confirm_password:
            flash('Mật khẩu mới và xác nhận mật khẩu không khớp', 'error')
            return redirect(url_for('change_password'))
        
        user = User.query.filter_by(username=session['username']).first()
        if user and bcrypt.check_password_hash(user.password, old_password):
            user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            db.session.commit()
            flash('Đổi mật khẩu thành công', 'success')
            return redirect(url_for('index'))
        else:
            flash('Mật khẩu cũ không đúng', 'error')
            return redirect(url_for('change_password'))
    
    return render_template("change_password.html")

@app.route('/manage-users', methods=['GET', 'POST'])
def manage_users():
    if 'username' not in session or User.query.filter_by(username=session['username']).first().role != 'admin':
        flash('Chỉ admin mới có quyền truy cập', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            username = request.form['username']
            password = request.form['password']
            if User.query.filter_by(username=username).first():
                flash('Tên đăng nhập đã tồn tại', 'error')
            else:
                hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
                new_user = User(username=username, password=hashed_password, role='user')
                db.session.add(new_user)
                db.session.commit()
                flash('Thêm tài khoản thành công', 'success')
        elif action == 'delete':
            user_id = request.form['user_id']
            user = User.query.get(user_id)
            if user and user.role != 'admin':
                db.session.delete(user)
                db.session.commit()
                flash('Xóa tài khoản thành công', 'success')
            else:
                flash('Không thể xóa tài khoản admin', 'error')
        elif action == 'update':
            user_id = request.form['user_id']
            new_password = request.form['new_password']
            user = User.query.get(user_id)
            if user:
                user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
                db.session.commit()
                flash('Cập nhật mật khẩu thành công', 'success')
            else:
                flash('Tài khoản không tồn tại', 'error')
    
    users = User.query.all()
    return render_template("manage_users.html", users=users)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)