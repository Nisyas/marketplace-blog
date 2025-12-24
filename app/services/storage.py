from uuid import uuid4
from typing import BinaryIO

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import get_settings


settings = get_settings()

ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024

_s3_client = boto3.client(
    "s3",
    endpoint_url=settings.s3_endpoint_url,
    aws_access_key_id=settings.s3_access_key,
    aws_secret_access_key=settings.s3_secret_key,
    region_name=settings.s3_region,
)


def get_s3_client():
    return _s3_client


def generate_object_name(filename: str) -> str:
    ext = ""
    if "." in filename:
        ext = "." + filename.rsplit(".", 1)[-1]
    return f"articles/{uuid4().hex}{ext}"


def validate_image_file(
    file_obj: BinaryIO,
    filename: str,
    content_type: str | None,
) -> None:
    if not content_type or content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise ValueError(
            f"Unsupported image content type: {content_type!r}. "
            "Allowed: " + ", ".join(sorted(ALLOWED_IMAGE_CONTENT_TYPES))
        )

    file_obj.seek(0, 2)
    size = file_obj.tell()
    file_obj.seek(0)

    if size > MAX_IMAGE_SIZE_BYTES:
        raise ValueError(
            f"File is too large: {size} bytes. "
            f"Max allowed: {MAX_IMAGE_SIZE_BYTES} bytes."
        )


def upload_image_file(file_obj, filename: str, content_type: str | None = None) -> str:
    validate_image_file(file_obj, filename, content_type)
    s3 = get_s3_client()
    object_name = generate_object_name(filename)

    extra_args: dict[str, str] = {}
    if content_type:
        extra_args["ContentType"] = content_type

    try:
        s3.upload_fileobj(
            Fileobj=file_obj,
            Bucket=settings.s3_bucket_name,
            Key=object_name,
            ExtraArgs=extra_args or None,
        )
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(f"S3 upload failed: {exc}") from exc

    base = settings.s3_endpoint_url.rstrip("/")
    return f"{base}/{settings.s3_bucket_name}/{object_name}"
