
import os
import uuid
from io import BytesIO
from pathlib import Path

from flask import current_app
from PIL import Image, UnidentifiedImageError
from supabase import create_client


MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB per image

ALLOWED_FORMATS = {
    "JPEG": ("jpg", "image/jpeg"),
    "PNG": ("png", "image/png"),
    "WEBP": ("webp", "image/webp"),
}


def get_supabase_client():
    """Create and cache the Supabase client for this Flask application."""

    client = current_app.extensions.get("supabase_storage_client")

    if client is None:
        supabase_url = current_app.config.get("SUPABASE_URL") or os.getenv(
            "SUPABASE_URL"
        )
        supabase_key = current_app.config.get("SUPABASE_SECRET_KEY") or os.getenv(
            "SUPABASE_SECRET_KEY"
        )

        if not supabase_url or not supabase_key:
            raise RuntimeError(
                "SUPABASE_URL or SUPABASE_SECRET_KEY is not configured."
            )

        client = create_client(supabase_url, supabase_key)
        current_app.extensions["supabase_storage_client"] = client

    return client


def get_storage_bucket():
    return (
        current_app.config.get("SUPABASE_INSPECTION_BUCKET")
        or os.getenv("SUPABASE_INSPECTION_BUCKET")
        or "inspections"
    )


def validate_inspection_image(file_storage):
    """
    Validate an uploaded image using its actual image content.
    Returns: (image_bytes, extension, content_type)
    """

    if not file_storage or not file_storage.filename:
        raise ValueError("Please select an image.")

    image_bytes = file_storage.read()

    if not image_bytes:
        raise ValueError("The selected image is empty.")

    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise ValueError("Each inspection image must not exceed 5 MB.")

    try:
        with Image.open(BytesIO(image_bytes)) as image:
            image_format = image.format
            image.verify()

    except (UnidentifiedImageError, OSError, ValueError):
        raise ValueError(
            f"{file_storage.filename} is not a valid image."
        )

    if image_format not in ALLOWED_FORMATS:
        raise ValueError(
            "Only JPG, JPEG, PNG and WEBP images are allowed."
        )

    extension, content_type = ALLOWED_FORMATS[image_format]

    return image_bytes, extension, content_type


def upload_inspection_image(
    image_bytes,
    company_id,
    inspection_id,
    extension,
    content_type,
):
    """Upload an image to the private Supabase inspection bucket."""

    client = get_supabase_client()
    bucket = get_storage_bucket()

    filename = f"{uuid.uuid4().hex}.{extension}"

    object_path = (
        f"company_{company_id}/"
        f"inspection_{inspection_id}/"
        f"{filename}"
    )

    client.storage.from_(bucket).upload(
        path=object_path,
        file=image_bytes,
        file_options={
            "content-type": content_type,
            "cache-control": "3600",
            "upsert": "false",
        },
    )

    return object_path


def save_local_inspection_copy(
    image_bytes,
    company_id,
    inspection_id,
    filename,
):
    """
    Save a development copy under static/uploads/inspections.
    Render's local filesystem is not used for permanent image storage.
    """

    if os.getenv("RENDER", "").lower() == "true":
        return None

    relative_path = (
        Path("uploads")
        / "inspections"
        / f"company_{company_id}"
        / f"inspection_{inspection_id}"
        / filename
    )

    absolute_path = Path(current_app.static_folder) / relative_path
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    absolute_path.write_bytes(image_bytes)

    return relative_path.as_posix()


def create_inspection_image_signed_url(object_path, expires_in=3600):
    """Generate a temporary URL for an image in the private bucket."""

    client = get_supabase_client()
    bucket = get_storage_bucket()

    response = client.storage.from_(bucket).create_signed_url(
        object_path,
        expires_in,
    )

    if isinstance(response, dict):
        signed_url = (
            response.get("signedURL")
            or response.get("signedUrl")
            or response.get("signed_url")
        )
    else:
        signed_url = None

    if not signed_url:
        raise RuntimeError("Supabase did not return a signed image URL.")

    return signed_url


def delete_supabase_inspection_images(object_paths):
    """Delete one or more image objects from Supabase."""

    paths = [path for path in object_paths if path]

    if not paths:
        return

    client = get_supabase_client()
    client.storage.from_(get_storage_bucket()).remove(paths)


def delete_local_inspection_copy(local_path):
    """Delete a local development copy, if one exists."""

    if not local_path:
        return

    absolute_path = Path(current_app.static_folder) / local_path
    absolute_path.unlink(missing_ok=True)
