from flask import Flask
from config import Config
from routes import main_bp
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['UPLOAD_FOLDER'] = 'uploads/'

    # 업로드 폴더가 존재하지 않으면 생성
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # 블루프린트 등록
    app.register_blueprint(main_bp)

    return app