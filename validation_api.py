#!/usr/bin/env python3
"""
MathML 변환 품질 검증 API
DreamSeed AI 프로젝트용 검증 시스템
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# SQLite 데이터베이스 초기화
def init_database():
    """검증 데이터베이스 초기화"""
    conn = sqlite3.connect('validation_results.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS validation_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            validation_result TEXT NOT NULL,
            notes TEXT,
            validator_name TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            original_mathml TEXT,
            converted_content TEXT,
            conversion_type TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversion_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            original_mathml TEXT NOT NULL,
            converted_content TEXT NOT NULL,
            conversion_type TEXT NOT NULL,
            success BOOLEAN NOT NULL,
            error_message TEXT,
            processing_time REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def load_conversion_data(file_path: str) -> List[Dict]:
    """변환 결과 파일 로드"""
    conversion_data = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    conversion_data.append(json.loads(line))
    except FileNotFoundError:
        print(f"변환 파일을 찾을 수 없습니다: {file_path}")
    except Exception as e:
        print(f"파일 로드 오류: {e}")
    
    return conversion_data

@app.route('/api/conversion-data')
def get_conversion_data():
    """변환 데이터 조회"""
    file_path = request.args.get('file', 'mathml_conversion_results.jsonl')
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    
    conversion_data = load_conversion_data(file_path)
    
    # 페이지네이션
    start = offset
    end = offset + limit
    paginated_data = conversion_data[start:end]
    
    return jsonify({
        'data': paginated_data,
        'total': len(conversion_data),
        'offset': offset,
        'limit': limit
    })

@app.route('/api/questions/<int:question_id>')
def get_question(question_id: int):
    """특정 문제 조회"""
    # 실제 구현에서는 PostgreSQL에서 조회
    # 여기서는 변환 데이터에서 찾기
    
    file_path = request.args.get('file', 'mathml_conversion_results.jsonl')
    conversion_data = load_conversion_data(file_path)
    
    question_data = None
    for item in conversion_data:
        if item['question_id'] == question_id:
            question_data = item
            break
    
    if not question_data:
        return jsonify({'error': '문제를 찾을 수 없습니다'}), 404
    
    return jsonify({
        'id': question_id,
        'original_mathml': question_data['original_mathml'],
        'converted_content': question_data['converted_content'],
        'conversion_type': question_data['conversion_type'],
        'success': question_data['success'],
        'error_message': question_data.get('error_message'),
        'processing_time': question_data.get('processing_time', 0)
    })

@app.route('/api/validation', methods=['POST'])
def save_validation():
    """검증 결과 저장"""
    data = request.json
    
    conn = sqlite3.connect('validation_results.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO validation_results 
        (question_id, validation_result, notes, validator_name, original_mathml, converted_content, conversion_type)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['question_id'],
        data['result'],
        data.get('notes', ''),
        data.get('validator_name', 'unknown'),
        data.get('original_mathml', ''),
        data.get('converted_content', ''),
        data.get('conversion_type', '')
    ))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '검증 결과가 저장되었습니다'})

@app.route('/api/validation/stats')
def get_validation_stats():
    """검증 통계 조회"""
    conn = sqlite3.connect('validation_results.db')
    cursor = conn.cursor()
    
    # 전체 통계
    cursor.execute('SELECT COUNT(*) FROM validation_results')
    total_validations = cursor.fetchone()[0]
    
    # 결과별 통계
    cursor.execute('SELECT validation_result, COUNT(*) FROM validation_results GROUP BY validation_result')
    result_stats = dict(cursor.fetchall())
    
    # 변환 타입별 통계
    cursor.execute('SELECT conversion_type, COUNT(*) FROM validation_results GROUP BY conversion_type')
    type_stats = dict(cursor.fetchall())
    
    # 최근 검증
    cursor.execute('''
        SELECT question_id, validation_result, timestamp 
        FROM validation_results 
        ORDER BY timestamp DESC 
        LIMIT 10
    ''')
    recent_validations = cursor.fetchall()
    
    conn.close()
    
    return jsonify({
        'total_validations': total_validations,
        'result_stats': result_stats,
        'type_stats': type_stats,
        'recent_validations': recent_validations
    })

@app.route('/api/validation/export')
def export_validation_results():
    """검증 결과 내보내기"""
    conn = sqlite3.connect('validation_results.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT question_id, validation_result, notes, validator_name, timestamp,
               original_mathml, converted_content, conversion_type
        FROM validation_results
        ORDER BY timestamp DESC
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    # CSV 형식으로 내보내기
    csv_data = "question_id,validation_result,notes,validator_name,timestamp,original_mathml,converted_content,conversion_type\n"
    
    for result in results:
        csv_data += f"{result[0]},{result[1]},\"{result[2]}\",{result[3]},{result[4]},\"{result[5]}\",\"{result[6]}\",{result[7]}\n"
    
    return csv_data, 200, {'Content-Type': 'text/csv'}

@app.route('/api/validation/report')
def generate_validation_report():
    """검증 보고서 생성"""
    conn = sqlite3.connect('validation_results.db')
    cursor = conn.cursor()
    
    # 전체 통계
    cursor.execute('SELECT COUNT(*) FROM validation_results')
    total = cursor.fetchone()[0]
    
    # 정확한 변환 수
    cursor.execute('SELECT COUNT(*) FROM validation_results WHERE validation_result = "correct"')
    correct = cursor.fetchone()[0]
    
    # 오류가 있는 변환 수
    cursor.execute('SELECT COUNT(*) FROM validation_results WHERE validation_result = "error"')
    errors = cursor.fetchone()[0]
    
    # 정확도 계산
    accuracy = (correct / total * 100) if total > 0 else 0
    
    # 변환 타입별 정확도
    cursor.execute('''
        SELECT conversion_type, 
               COUNT(*) as total,
               SUM(CASE WHEN validation_result = "correct" THEN 1 ELSE 0 END) as correct
        FROM validation_results 
        GROUP BY conversion_type
    ''')
    type_accuracy = cursor.fetchall()
    
    conn.close()
    
    report = {
        'summary': {
            'total_validations': total,
            'correct_validations': correct,
            'error_validations': errors,
            'accuracy_percentage': round(accuracy, 2)
        },
        'type_breakdown': [
            {
                'type': row[0],
                'total': row[1],
                'correct': row[2],
                'accuracy': round((row[2] / row[1] * 100) if row[1] > 0 else 0, 2)
            }
            for row in type_accuracy
        ],
        'generated_at': datetime.now().isoformat()
    }
    
    return jsonify(report)

@app.route('/')
def serve_comparison_tool():
    """비교 도구 서빙"""
    return send_from_directory('.', 'visual_comparison_tool.html')

if __name__ == '__main__':
    init_database()
    app.run(debug=True, host='0.0.0.0', port=5000)
