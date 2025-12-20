from uuid import uuid4

import boto3

from app.core.config import get_settings


settings = get_settings()


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
    )


def generate_object_name(filename: str) -> str:
    ext = ""
    if "." in filename:
        ext = "." + filename.rsplit(".", 1)[-1]
    return f"articles/{uuid4().hex}{ext}"


def upload_image_file(file_obj, filename: str, content_type: str | None = None) -> str:
    s3 = get_s3_client()
    object_name = generate_object_name(filename)

    extra_args: dict[str, str] = {}
    if content_type:
        extra_args["ContentType"] = content_type

    s3.upload_fileobj(
        Fileobj=file_obj,
        Bucket=settings.s3_bucket_name,
        Key=object_name,
        ExtraArgs=extra_args or None,
    )

    if settings.s3_endpoint_url.endswith("/"):
        base = settings.s3_endpoint_url.rstrip("/")
    else:
        base = settings.s3_endpoint_url

    return f"{base}/{settings.s3_bucket_name}/{object_name}"
