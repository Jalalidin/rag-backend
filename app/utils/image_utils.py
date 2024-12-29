import base64
from fastapi import UploadFile

async def image_to_base64(image: UploadFile) -> str:
    """Converts an uploaded image to a base64 string."""
    image_bytes = await image.read()
    return base64.b64encode(image_bytes).decode("utf-8") 