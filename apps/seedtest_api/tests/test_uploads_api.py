import os
import io
from fastapi.testclient import TestClient

# Ensure LOCAL_DEV to bypass auth for tests
os.environ.setdefault("LOCAL_DEV", "true")

from apps.seedtest_api.app.main import app
from apps.seedtest_api.settings import settings


def test_upload_image_png_allowed_and_org_scoped(tmp_path):
    client = TestClient(app)

    # Patch upload dir to temp
    old_dir = settings.UPLOAD_DIR
    try:
        settings.UPLOAD_DIR = str(tmp_path)
        data = {
            'file': (
                'test.png',
                io.BytesIO(b'\x89PNG\r\n\x1a\nFAKE'),
                'image/png',
            )
        }
        r = client.post("/api/seedtest/uploads/images", files=data)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body['content_type'] == 'image/png'
        # URL should include org-id default from LOCAL_DEV (org_id=1)
        assert '/uploads/1/' in body['url'] or body['url'].endswith('/uploads/1/' + body['filename'])
    finally:
        settings.UPLOAD_DIR = old_dir


def test_upload_image_reject_unsupported_mime(tmp_path):
    client = TestClient(app)
    old_dir = settings.UPLOAD_DIR
    try:
        settings.UPLOAD_DIR = str(tmp_path)
        data = {
            'file': (
                'doc.pdf',
                io.BytesIO(b'%PDF-1.4 fake'),
                'application/pdf',
            )
        }
        r = client.post("/api/seedtest/uploads/images", files=data)
        assert r.status_code == 400
        assert r.json().get('detail') == 'unsupported_media_type'
    finally:
        settings.UPLOAD_DIR = old_dir


def test_upload_image_enforces_size_limit(tmp_path):
    client = TestClient(app)
    old_dir = settings.UPLOAD_DIR
    old_max = settings.UPLOAD_MAX_MB
    try:
        settings.UPLOAD_DIR = str(tmp_path)
        settings.UPLOAD_MAX_MB = 0  # 0 bytes allowed -> any payload too large
        data = {
            'file': (
                'small.png',
                io.BytesIO(b'12345'),
                'image/png',
            )
        }
        r = client.post("/api/seedtest/uploads/images", files=data)
        assert r.status_code == 413
        assert r.json().get('detail') == 'file_too_large'
    finally:
        settings.UPLOAD_DIR = old_dir
        settings.UPLOAD_MAX_MB = old_max
