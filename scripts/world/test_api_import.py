import axios
import base64
import json
import requests

# The user's image is available to me as a media file in the conversation context.
# I'll use the API directly to test.

IMG_PATH = r"C:\Users\Chris\antigravity\Godless\scripts\world\fire_emblem_judral.png"

# Note: I need to make sure the image exists at this path or similar.
# In this environment, I can use the 'generate_image' or 'search_web' but the user already
# attached the image. I will assume the image is downloaded or I can just mock the 
# base64 for a 1x1 pixel to test the endpoint connectivity.

def test_import():
    url = "http://localhost:8000/import_stencil"
    payload = {
        "image_base64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
        "width": 10,
        "height": 10
    }
    try:
        resp = requests.post(url, json=payload)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.json().get('status')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_import()
