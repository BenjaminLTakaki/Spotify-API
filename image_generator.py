import requests
import json
import os
import base64
from PIL import Image
import io
import time
from config import STABILITY_API_KEY, DEFAULT_NEGATIVE_PROMPT, COVERS_DIR

# Cache for engine ID to avoid repeated API calls
_ENGINE_ID_CACHE = None

def get_engine_id():
    """Get the most appropriate engine ID for text-to-image generation"""
    global _ENGINE_ID_CACHE
    
    # Return cached engine ID if available
    if _ENGINE_ID_CACHE:
        return _ENGINE_ID_CACHE
    
    # Check if we have API key
    if not STABILITY_API_KEY:
        print("ERROR: Missing Stability API key. Please set STABILITY_API_KEY in your .env file.")
        return None
    
    # Get available engines
    engines_url = "https://api.stability.ai/v1/engines/list"
    
    headers = {
        "Authorization": f"Bearer {STABILITY_API_KEY}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(engines_url, headers=headers)
        
        if response.status_code != 200:
            print(f"Error getting engines: {response.status_code}")
            print(f"Details: {response.text}")
            # Fall back to default engine ID
            _ENGINE_ID_CACHE = "stable-diffusion-xl-1024-v1-0"
            return _ENGINE_ID_CACHE
        
        engines_data = response.json()
        
        # Filter for Stable Diffusion engines
        sd_engines = [engine for engine in engines_data if "stable-diffusion" in engine['id'].lower()]
        if not sd_engines:
            print("No Stable Diffusion engines found. Using default.")
            _ENGINE_ID_CACHE = "stable-diffusion-xl-1024-v1-0"
            return _ENGINE_ID_CACHE
        
        # Prefer SDXL if available
        sdxl_engines = [engine for engine in sd_engines if "xl" in engine['id'].lower()]
        selected_engine = sdxl_engines[0]['id'] if sdxl_engines else sd_engines[0]['id']
        
        print(f"Using Stability AI engine: {selected_engine}")
        _ENGINE_ID_CACHE = selected_engine
        return _ENGINE_ID_CACHE
        
    except Exception as e:
        print(f"Error fetching engine list: {e}")
        # Fall back to default engine ID
        _ENGINE_ID_CACHE = "stable-diffusion-xl-1024-v1-0"
        return _ENGINE_ID_CACHE

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

def generate_cover_image(prompt, lora=None, output_path=None, negative_prompt=DEFAULT_NEGATIVE_PROMPT):
    """Generate album cover image using Stability AI API"""
    # Get the appropriate engine ID
    engine_id = get_engine_id()
    if not engine_id:
        print("ERROR: Could not determine Stability AI engine ID.")
        return False
    
    print(f"Generating with prompt: {prompt}")
    
    # Configure API URL and headers
    url = f"https://api.stability.ai/v1/generation/{engine_id}/text-to-image"
    
    headers = {
        "Authorization": f"Bearer {STABILITY_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Prepare text prompts
    text_prompts = [
        {
            "text": prompt,
            "weight": 1.0
        }
    ]
    
    # Add negative prompt if provided
    if negative_prompt:
        text_prompts.append({
            "text": negative_prompt,
            "weight": -1.0
        })
    
    # LoRA support is limited in the Stability API
    # If LoRA is provided, we can add it as additional prompt context
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
        
        # Add LoRA context to the prompt if we have it
        if lora_prompt:
            # Add to existing prompt
            enhanced_prompt = f"{prompt}, {lora_prompt}"
            # Update the prompt in the payload
            text_prompts[0]["text"] = enhanced_prompt
            print(f"Enhanced prompt with LoRA context: {enhanced_prompt}")
    
    # Prepare the JSON payload
    payload = {
        "text_prompts": text_prompts,
        "cfg_scale": 7.0,
        "height": 1024,
        "width": 1024,
        "samples": 1,
        "steps": 30
    }
    
    try:
        # Make the API request
        response = requests.post(url, headers=headers, json=payload)
        
        # Check response
        if response.status_code != 200:
            print(f"Error: API returned status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        # Parse the response
        response_data = response.json()
        
        # Extract the image data
        if "artifacts" in response_data and len(response_data["artifacts"]) > 0:
            image_base64 = response_data["artifacts"][0]["base64"]
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