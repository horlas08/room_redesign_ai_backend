import base64
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


def generate_redesign_image(prompt: str, image_path: str | None = None) -> dict:
    """Generate an image using OpenAI Images API.
    If image_path is provided, perform an edit using the input image.
    Returns dict with keys: image_url or image_bytes (base64 string)
    """
    if image_path:
        with open(image_path, 'rb') as f:
            resp = client.images.edits(
                model="gpt-image-1",
                image=f,
                prompt=prompt,
                size="1024x1024",
            )
    else:
        resp = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024"
        )
    if not resp.data:
        raise RuntimeError('No image generated')
    image_b64 = resp.data[0].b64_json
    return {"image_bytes": image_b64}
