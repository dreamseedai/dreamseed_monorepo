"""
File Upload & Storage System for Messenger

Handles file uploads, storage (local/S3), virus scanning, and thumbnail generation.
Supports images, videos, documents, and audio files.

Storage Backends:
- Local: Development/testing (files stored in /uploads)
- S3: Production (AWS S3 or compatible)

Features:
- File validation (size, type, extension)
- Virus scanning (ClamAV integration)
- Image thumbnail generation (PIL)
- Video thumbnail extraction (ffmpeg)
- CDN URL generation
- File cleanup (orphaned files)
"""

from __future__ import annotations

import hashlib
import io
import logging
import mimetypes
import os
import subprocess
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import BinaryIO, Optional
from uuid import uuid4

from PIL import Image

logger = logging.getLogger(__name__)


class FileType(str, Enum):
    """Supported file types"""

    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    OTHER = "other"


class StorageBackend(str, Enum):
    """Storage backend options"""

    LOCAL = "local"
    S3 = "s3"


# File size limits (bytes)
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_AUDIO_SIZE = 20 * 1024 * 1024  # 20 MB
MAX_DOCUMENT_SIZE = 50 * 1024 * 1024  # 50 MB

# Allowed file extensions
ALLOWED_IMAGES = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic"}
ALLOWED_VIDEOS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
ALLOWED_AUDIO = {".mp3", ".wav", ".ogg", ".m4a", ".aac"}
ALLOWED_DOCUMENTS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt"}

# Thumbnail settings
THUMBNAIL_SIZE = (300, 300)
THUMBNAIL_QUALITY = 85


class FileUploadError(Exception):
    """Base exception for file upload errors"""

    pass


class FileSizeError(FileUploadError):
    """File size exceeds limit"""

    pass


class FileTypeError(FileUploadError):
    """File type not allowed"""

    pass


class VirusScanError(FileUploadError):
    """Virus detected in file"""

    pass


def detect_file_type(filename: str, content_type: Optional[str] = None) -> FileType:
    """
    Detect file type from filename and content type.

    Args:
        filename: Original filename
        content_type: MIME type (optional)

    Returns:
        FileType enum value
    """
    ext = Path(filename).suffix.lower()

    if ext in ALLOWED_IMAGES:
        return FileType.IMAGE
    elif ext in ALLOWED_VIDEOS:
        return FileType.VIDEO
    elif ext in ALLOWED_AUDIO:
        return FileType.AUDIO
    elif ext in ALLOWED_DOCUMENTS:
        return FileType.DOCUMENT

    # Fallback to content type
    if content_type:
        if content_type.startswith("image/"):
            return FileType.IMAGE
        elif content_type.startswith("video/"):
            return FileType.VIDEO
        elif content_type.startswith("audio/"):
            return FileType.AUDIO
        elif content_type in ["application/pdf", "application/msword"]:
            return FileType.DOCUMENT

    return FileType.OTHER


def validate_file(
    file_size: int,
    filename: str,
    content_type: Optional[str] = None,
) -> FileType:
    """
    Validate file size, type, and extension.

    Args:
        file_size: File size in bytes
        filename: Original filename
        content_type: MIME type (optional)

    Returns:
        FileType enum value

    Raises:
        FileSizeError: If file too large
        FileTypeError: If file type not allowed
    """
    # Detect file type
    file_type = detect_file_type(filename, content_type)
    ext = Path(filename).suffix.lower()

    # Check extension whitelist
    all_allowed = ALLOWED_IMAGES | ALLOWED_VIDEOS | ALLOWED_AUDIO | ALLOWED_DOCUMENTS
    if ext not in all_allowed:
        raise FileTypeError(f"File extension not allowed: {ext}")

    # Check file size limits
    if file_type == FileType.IMAGE and file_size > MAX_IMAGE_SIZE:
        raise FileSizeError(
            f"Image too large: {file_size} bytes (max {MAX_IMAGE_SIZE})"
        )
    elif file_type == FileType.VIDEO and file_size > MAX_VIDEO_SIZE:
        raise FileSizeError(
            f"Video too large: {file_size} bytes (max {MAX_VIDEO_SIZE})"
        )
    elif file_type == FileType.AUDIO and file_size > MAX_AUDIO_SIZE:
        raise FileSizeError(
            f"Audio too large: {file_size} bytes (max {MAX_AUDIO_SIZE})"
        )
    elif file_type == FileType.DOCUMENT and file_size > MAX_DOCUMENT_SIZE:
        raise FileSizeError(
            f"Document too large: {file_size} bytes (max {MAX_DOCUMENT_SIZE})"
        )
    elif file_size > MAX_FILE_SIZE:
        raise FileSizeError(f"File too large: {file_size} bytes (max {MAX_FILE_SIZE})")

    return file_type


def scan_file_for_virus(file_path: Path) -> bool:
    """
    Scan file for viruses using ClamAV.

    Args:
        file_path: Path to file to scan

    Returns:
        True if clean, False if virus detected

    Raises:
        VirusScanError: If scan fails or virus detected
    """
    try:
        # Check if clamdscan is available
        result = subprocess.run(
            ["which", "clamdscan"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            # ClamAV not installed - skip scan in development
            logger.warning("ClamAV not installed - skipping virus scan")
            return True

        # Run virus scan
        result = subprocess.run(
            ["clamdscan", "--no-summary", str(file_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            # File is clean
            return True
        elif result.returncode == 1:
            # Virus detected
            logger.error(f"Virus detected in {file_path}: {result.stdout}")
            raise VirusScanError("Virus detected in uploaded file")
        else:
            # Scan error
            logger.error(f"ClamAV scan error: {result.stderr}")
            raise VirusScanError("Virus scan failed")

    except subprocess.TimeoutExpired:
        logger.error("ClamAV scan timeout")
        raise VirusScanError("Virus scan timeout")
    except Exception as e:
        logger.error(f"ClamAV scan error: {e}")
        # In production, fail closed (reject file)
        # In development, fail open (allow file)
        if os.getenv("ENVIRONMENT") == "production":
            raise VirusScanError(f"Virus scan failed: {e}")
        return True


def generate_thumbnail(
    image_data: bytes,
    size: tuple[int, int] = THUMBNAIL_SIZE,
    quality: int = THUMBNAIL_QUALITY,
) -> bytes:
    """
    Generate thumbnail from image data.

    Args:
        image_data: Original image bytes
        size: Thumbnail dimensions (width, height)
        quality: JPEG quality (1-100)

    Returns:
        Thumbnail image bytes (JPEG)

    Raises:
        Exception: If thumbnail generation fails
    """
    try:
        # Open image
        image = Image.open(io.BytesIO(image_data))

        # Convert RGBA to RGB (for JPEG)
        if image.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(
                image, mask=image.split()[-1] if image.mode == "RGBA" else None
            )
            image = background

        # Generate thumbnail
        image.thumbnail(size, Image.Resampling.LANCZOS)

        # Save to bytes
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=quality, optimize=True)
        output.seek(0)

        return output.read()

    except Exception as e:
        logger.error(f"Thumbnail generation failed: {e}")
        raise


def generate_video_thumbnail(
    video_path: Path,
    output_path: Path,
    timestamp: str = "00:00:01",
) -> bool:
    """
    Extract video thumbnail using ffmpeg.

    Args:
        video_path: Path to video file
        output_path: Path to save thumbnail
        timestamp: Time position for thumbnail (HH:MM:SS)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if ffmpeg is available
        result = subprocess.run(
            ["which", "ffmpeg"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            logger.warning("ffmpeg not installed - skipping video thumbnail")
            return False

        # Extract frame at timestamp
        result = subprocess.run(
            [
                "ffmpeg",
                "-ss",
                timestamp,
                "-i",
                str(video_path),
                "-vframes",
                "1",
                "-vf",
                f"scale={THUMBNAIL_SIZE[0]}:{THUMBNAIL_SIZE[1]}:force_original_aspect_ratio=decrease",
                "-y",
                str(output_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            return True
        else:
            logger.error(f"ffmpeg error: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        logger.error("ffmpeg timeout")
        return False
    except Exception as e:
        logger.error(f"Video thumbnail error: {e}")
        return False


def compute_file_hash(file_data: bytes) -> str:
    """
    Compute SHA-256 hash of file content.

    Args:
        file_data: File bytes

    Returns:
        Hex-encoded SHA-256 hash
    """
    return hashlib.sha256(file_data).hexdigest()


class FileStorage:
    """
    File storage manager - handles local and S3 storage.

    Supports:
    - File upload with validation
    - Thumbnail generation
    - Virus scanning
    - CDN URL generation
    - File cleanup
    """

    def __init__(
        self,
        backend: StorageBackend = StorageBackend.LOCAL,
        local_path: str = "./uploads",
        s3_bucket: Optional[str] = None,
        s3_region: Optional[str] = None,
        cdn_base_url: Optional[str] = None,
    ):
        """
        Initialize storage backend.

        Args:
            backend: Storage backend (local or s3)
            local_path: Local storage directory
            s3_bucket: S3 bucket name (required if backend=s3)
            s3_region: S3 region (required if backend=s3)
            cdn_base_url: CDN base URL (optional)
        """
        self.backend = backend
        self.local_path = Path(local_path)
        self.s3_bucket = s3_bucket
        self.s3_region = s3_region
        self.cdn_base_url = cdn_base_url

        # Initialize local storage
        if backend == StorageBackend.LOCAL:
            self.local_path.mkdir(parents=True, exist_ok=True)
            (self.local_path / "thumbnails").mkdir(exist_ok=True)

        # Initialize S3 client
        if backend == StorageBackend.S3:
            if not s3_bucket:
                raise ValueError("s3_bucket required for S3 backend")

            try:
                import boto3

                self.s3_client = boto3.client("s3", region_name=s3_region)
            except ImportError:
                raise ImportError("boto3 required for S3 backend: pip install boto3")

    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        user_id: int,
        conversation_id: Optional[str] = None,
        scan_virus: bool = True,
        generate_thumb: bool = True,
    ) -> dict:
        """
        Upload file with validation, virus scan, and thumbnail generation.

        Args:
            file: File-like object (opened file or UploadFile.file)
            filename: Original filename
            user_id: Uploader user ID
            conversation_id: Optional conversation ID
            scan_virus: Whether to scan for viruses
            generate_thumb: Whether to generate thumbnail

        Returns:
            dict with file metadata:
            {
                "file_id": "uuid",
                "file_name": "original.jpg",
                "file_size": 12345,
                "file_type": "image",
                "file_url": "https://cdn.../uuid.jpg",
                "thumbnail_url": "https://cdn.../uuid_thumb.jpg",
                "content_type": "image/jpeg",
                "file_hash": "sha256...",
                "uploaded_by": 1,
                "uploaded_at": "2024-11-26T10:30:00Z",
            }

        Raises:
            FileSizeError: File too large
            FileTypeError: File type not allowed
            VirusScanError: Virus detected
        """
        # Read file data
        file_data = file.read()
        file_size = len(file_data)

        # Validate file
        content_type = mimetypes.guess_type(filename)[0]
        file_type = validate_file(file_size, filename, content_type)

        # Generate unique file ID
        file_id = str(uuid4())
        ext = Path(filename).suffix.lower()
        stored_filename = f"{file_id}{ext}"

        # Compute file hash (for deduplication)
        file_hash = compute_file_hash(file_data)

        # Save to temporary location for virus scan
        if self.backend == StorageBackend.LOCAL:
            temp_path = self.local_path / stored_filename
            temp_path.write_bytes(file_data)
        else:
            # For S3, write to temp file
            import tempfile

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
            temp_path = Path(temp_file.name)
            temp_path.write_bytes(file_data)

        try:
            # Virus scan
            if scan_virus:
                scan_file_for_virus(temp_path)

            # Generate thumbnail
            thumbnail_url = None
            if generate_thumb:
                if file_type == FileType.IMAGE:
                    thumbnail_data = generate_thumbnail(file_data)
                    thumbnail_filename = f"{file_id}_thumb.jpg"

                    if self.backend == StorageBackend.LOCAL:
                        thumb_path = self.local_path / "thumbnails" / thumbnail_filename
                        thumb_path.write_bytes(thumbnail_data)
                        thumbnail_url = f"/uploads/thumbnails/{thumbnail_filename}"
                    else:
                        # Upload thumbnail to S3
                        thumb_key = f"thumbnails/{thumbnail_filename}"
                        self.s3_client.put_object(
                            Bucket=self.s3_bucket,
                            Key=thumb_key,
                            Body=thumbnail_data,
                            ContentType="image/jpeg",
                        )
                        thumbnail_url = self._get_s3_url(thumb_key)

                elif file_type == FileType.VIDEO:
                    # Video thumbnail
                    thumbnail_filename = f"{file_id}_thumb.jpg"
                    thumb_path = self.local_path / "thumbnails" / thumbnail_filename

                    if generate_video_thumbnail(temp_path, thumb_path):
                        if self.backend == StorageBackend.S3:
                            thumb_key = f"thumbnails/{thumbnail_filename}"
                            self.s3_client.upload_file(
                                str(thumb_path),
                                self.s3_bucket,
                                thumb_key,
                                ExtraArgs={"ContentType": "image/jpeg"},
                            )
                            thumbnail_url = self._get_s3_url(thumb_key)
                            thumb_path.unlink()  # Cleanup local temp
                        else:
                            thumbnail_url = f"/uploads/thumbnails/{thumbnail_filename}"

            # Upload to final destination
            if self.backend == StorageBackend.S3:
                # Upload to S3
                file_key = f"messenger/{user_id}/{stored_filename}"
                self.s3_client.put_object(
                    Bucket=self.s3_bucket,
                    Key=file_key,
                    Body=file_data,
                    ContentType=content_type or "application/octet-stream",
                    Metadata={
                        "user_id": str(user_id),
                        "conversation_id": conversation_id or "",
                        "original_filename": filename,
                    },
                )

                file_url = self._get_s3_url(file_key)

                # Cleanup temp file
                temp_path.unlink()
            else:
                # Local storage - already saved
                file_url = f"/uploads/{stored_filename}"

            # Return metadata
            return {
                "file_id": file_id,
                "file_name": filename,
                "file_size": file_size,
                "file_type": file_type.value,
                "file_url": file_url,
                "thumbnail_url": thumbnail_url,
                "content_type": content_type,
                "file_hash": file_hash,
                "uploaded_by": user_id,
                "uploaded_at": datetime.utcnow().isoformat(),
            }

        except Exception:
            # Cleanup on error
            if temp_path.exists():
                temp_path.unlink()
            raise

    def _get_s3_url(self, key: str) -> str:
        """
        Generate S3 URL (CDN or direct).

        Args:
            key: S3 object key

        Returns:
            Full URL to file
        """
        if self.cdn_base_url:
            return f"{self.cdn_base_url}/{key}"
        else:
            return f"https://{self.s3_bucket}.s3.{self.s3_region}.amazonaws.com/{key}"

    async def delete_file(self, file_url: str) -> bool:
        """
        Delete file from storage.

        Args:
            file_url: File URL to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.backend == StorageBackend.LOCAL:
                # Extract filename from URL
                filename = Path(file_url).name
                file_path = self.local_path / filename
                if file_path.exists():
                    file_path.unlink()
                return True
            else:
                # Delete from S3
                # Extract key from URL
                key = file_url.split(f"{self.s3_bucket}/")[-1]
                self.s3_client.delete_object(Bucket=self.s3_bucket, Key=key)
                return True

        except Exception:
            return False


# Singleton instance
_file_storage_instance: Optional[FileStorage] = None


def get_file_storage() -> FileStorage:
    """
    Get or create singleton FileStorage instance.

    Configuration from environment variables:
    - STORAGE_BACKEND: "local" or "s3" (default: local)
    - STORAGE_LOCAL_PATH: Local storage directory (default: ./uploads)
    - STORAGE_S3_BUCKET: S3 bucket name
    - STORAGE_S3_REGION: S3 region (default: ap-northeast-2)
    - STORAGE_CDN_URL: CDN base URL (optional)

    Returns:
        FileStorage singleton instance
    """
    global _file_storage_instance

    if _file_storage_instance is None:
        backend_str = os.getenv("STORAGE_BACKEND", "local")
        backend = StorageBackend(backend_str)

        _file_storage_instance = FileStorage(
            backend=backend,
            local_path=os.getenv("STORAGE_LOCAL_PATH", "./uploads"),
            s3_bucket=os.getenv("STORAGE_S3_BUCKET"),
            s3_region=os.getenv("STORAGE_S3_REGION", "ap-northeast-2"),
            cdn_base_url=os.getenv("STORAGE_CDN_URL"),
        )

    return _file_storage_instance
