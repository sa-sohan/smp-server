from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# 데이터베이스 설정 (나중에 Heroku에서 실제 DB URL로 변경할 예정)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///temp.db'
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)