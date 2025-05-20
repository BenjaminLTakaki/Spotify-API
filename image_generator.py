import requests
import json
import os
import base64
from PIL import Image
import io
import time
import random
from config import STABILITY_API_KEY, DEFAULT_NEGATIVE_PROMPT, COVERS_DIR

def create_prompt_from_data(playlist_data, user_mood=None):
    """Create optimized prompt for stable diffusion"""
    genres_str = ", ".join(playlist_data.get("genres", ["various"]))
    energy = playlist_data.get("energy_level", "balanced")
    mood = user_mood if user_mood else playlist_data.get("mood_descriptor", "balanced")
    
    style_elements = playlist_data.get("style_elements", [])
    
    prompt = (
        f"album cover art, {genres_str} music, professional artwork, "
        f"highly detailed, 8k"
    )
    
    if user_mood:
        prompt += f", {user_mood} atmosphere"
    
    if style_elements:
        prompt += ", " + ", ".join(style_elements)
    
    return prompt

def send_generation_request(url, params):
    """Send request to Stability API using multipart/form-data"""
    if not STABILITY_API_KEY:
        print("ERROR: Missing Stability API key. Please set STABILITY_API_KEY in your .env file.")
        return None
        
    headers = {
        "Authorization": f"Bearer {STABILITY_API_KEY}",
        "Accept": "application/json"
    }
    
    # Convert params to multipart/form-data format
    files = {}
    for key, value in params.items():
        if isinstance(value, (int, float)):
            value = str(value)
        files[key] = (None, value)
    
    response = requests.post(url, files=files, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: API returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return None
    
    return response.json()

def generate_cover_image(prompt, lora=None, output_path=None, negative_prompt=DEFAULT_NEGATIVE_PROMPT):
    """Generate album cover image using Stability AI SD 3.5 Large API"""
    # Check if we have API key
    if not STABILITY_API_KEY:
        print("ERROR: Missing Stability API key. Please set STABILITY_API_KEY in your .env file.")
        return False
    
    print(f"Generating with prompt: {prompt}")
    
    # Check if we have a LoRA model
    if lora:
        lora_prompt = ""
        if isinstance(lora, dict):
            lora_name = lora.get("name", "")
            lora_type = lora.get("source_type", "local")
            lora_url = lora.get("url", "")
            trigger_words = lora.get("trigger_words", [])
            
            # Add trigger words to the prompt
            if trigger_words:
                lora_prompt = ", ".join(trigger_words)
            else:
                lora_prompt = f"in the style of {lora_name}"
        else:
            # If it's just a string, use it as a style reference
            lora_prompt = f"in the style of {lora}"
        
        if lora_prompt:
            prompt = f"{prompt}, {lora_prompt}"
            print(f"Enhanced prompt with LoRA context: {prompt}")
    
    url = "https://api.stability.ai/v2beta/stable-image/generate/sd3"
    
    seed = random.randint(1, 1000000)
    
    # Prepare parameters for the API
    params = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "aspect_ratio": "1:1",  # Square aspect ratio for album covers
        "seed": seed,
        "output_format": "png",
        "model": "sd3.5-large",  # Using the flagship model
        "mode": "text-to-image"
    }
    
    try:
        # Send the request
        response_data = send_generation_request(url, params)
        
        # Check if we got a valid response
        if not response_data:
            return False
            
        # Extract image data
        if "image" in response_data:
            image_base64 = response_data["image"]
            image_bytes = base64.b64decode(image_base64)
            
            # Create image from bytes
            image = Image.open(io.BytesIO(image_bytes))
            
            # Save image if output path is specified
            if output_path:
                image.save(output_path)
                print(f"Image saved to {output_path}")
                return True
                
            return image
        else:
            print("No image data found in the response.")
            print(f"Response structure: {json.dumps(list(response_data.keys()), indent=2)}")
            return False
            
    except Exception as e:
        print(f"Error generating image: {e}")
        if output_path:
            return False
        # Return a placeholder image
        return Image.new('RGB', (512, 512), color='#3A506B')