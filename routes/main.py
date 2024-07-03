from flask import request, jsonify, render_template, send_from_directory, request,  current_app, redirect, url_for
from . import main_bp
from services.backtest_service import perform_backtest
from services.backtests.Static_Asset_Allocation import Static_Asset_Allocation
import os
from werkzeug.utils import secure_filename
from services.day_run import *
import json

# 허용된 파일 확장자를 정의하는 함수
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'csv', 'pdf'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main_bp.route('/')
def home():
    return render_template('index.html')

@main_bp.route('/backtests')
def homes():
    return render_template('backtest.html')

@main_bp.route('/showReport')
def showRepot():
    return send_from_directory('static', 'report.html')

@main_bp.route('/up')
def up():
    return render_template('upload.html')

@main_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    if file and allowed_file(file.filename):
        ext = os.path.splitext(file.filename)[1]  # 파일 확장자 추출
        fixed_filename = f"backtest.csv"  # 고정된 파일 이름 설정
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], fixed_filename))
        return '', 204  # 성공 시 아무 내용 없이 응답
    return 'File type not allowed', 400

@main_bp.route('/backtest', methods=['POST'])
def backtest():
    data = request.get_json()
    symbol = data.get('symbol')
    
    symbol = symbol.split(', ')
    symbol = [f'{item}' for item in symbol]

    start_date = data.get('startDate')
    end_date = data.get('endDate')

    # 백테스트 로직 호출
    result = perform_backtest(symbol, start_date, end_date)
    results = Static_Asset_Allocation(symbol, start_date, end_date)

    return jsonify(results)

@main_bp.route('/day_backtest', methods=['POST'])
def day_backtest():
    run_portfolio_analysis()
    json_file_path = os.path.join(current_app.root_path, 'Record/stock_rate.json')

    # stock_rate.json 파일을 열고 JSON 데이터를 로드합니다.
    with open(json_file_path, 'r') as file:
        stock_data = json.load(file)

    # JSON 데이터를 클라이언트에 반환합니다.
    return jsonify(stock_data), 200


@main_bp.route('/download_report')
def download_report():
    return send_from_directory('static', 'report.html', as_attachment=True)

# @main_bp.route('/plot')
# def plot():
#     # 그래프 생성
#     plt.figure()
#     plt.plot([1, 2, 3, 4, 5], [1, 4, 2, 3, 5])
#     plt.title('Sample Plot')
#     plt.xlabel('X-axis')
#     plt.ylabel('Y-axis')

#     # 그래프를 이미지 파일로 저장
#     buf = io.BytesIO()
#     plt.savefig(buf, format='png')
#     buf.seek(0)
#     return send_file(buf, mimetype='image/png')

@main_bp.route('/show_plot')
def show_plot():
    return render_template('backtest_report.html')