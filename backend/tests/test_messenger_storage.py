"""
Tests for File Upload & Storage System (Task 2.3)

Tests file upload, validation, thumbnail generation, and virus scanning.
"""

import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from app.messenger.storage import (
    FileSizeError,
    FileStorage,
    FileType,
    FileTypeError,
    StorageBackend,
    VirusScanError,
    compute_file_hash,
    detect_file_type,
    generate_thumbnail,
    validate_file,
)


@pytest.fixture
def temp_storage_dir(tmp_path):
    """Create temporary storage directory"""
    storage_dir = tmp_path / "uploads"
    storage_dir.mkdir()
    return storage_dir


@pytest.fixture
def file_storage(temp_storage_dir):
    """Create FileStorage instance with local backend"""
    return FileStorage(
        backend=StorageBackend.LOCAL,
        local_path=str(temp_storage_dir),
    )


@pytest.fixture
def sample_image():
    """Create sample image bytes"""
    img = Image.new("RGB", (800, 600), color="red")
    output = io.BytesIO()
    img.save(output, format="JPEG")
    output.seek(0)
    return output.read()


@pytest.fixture
def sample_file():
    """Create sample text file"""
    return b"This is a test file content"


def test_detect_file_type_image():
    """Test file type detection for images"""
    assert detect_file_type("photo.jpg") == FileType.IMAGE
    assert detect_file_type("image.png") == FileType.IMAGE
    assert detect_file_type("animation.gif") == FileType.IMAGE
    assert detect_file_type("modern.webp") == FileType.IMAGE


def test_detect_file_type_video():
    """Test file type detection for videos"""
    assert detect_file_type("video.mp4") == FileType.VIDEO
    assert detect_file_type("movie.mov") == FileType.VIDEO
    assert detect_file_type("clip.webm") == FileType.VIDEO


def test_detect_file_type_audio():
    """Test file type detection for audio"""
    assert detect_file_type("song.mp3") == FileType.AUDIO
    assert detect_file_type("sound.wav") == FileType.AUDIO
    assert detect_file_type("track.ogg") == FileType.AUDIO


def test_detect_file_type_document():
    """Test file type detection for documents"""
    assert detect_file_type("doc.pdf") == FileType.DOCUMENT
    assert detect_file_type("sheet.xlsx") == FileType.DOCUMENT
    assert detect_file_type("presentation.pptx") == FileType.DOCUMENT


def test_detect_file_type_unknown():
    """Test file type detection for unknown types"""
    assert detect_file_type("script.exe") == FileType.OTHER
    assert detect_file_type("data.bin") == FileType.OTHER


def test_validate_file_success():
    """Test successful file validation"""
    file_type = validate_file(
        file_size=1024 * 1024,  # 1 MB
        filename="photo.jpg",
    )
    assert file_type == FileType.IMAGE


def test_validate_file_image_too_large():
    """Test file size validation for images"""
    with pytest.raises(FileSizeError):
        validate_file(
            file_size=15 * 1024 * 1024,  # 15 MB (exceeds 10 MB limit)
            filename="huge_photo.jpg",
        )


def test_validate_file_invalid_extension():
    """Test file extension validation"""
    with pytest.raises(FileTypeError):
        validate_file(
            file_size=1024,
            filename="malware.exe",
        )


def test_compute_file_hash():
    """Test SHA-256 hash computation"""
    data = b"test content"
    hash1 = compute_file_hash(data)
    hash2 = compute_file_hash(data)

    # Same content should produce same hash
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 is 64 hex chars


def test_compute_file_hash_different():
    """Test hash differs for different content"""
    hash1 = compute_file_hash(b"content1")
    hash2 = compute_file_hash(b"content2")

    assert hash1 != hash2


def test_generate_thumbnail(sample_image):
    """Test thumbnail generation from image"""
    thumbnail_data = generate_thumbnail(sample_image, size=(100, 100))

    # Verify it's valid JPEG
    img = Image.open(io.BytesIO(thumbnail_data))
    assert img.format == "JPEG"

    # Verify size (should be ≤100x100)
    assert img.width <= 100
    assert img.height <= 100


def test_generate_thumbnail_rgba():
    """Test thumbnail generation from RGBA image"""
    # Create RGBA image with transparency
    img = Image.new("RGBA", (800, 600), color=(255, 0, 0, 128))
    output = io.BytesIO()
    img.save(output, format="PNG")
    output.seek(0)

    thumbnail_data = generate_thumbnail(output.read())

    # Should be converted to RGB JPEG
    thumb_img = Image.open(io.BytesIO(thumbnail_data))
    assert thumb_img.format == "JPEG"
    assert thumb_img.mode == "RGB"


@pytest.mark.asyncio
async def test_upload_file_local(file_storage, sample_image):
    """Test file upload to local storage"""
    file_obj = io.BytesIO(sample_image)

    with patch("app.messenger.storage.scan_file_for_virus", return_value=True):
        result = await file_storage.upload_file(
            file=file_obj,
            filename="test_photo.jpg",
            user_id=1,
            scan_virus=True,
            generate_thumb=True,
        )

    # Verify metadata
    assert result["file_name"] == "test_photo.jpg"
    assert result["file_type"] == "image"
    assert result["file_size"] > 0
    assert result["file_url"].endswith(".jpg")
    assert result["thumbnail_url"] is not None
    assert result["uploaded_by"] == 1

    # Verify file exists
    file_path = Path(
        result["file_url"].replace("/uploads/", str(file_storage.local_path) + "/")
    )
    assert file_path.exists()


@pytest.mark.asyncio
async def test_upload_file_without_thumbnail(file_storage, sample_file):
    """Test file upload without thumbnail generation"""
    file_obj = io.BytesIO(sample_file)

    with patch("app.messenger.storage.scan_file_for_virus", return_value=True):
        result = await file_storage.upload_file(
            file=file_obj,
            filename="document.pdf",
            user_id=1,
            scan_virus=True,
            generate_thumb=False,
        )

    assert result["thumbnail_url"] is None


@pytest.mark.asyncio
async def test_upload_file_virus_detected(file_storage, sample_file):
    """Test file upload with virus detection"""
    file_obj = io.BytesIO(sample_file)

    with patch(
        "app.messenger.storage.scan_file_for_virus",
        side_effect=VirusScanError("Virus detected"),
    ):
        with pytest.raises(VirusScanError):
            await file_storage.upload_file(
                file=file_obj,
                filename="malware.exe",
                user_id=1,
                scan_virus=True,
            )


@pytest.mark.asyncio
async def test_upload_file_too_large(file_storage):
    """Test file upload with size limit exceeded"""
    # Create large file (150 MB)
    large_file = io.BytesIO(b"x" * (150 * 1024 * 1024))

    with pytest.raises(FileSizeError):
        await file_storage.upload_file(
            file=large_file,
            filename="huge_video.mp4",
            user_id=1,
            scan_virus=False,
        )


@pytest.mark.asyncio
async def test_upload_file_invalid_type(file_storage):
    """Test file upload with invalid file type"""
    file_obj = io.BytesIO(b"malicious content")

    with pytest.raises(FileTypeError):
        await file_storage.upload_file(
            file=file_obj,
            filename="virus.exe",
            user_id=1,
            scan_virus=False,
        )


@pytest.mark.asyncio
async def test_delete_file_local(file_storage, sample_image):
    """Test file deletion from local storage"""
    file_obj = io.BytesIO(sample_image)

    with patch("app.messenger.storage.scan_file_for_virus", return_value=True):
        result = await file_storage.upload_file(
            file=file_obj,
            filename="temp.jpg",
            user_id=1,
            scan_virus=True,
        )

    # Delete file
    deleted = await file_storage.delete_file(result["file_url"])
    assert deleted is True

    # Verify file removed
    file_path = Path(
        result["file_url"].replace("/uploads/", str(file_storage.local_path) + "/")
    )
    assert not file_path.exists()


@pytest.mark.asyncio
async def test_delete_file_not_found(file_storage):
    """Test deletion of non-existent file"""
    result = await file_storage.delete_file("/uploads/nonexistent.jpg")
    assert result is True  # Should not raise error


def test_scan_file_for_virus_clamav_not_installed(tmp_path):
    """Test virus scan when ClamAV not installed"""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    with patch("subprocess.run") as mock_run:
        # Mock 'which clamdscan' returning not found
        mock_run.return_value = MagicMock(returncode=1)

        # Should skip scan and return True
        from app.messenger.storage import scan_file_for_virus

        result = scan_file_for_virus(test_file)
        assert result is True


def test_scan_file_for_virus_clean(tmp_path):
    """Test virus scan with clean file"""
    test_file = tmp_path / "clean.txt"
    test_file.write_text("clean content")

    with patch("subprocess.run") as mock_run:
        # Mock 'which clamdscan' success
        mock_run.side_effect = [
            MagicMock(returncode=0),  # which command
            MagicMock(returncode=0, stdout="", stderr=""),  # clamdscan
        ]

        from app.messenger.storage import scan_file_for_virus

        result = scan_file_for_virus(test_file)
        assert result is True


def test_scan_file_for_virus_infected(tmp_path):
    """Test virus scan with infected file"""
    test_file = tmp_path / "virus.txt"
    test_file.write_text("VIRUS!")

    with patch("subprocess.run") as mock_run:
        # Mock virus detection
        mock_run.side_effect = [
            MagicMock(returncode=0),  # which command
            MagicMock(returncode=1, stdout="FOUND", stderr=""),  # clamdscan virus found
        ]

        from app.messenger.storage import scan_file_for_virus

        with pytest.raises(VirusScanError):
            scan_file_for_virus(test_file)


@pytest.mark.asyncio
async def test_file_storage_s3_init():
    """Test S3 storage initialization"""
    with patch("app.messenger.storage.boto3"):
        storage = FileStorage(
            backend=StorageBackend.S3,
            s3_bucket="test-bucket",
            s3_region="us-west-2",
        )

        assert storage.backend == StorageBackend.S3
        assert storage.s3_bucket == "test-bucket"


def test_file_storage_s3_missing_bucket():
    """Test S3 storage initialization without bucket"""
    with pytest.raises(ValueError):
        FileStorage(backend=StorageBackend.S3)


def test_file_storage_get_s3_url():
    """Test S3 URL generation"""
    with patch("app.messenger.storage.boto3"):
        storage = FileStorage(
            backend=StorageBackend.S3,
            s3_bucket="test-bucket",
            s3_region="ap-northeast-2",
        )

        url = storage._get_s3_url("files/test.jpg")
        assert "test-bucket" in url
        assert "files/test.jpg" in url


def test_file_storage_get_s3_url_with_cdn():
    """Test S3 URL generation with CDN"""
    with patch("app.messenger.storage.boto3"):
        storage = FileStorage(
            backend=StorageBackend.S3,
            s3_bucket="test-bucket",
            s3_region="ap-northeast-2",
            cdn_base_url="https://cdn.example.com",
        )

        url = storage._get_s3_url("files/test.jpg")
        assert url == "https://cdn.example.com/files/test.jpg"


def test_get_file_storage_singleton():
    """Test FileStorage singleton pattern"""
    from app.messenger.storage import get_file_storage

    # Clear singleton
    import app.messenger.storage

    app.messenger.storage._file_storage_instance = None

    storage1 = get_file_storage()
    storage2 = get_file_storage()

    assert storage1 is storage2
