import requests
import json
import base64
from PIL import Image
import io
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get API key from environment
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")

def test_stability_api():
    """Test the Stability AI API with a simple text-to-image request"""
    
    if not STABILITY_API_KEY:
        print("ERROR: Missing Stability API key. Please add STABILITY_API_KEY to your .env file.")
        return False
    
    # List available engines first to confirm API connection
    engines_url = "https://api.stability.ai/v1/engines/list"
    
    headers = {
        "Authorization": f"Bearer {STABILITY_API_KEY}",
        "Accept": "application/json"
    }
    
    print("Step 1: Checking available engines...")
    
    try:
        engines_response = requests.get(engines_url, headers=headers)
        print(f"Engines response status: {engines_response.status_code}")
        
        if engines_response.status_code != 200:
            print(f"Error checking engines: {engines_response.text}")
            print("This likely indicates an authentication issue with your API key.")
            return False
            
        engines_data = engines_response.json()
        print(f"Available engines: {[engine['id'] for engine in engines_data]}")
        
        # Select an appropriate engine for text-to-image
        # Stable Diffusion XL is typically available as "stable-diffusion-xl-1024-v1-0"
        # or similar, but let's find it dynamically
        
        sd_engines = [engine for engine in engines_data if "stable-diffusion" in engine['id'].lower()]
        if not sd_engines:
            print("No Stable Diffusion engines found. Available engines:")
            for engine in engines_data:
                print(f"- {engine['id']}: {engine['description']}")
            return False
            
        # Prefer SDXL if available
        sdxl_engines = [engine for engine in sd_engines if "xl" in engine['id'].lower()]
        selected_engine = sdxl_engines[0]['id'] if sdxl_engines else sd_engines[0]['id']
        
        print(f"Selected engine: {selected_engine}")
        
        # Now try the text-to-image generation with the selected engine
        generation_url = f"https://api.stability.ai/v1/generation/{selected_engine}/text-to-image"
        
        headers = {
            "Authorization": f"Bearer {STABILITY_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Test prompt
        prompt = "Album cover art for electronic dance music, professional artwork, vibrant colors, abstract design, 8k"
        
        # Prepare the JSON payload according to Stability AI's documentation
        payload = {
            "text_prompts": [
                {
                    "text": prompt,
                    "weight": 1.0
                },
                {
                    "text": "blurry, bad quality, distorted, deformed",
                    "weight": -1.0
                }
            ],
            "cfg_scale": 7.0,
            "height": 1024,
            "width": 1024,
            "samples": 1,
            "steps": 30
        }
        
        print("\nStep 2: Generating image...")
        print(f"Prompt: {prompt}")
        print(f"Endpoint: {generation_url}")
        
        # Make the API request
        response = requests.post(generation_url, headers=headers, json=payload)
        
        # Print basic response info
        print(f"Status code: {response.status_code}")
        
        # Check response
        if response.status_code != 200:
            print(f"Error: API returned status code {response.status_code}")
            if response.headers.get('content-type') == 'application/json':
                try:
                    error_data = response.json()
                    print(f"Error details: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"Response: {response.text[:500]}")
            else:
                print(f"Response: {response.text[:500]}")
            return False
        
        # Process successful response
        try:
            data = response.json()
            print(f"Response data structure: {json.dumps(list(data.keys()), indent=2)}")
            
            # Extract image data
            if "artifacts" in data and len(data["artifacts"]) > 0:
                print(f"Successfully received {len(data['artifacts'])} image(s)")
                
                # Get the first image
                image_data = data["artifacts"][0]
                print(f"Image data keys: {list(image_data.keys())}")
                
                # Get base64 image data and decode
                image_base64 = image_data["base64"]
                image_bytes = base64.b64decode(image_base64)
                
                # Save the image
                with open("stability_test_output.png", "wb") as f:
                    f.write(image_bytes)
                
                print("Image saved as stability_test_output.png")
                
                # Open the image to verify
                try:
                    image = Image.open(io.BytesIO(image_bytes))
                    print(f"Image size: {image.size}")
                    print(f"Image mode: {image.mode}")
                    return True
                except Exception as img_err:
                    print(f"Error opening saved image: {img_err}")
            else:
                print(f"No image artifacts found in response. Available keys: {data.keys()}")
                return False
                
        except json.JSONDecodeError:
            print("Could not parse JSON response:")
            print(response.text[:500])  # Print first 500 chars to avoid overwhelming console
            return False
            
    except Exception as e:
        print(f"Error sending request: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("STABILITY AI API TEST")
    print("=" * 50)
    
    success = test_stability_api()
    
    if success:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed!")