from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# 데이터베이스 설정
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///temp.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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

# 관리자용 IP 추가 엔드포인트
@app.route('/admin/add-ip', methods=['POST'])
def add_ip():
    auth_token = request.headers.get('Authorization')
    if auth_token != 'your_secret_admin_token':  # 실제 운영에서는 더 안전한 인증 방식 사용
        return jsonify({'error': 'Unauthorized'}), 401

    ip_address = request.json.get('ip')
    if not ip_address:
        return jsonify({'error': 'No IP provided'}), 400

    try:
        new_ip = AllowedIP(ip_address=ip_address)
        db.session.add(new_ip)
        db.session.commit()
        return jsonify({'message': f'IP {ip_address} added successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 관리자용 버전 업데이트 엔드포인트
@app.route('/admin/update-version', methods=['POST'])
def update_version():
    auth_token = request.headers.get('Authorization')
    if auth_token != 'your_secret_admin_token':  # 실제 운영에서는 더 안전한 인증 방식 사용
        return jsonify({'error': 'Unauthorized'}), 401

    version = request.json.get('version')
    download_url = request.json.get('download_url')
    
    if not version or not download_url:
        return jsonify({'error': 'Version and download_url are required'}), 400

    try:
        new_version = ProgramVersion(version=version, download_url=download_url)
        db.session.add(new_version)
        db.session.commit()
        return jsonify({'message': f'Version {version} added successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 메인 페이지
@app.route('/')
def index():
    return 'SMP Server is running!'

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)