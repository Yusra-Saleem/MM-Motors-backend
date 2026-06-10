from __future__ import annotations

import io
import json
import pillow_avif  # noqa: F401
from pathlib import Path
from urllib import error, parse, request
from PIL import Image

from fastapi import UploadFile

from app.core.config import settings
from app.core.errors import AppError


def _public_storage_url(object_name: str) -> str:
    if settings.supabase_storage_public_base_url:
        base = settings.supabase_storage_public_base_url.rstrip("/")
        return f"{base}/{object_name}"
    if not settings.supabase_url:
        raise AppError("Supabase storage is not configured", 503)
    return f"{settings.supabase_url.rstrip('/')}/storage/v1/object/public/{settings.supabase_storage_bucket}/{parse.quote(object_name)}"


def _process_image_to_avif(file: UploadFile) -> tuple[bytes, str]:
    """
    Converts an image to AVIF format and resizes it if it exceeds max dimensions.
    Returns (bytes, content_type).
    """
    try:
        img = Image.open(file.file)
        
        # Max dimensions for a car showroom image (HD)
        MAX_WIDTH = 1920
        MAX_HEIGHT = 1080
        
        # Maintain aspect ratio
        if img.width > MAX_WIDTH or img.height > MAX_HEIGHT:
            img.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.Resampling.LANCZOS)
            
        # Convert to RGB if necessary (AVIF doesn't support some modes like P)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")
            
        buffer = io.BytesIO()
        # Save as AVIF with high quality (speed=6 is a good balance for production)
        img.save(buffer, format="AVIF", quality=85, speed=6)
        return buffer.getvalue(), "image/avif"
    except Exception as e:
        # Fallback to original bytes if processing fails
        file.file.seek(0)
        return file.file.read(), file.content_type or "application/octet-stream"


def upload_file_to_supabase(file: UploadFile, object_name: str) -> str:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise AppError("Supabase storage is not configured", 503)

    # Automatically convert images to AVIF for optimization
    is_image = file.content_type and file.content_type.startswith("image/")
    if is_image:
        body, content_type = _process_image_to_avif(file)
        # Ensure extension is .avif
        path = Path(object_name)
        object_name = path.with_suffix(".avif").as_posix()
    else:
        body = file.file.read()
        content_type = file.content_type or "application/octet-stream"

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


def build_object_name(prefix: str, filename: str) -> str:
    safe_name = Path(filename).name
    return f"{prefix}/{safe_name}"
