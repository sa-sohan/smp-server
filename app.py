from flask import Flask, jsonify, request, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

app = Flask(__name__)
app.secret_key = 'Kx9#mP2$vN5@jL8q'  # 실제 배포 시 변경해야 합니다

# 데이터베이스 설정
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///temp.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 관리자 계정 설정
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Kx9#mP2$vN5@jL8q"  # 실제 사용할 비밀번호로 변경하세요

# 로그인 매니저 설정
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# IP 주소를 저장할 모델
class AllowedIP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(50), unique=True, nullable=False)
    added_date = db.Column(db.DateTime, default=datetime.utcnow)

# 프로그램 버전 정보를 저장할 모델
class ProgramVersion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String(20), nullable=False)
    download_url = db.Column(db.String(200), nullable=False)
    release_date = db.Column(db.DateTime, default=datetime.utcnow)

# 사용자 클래스
class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    if user_id == ADMIN_USERNAME:
        return User(user_id)
    return None

# 로그인 페이지
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            user = User(username)
            login_user(user)
            return redirect(url_for('admin_panel'))
        flash('잘못된 로그인 정보입니다.')
    return render_template('login.html')

# 로그아웃
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# 관리자 패널
@app.route('/admin')
@login_required
def admin_panel():
    ips = AllowedIP.query.all()
    versions = ProgramVersion.query.order_by(ProgramVersion.release_date.desc()).all()
    return render_template('admin.html', ips=ips, versions=versions)

# IP 체크 엔드포인트
@app.route('/check-ip', methods=['POST'])
def check_ip():
    client_ip = request.json.get('ip')
    if not client_ip:
        return jsonify({'allowed': False, 'message': 'No IP provided'}), 400
    
    ip = AllowedIP.query.filter_by(ip_address=client_ip).first()
    return jsonify({'allowed': bool(ip)})

# 버전 체크 엔드포인트
@app.route('/check-version', methods=['GET'])
def check_version():
    latest_version = ProgramVersion.query.order_by(ProgramVersion.release_date.desc()).first()
    if latest_version:
        return jsonify({
            'version': latest_version.version,
            'download_url': latest_version.download_url
        })
    return jsonify({'version': None, 'download_url': None})

# IP 추가 (웹 인터페이스)
@app.route('/admin/ip/add', methods=['POST'])
@login_required
def add_ip_web():
    ip = request.form.get('ip')
    if ip:
        try:
            new_ip = AllowedIP(ip_address=ip)
            db.session.add(new_ip)
            db.session.commit()
            flash('IP가 추가되었습니다.')
        except Exception as e:
            flash(f'IP 추가 중 오류가 발생했습니다: {str(e)}')
    return redirect(url_for('admin_panel'))

# IP 삭제 (웹 인터페이스)
@app.route('/admin/ip/delete/<int:id>', methods=['POST'])
@login_required
def delete_ip(id):
    ip = AllowedIP.query.get_or_404(id)
    try:
        db.session.delete(ip)
        db.session.commit()
        flash('IP가 삭제되었습니다.')
    except Exception as e:
        flash(f'IP 삭제 중 오류가 발생했습니다: {str(e)}')
    return redirect(url_for('admin_panel'))

# 버전 업데이트 추가 (웹 인터페이스)
@app.route('/admin/version/add', methods=['POST'])
@login_required
def add_version_web():
    version = request.form.get('version')
    download_url = request.form.get('download_url')
    if version and download_url:
        try:
            new_version = ProgramVersion(version=version, download_url=download_url)
            db.session.add(new_version)
            db.session.commit()
            flash('새 버전이 추가되었습니다.')
        except Exception as e:
            flash(f'버전 추가 중 오류가 발생했습니다: {str(e)}')
    return redirect(url_for('admin_panel'))

# 버전 삭제 (웹 인터페이스)
@app.route('/admin/version/delete/<int:id>', methods=['POST'])
@login_required
def delete_version(id):
    version = ProgramVersion.query.get_or_404(id)
    try:
        db.session.delete(version)
        db.session.commit()
        flash('버전이 삭제되었습니다.')
    except Exception as e:
        flash(f'버전 삭제 중 오류가 발생했습니다: {str(e)}')
    return redirect(url_for('admin_panel'))

# 메인 페이지
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('admin_panel'))
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)