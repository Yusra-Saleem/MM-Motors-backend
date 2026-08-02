import sys
import io
from pathlib import Path
from urllib import request
from uuid import uuid4
from PIL import Image, ImageOps

# Ensure parent directory is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal
from app.models.car import Car
from app.services.storage import (
    upload_raw_bytes_to_supabase,
    build_object_name,
)

# Safety Flag: Set DRY_RUN = True to test without writing any changes to DB or Supabase.
DRY_RUN = "--dry-run" in sys.argv

def optimize_url(url: str, car_id: str, is_thumb: bool = False) -> str | None:
    """Downloads an existing image URL, converts to WebP, and uploads to Supabase with 1-year cache headers."""
    if not url:
        return None
        
    try:
        if DRY_RUN:
            print(f"  [DRY RUN] Would download & compress {url[:60]}...")
            return url.replace(".png", ".webp").replace(".jpg", ".webp")

        req = request.Request(url, headers={"User-Agent": "MMMotors-Migrator/1.0"})
        with request.urlopen(req, timeout=15) as resp:
            data = resp.read()

        img_file = io.BytesIO(data)
        img = Image.open(img_file)
        img = ImageOps.exif_transpose(img)

        max_w = 600 if is_thumb else 1440
        max_h = 450 if is_thumb else 1080
        quality = 75 if is_thumb else 82

        if img.width > max_w or img.height > max_h:
            img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)

        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")

        buffer = io.BytesIO()
        img.save(buffer, format="WEBP", quality=quality, method=4)
        webp_bytes = buffer.getvalue()

        prefix = "thumb-" if is_thumb else ""
        obj_name = build_object_name(
            f"cars/{car_id}",
            f"{prefix}{uuid4().hex[:8]}.webp"
        )

        return upload_raw_bytes_to_supabase(webp_bytes, "image/webp", obj_name)
    except Exception as e:
        print(f"  [Safety Fallback] Could not process {url[:50]}: {e}. Preserving original URL safely.")
        return url  # Safely keep original URL if any error occurs!

def main():
    if DRY_RUN:
        print("=== RUNNING IN SAFE DRY-RUN MODE (NO CHANGES WILL BE SAVED) ===")
    else:
        print("=== RUNNING IN PRODUCTION MIGRATION MODE ===")

    db = SessionLocal()
    try:
        cars = db.query(Car).filter(Car.deleted_at.is_(None)).all()
        print(f"Found {len(cars)} active car records to inspect/optimize.\n")

        updated_count = 0
        for index, car in enumerate(cars, start=1):
            print(f"[{index}/{len(cars)}] Checking Car ID: {car.id} - {car.name}")
            needs_update = False

            # 1. Optimize images if uncompressed/old format
            new_images = []
            for img_url in (car.images or []):
                if not img_url:
                    continue
                # If already optimized WebP with 1-year cache, keep as is safely
                if ".webp" in img_url and "thumb-" not in img_url and "cars/" in img_url:
                    new_images.append(img_url)
                else:
                    opt_url = optimize_url(img_url, car.id, is_thumb=False)
                    new_images.append(opt_url or img_url)
                    if opt_url and opt_url != img_url:
                        needs_update = True

            # 2. Check/Generate thumbnail
            if not car.thumbnail or ".webp" not in car.thumbnail or "thumb-" not in car.thumbnail:
                primary_url = car.thumbnail or (car.images[0] if car.images else None)
                if primary_url:
                    thumb_url = optimize_url(primary_url, car.id, is_thumb=True)
                    if thumb_url and thumb_url != car.thumbnail:
                        car.thumbnail = thumb_url
                        needs_update = True

            if needs_update:
                if not DRY_RUN:
                    car.images = new_images
                    db.commit()
                updated_count += 1
                print(f"  -> Safely optimized Car {car.id}")

        if DRY_RUN:
            print(f"\n[DRY RUN COMPLETE] {updated_count} cars would be optimized safely.")
        else:
            print(f"\n[COMPLETE] Successfully optimized {updated_count} cars in database safely!")
    except Exception as err:
        print(f"Migration error: {err}. Rolling back transaction safely.")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
