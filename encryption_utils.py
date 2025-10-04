#!/usr/bin/env python3
"""
DreamSeed 데이터 암호화 유틸리티
"""
import os
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import sqlite3
import json

class DataEncryption:
    def __init__(self, master_password=None):
        """암호화 클래스 초기화"""
        self.master_password = master_password or os.getenv('DREAMSEED_MASTER_PASSWORD', 'default_master_password_2025')
        self.key = self._derive_key()
        self.cipher = Fernet(self.key)
    
    def _derive_key(self):
        """마스터 패스워드에서 암호화 키 생성"""
        password = self.master_password.encode()
        salt = b'dreamseed_salt_2025'  # 실제 운영에서는 랜덤 솔트 사용
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def encrypt_data(self, data):
        """데이터 암호화"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        elif isinstance(data, dict):
            data = json.dumps(data).encode('utf-8')
        return self.cipher.encrypt(data)
    
    def decrypt_data(self, encrypted_data):
        """데이터 복호화"""
        if isinstance(encrypted_data, str):
            encrypted_data = encrypted_data.encode('utf-8')
        decrypted = self.cipher.decrypt(encrypted_data)
        try:
            return json.loads(decrypted.decode('utf-8'))
        except:
            return decrypted.decode('utf-8')
    
    def encrypt_database_field(self, db_path, table_name, field_name, where_clause=None):
        """데이터베이스 필드 암호화"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 암호화할 데이터 조회
        query = f"SELECT rowid, {field_name} FROM {table_name}"
        if where_clause:
            query += f" WHERE {where_clause}"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # 암호화 및 업데이트
        for row_id, field_value in rows:
            if field_value:  # 빈 값이 아닌 경우만 암호화
                encrypted_value = self.encrypt_data(field_value)
                cursor.execute(
                    f"UPDATE {table_name} SET {field_name} = ? WHERE rowid = ?",
                    (encrypted_value, row_id)
                )
        
        conn.commit()
        conn.close()
        return len(rows)
    
    def decrypt_database_field(self, db_path, table_name, field_name, where_clause=None):
        """데이터베이스 필드 복호화"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 복호화할 데이터 조회
        query = f"SELECT rowid, {field_name} FROM {table_name}"
        if where_clause:
            query += f" WHERE {where_clause}"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # 복호화 및 업데이트
        for row_id, field_value in rows:
            if field_value:  # 빈 값이 아닌 경우만 복호화
                try:
                    decrypted_value = self.decrypt_data(field_value)
                    cursor.execute(
                        f"UPDATE {table_name} SET {field_name} = ? WHERE rowid = ?",
                        (decrypted_value, row_id)
                    )
                except Exception as e:
                    print(f"복호화 실패 (rowid: {row_id}): {e}")
        
        conn.commit()
        conn.close()
        return len(rows)

class BackupEncryption:
    def __init__(self, master_password=None):
        self.encryption = DataEncryption(master_password)
    
    def encrypt_backup_file(self, input_file, output_file):
        """백업 파일 암호화"""
        with open(input_file, 'rb') as f:
            data = f.read()
        
        encrypted_data = self.encryption.encrypt_data(data)
        
        with open(output_file, 'wb') as f:
            f.write(encrypted_data)
        
        return output_file
    
    def decrypt_backup_file(self, input_file, output_file):
        """백업 파일 복호화"""
        with open(input_file, 'rb') as f:
            encrypted_data = f.read()
        
        decrypted_data = self.encryption.decrypt_data(encrypted_data)
        
        with open(output_file, 'wb') as f:
            f.write(decrypted_data)
        
        return output_file

def hash_sensitive_data(data):
    """민감한 데이터 해시화 (복호화 불가능)"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()

def mask_sensitive_data(data, mask_char='*', visible_chars=4):
    """민감한 데이터 마스킹"""
    if not data or len(data) <= visible_chars:
        return data
    
    return data[:visible_chars] + mask_char * (len(data) - visible_chars)

# 사용 예시
if __name__ == "__main__":
    # 암호화 테스트
    encryption = DataEncryption("test_password")
    
    # 문자열 암호화/복호화
    original_text = "DreamSeed API Secret Data"
    encrypted = encryption.encrypt_data(original_text)
    decrypted = encryption.decrypt_data(encrypted)
    print(f"원본: {original_text}")
    print(f"암호화: {encrypted}")
    print(f"복호화: {decrypted}")
    
    # JSON 데이터 암호화/복호화
    original_json = {"user_id": 123, "api_key": "secret_key_12345"}
    encrypted_json = encryption.encrypt_data(original_json)
    decrypted_json = encryption.decrypt_data(encrypted_json)
    print(f"원본 JSON: {original_json}")
    print(f"복호화 JSON: {decrypted_json}")
    
    # 해시화 테스트
    sensitive_data = "user_password_12345"
    hashed = hash_sensitive_data(sensitive_data)
    print(f"원본: {sensitive_data}")
    print(f"해시: {hashed}")
    
    # 마스킹 테스트
    api_key = "ds_admin_2025_secure_key_12345"
    masked = mask_sensitive_data(api_key, visible_chars=8)
    print(f"원본: {api_key}")
    print(f"마스킹: {masked}")

