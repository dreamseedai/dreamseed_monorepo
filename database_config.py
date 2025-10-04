#!/usr/bin/env python3
"""
데이터베이스 연결 설정
"""

import os

# 데이터베이스 연결 정보 설정
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '5432'
os.environ['DB_NAME'] = 'dreamseed'
os.environ['DB_USER'] = 'postgres'
os.environ['DB_PASSWORD'] = 'password'

print("데이터베이스 연결 정보 설정 완료")
print(f"Host: {os.environ['DB_HOST']}")
print(f"Port: {os.environ['DB_PORT']}")
print(f"Database: {os.environ['DB_NAME']}")
print(f"User: {os.environ['DB_USER']}")
