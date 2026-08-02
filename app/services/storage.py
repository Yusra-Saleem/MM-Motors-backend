from __future__ import annotations

import io
from pathlib import Path
from urllib import error, parse, request
from PIL import Image, ImageOps

from fastapi import UploadFile

from app.core.config import settings
from app.core.errors import AppError

# Optional AVIF plugin fallback if required elsewhere
try:
    import pillow_avif  # noqa: F401
except Exception:
    pass


def _public_storage_url(object_name: str) -> str:
    if settings.supabase_storage_public_base_url:
        base = settings.supabase_storage_public_base_url.rstrip("/")
        return f"{base}/{object_name}"
    if not settings.supabase_url:
        raise AppError("Supabase storage is not configured", 503)
    return f"{settings.supabase_url.rstrip('/')}/storage/v1/object/public/{settings.supabase_storage_bucket}/{parse.quote(object_name)}"


def _process_image_to_webp(
    file: UploadFile,
    max_width: int = 1440,
    max_height: int = 1080,
    quality: int = 82,
) -> tuple[bytes, str]:
    """
    Converts an image to optimized WebP format with EXIF orientation correction.
    Returns (bytes, content_type).
    """
    try:
        file.file.seek(0)
        img = Image.open(file.file)

        # Auto-rotate according to EXIF data if present
        img = ImageOps.exif_transpose(img)

        # Maintain aspect ratio
        if img.width > max_width or img.height > max_height:
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

        # Convert to RGB / RGBA mode
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")

        buffer = io.BytesIO()
        img.save(buffer, format="WEBP", quality=quality, method=4)
        return buffer.getvalue(), "image/webp"
    except Exception as exc:
        raise AppError(f"Image processing failed: {exc}", 422) from exc


def upload_raw_bytes_to_supabase(body: bytes, content_type: str, object_name: str) -> str:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise AppError("Supabase storage is not configured", 503)

    object_name = object_name.replace("\\", "/")

    upload_url = (
        f"{settings.supabase_url.rstrip('/')}/storage/v1/object/"
        f"{settings.supabase_storage_bucket}/{parse.quote(object_name)}?upsert=true"
    )
    headers = {
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "apikey": settings.supabase_service_role_key,
        "Content-Type": content_type,
        "x-upsert": "true",
        "Cache-Control": "public, max-age=31536000, immutable",
    }

    req = request.Request(upload_url, data=body, headers=headers, method="POST")

    try:
        with request.urlopen(req, timeout=30) as response:  # noqa: S310 - controlled Supabase API request
            response.read()
    except error.HTTPError as exc:  # pragma: no cover - network dependent
        detail = exc.read().decode("utf-8", errors="ignore")
        raise AppError(f"Supabase upload failed: {detail or exc.reason}", 502) from exc
    except OSError as exc:  # pragma: no cover - network dependent
        raise AppError("Supabase upload failed", 502) from exc

    return _public_storage_url(object_name)


def upload_file_to_supabase(file: UploadFile, object_name: str) -> str:
    is_image = file.content_type and file.content_type.startswith("image/")
    if is_image:
        body, content_type = _process_image_to_webp(file, max_width=1440, max_height=1080, quality=82)
        object_name = Path(object_name).with_suffix(".webp").as_posix()
    else:
        file.file.seek(0)
        body = file.file.read()
        content_type = file.content_type or "application/octet-stream"

    return upload_raw_bytes_to_supabase(body, content_type, object_name)


def upload_thumbnail_to_supabase(file: UploadFile, object_name: str) -> str:
    """
    Generates a lightweight (max width 600px) WebP thumbnail for card/table view.
    """
    body, content_type = _process_image_to_webp(file, max_width=600, max_height=450, quality=75)
    thumb_object_name = Path(object_name).with_suffix(".webp").as_posix()
    return upload_raw_bytes_to_supabase(body, content_type, thumb_object_name)


def build_object_name(prefix: str, filename: str) -> str:
    safe_name = Path(filename).name
    return f"{prefix}/{safe_name}"

