# standalone_test.py - Simple script to test the Stable Diffusion API directly

import requests
import json
from PIL import Image
import io
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
API_KEY = os.getenv("STABLE_DIFFUSION_API_KEY")

# Make sure you have an API key
if not API_KEY:
    print("ERROR: Missing API key. Please add STABLE_DIFFUSION_API_KEY to your .env file.")
    exit(1)

def test_stable_diffusion_api():
    # API endpoint for Stable Diffusion API v4 dreambooth
    url = "https://stablediffusionapi.com/api/v4/dreambooth"
    
    # Exactly the same payload as in your example
    payload = {
        "key": API_KEY,
        "model_id": "sdxlceshi",
        "prompt": "ultra realistic close up portrait ((beautiful pale cyberpunk female with heavy black eyeliner)), blue eyes, shaved side haircut, hyper detail, cinematic lighting, magic neon, dark red city, Canon EOS R3, nikon, f/1.4, ISO 200, 1/160s, 8K, RAW, unedited, symmetrical balance, in-frame, 8K",
        "negative_prompt": "painting, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, deformed, ugly, blurry, bad anatomy, bad proportions, extra limbs, cloned face, skinny, glitchy, double torso, extra arms, extra hands, mangled fingers, missing lips, ugly face, distorted face, extra legs, anime",
        "width": "512",
        "height": "512",
        "samples": "1",
        "num_inference_steps": "30",
        "seed": None,
        "guidance_scale": 7.5,
        "webhook": None,
        "track_id": None
    }
    
    print("Sending request to Stable Diffusion API...")
    
    try:
        # Make the API request
        response = requests.post(url, json=payload)
        
        # Print basic info about the response
        print(f"Status code: {response.status_code}")
        
        # Try to parse JSON response
        try:
            data = response.json()
            print(f"Response data: {json.dumps(data, indent=2)}")
            
            # Check for success
            if data.get('status') == 'success':
                # Get image URL
                image_url = data.get('output', [])[0]
                print(f"Image URL: {image_url}")
                
                # Download and save the image
                img_response = requests.get(image_url)
                if img_response.status_code == 200:
                    image = Image.open(io.BytesIO(img_response.content))
                    image.save("test_output.png")
                    print("Image saved as test_output.png")
                    return True
                else:
                    print(f"Error downloading image: {img_response.status_code}")
            
            # Check for processing status
            elif data.get('status') == 'processing':
                fetch_id = data.get('id')
                print(f"Image is processing. Fetch ID: {fetch_id}")
                
                if fetch_id:
                    # Wait a bit
                    print("Waiting 10 seconds before checking status...")
                    time.sleep(10)
                    
                    # Check status
                    fetch_url = f"https://stablediffusionapi.com/api/v3/fetch/{fetch_id}"
                    fetch_payload = {"key": API_KEY}
                    
                    fetch_response = requests.post(fetch_url, json=fetch_payload)
                    fetch_data = fetch_response.json()
                    
                    print(f"Fetch response: {json.dumps(fetch_data, indent=2)}")
                    
                    if fetch_data.get('status') == 'success':
                        image_url = fetch_data.get('output', [])[0]
                        img_response = requests.get(image_url)
                        
                        if img_response.status_code == 200:
                            image = Image.open(io.BytesIO(img_response.content))
                            image.save("test_output.png")
                            print("Image saved as test_output.png")
                            return True
            
            # If neither success nor processing
            else:
                print(f"API returned error: {data.get('message', 'Unknown error')}")
            
        except json.JSONDecodeError:
            print("Failed to parse JSON response:")
            print(response.text)
    
    except Exception as e:
        print(f"Error sending request: {str(e)}")
    
    return False

if __name__ == "__main__":
    print("Testing Stable Diffusion API connection...")
    test_stable_diffusion_api()