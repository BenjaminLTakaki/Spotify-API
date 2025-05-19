import random
import string
import json
import datetime
import re
import urllib.parse
from pathlib import Path
import os
import requests
from config import DATA_DIR, LORA_DIR, LORA_CONFIG_PATH
from models import LoraModel

def generate_random_string(size=10):
    """Generate a random string of letters and digits."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=size))

def save_generation_data(data, output_path=None):
    """Save generation data to JSON file."""
    try:
        # Create a unique filename based on timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in data.get("item_name", "") if c.isalnum() or c in [' ', '-', '_']).strip()
        safe_name = safe_name.replace(' ', '_')
        json_filename = f"{timestamp}_{safe_name}.json"
        
        with open(DATA_DIR / json_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Data saved to {DATA_DIR / json_filename}")
        
        return str(DATA_DIR / json_filename)
    except Exception as e:
        print(f"Error saving data: {e}")
        return None

def get_available_loras():
    """Get list of available LoRAs (both local and from links)."""
    loras = []
    
    try:
        # First, get local LoRAs
        local_loras = []
        for ext in [".safetensors", ".ckpt", ".pt"]:
            local_loras.extend(list(LORA_DIR.glob(f"*{ext}")))
        
        # Convert to LoraModel objects
        for lora in local_loras:
            loras.append(LoraModel(
                name=lora.stem,
                source_type="local",
                path=str(lora),
                url="",
                trigger_words=[],
                strength=0.7
            ))
        
        # Next, get LoRAs from config file
        if os.path.exists(LORA_CONFIG_PATH):
            with open(LORA_CONFIG_PATH, 'r') as f:
                lora_config = json.load(f)
                
            for lora_data in lora_config.get("loras", []):
                if lora_data.get("source_type") == "link":
                    loras.append(LoraModel.from_dict(lora_data))
        
        # Sort by name
        loras.sort(key=lambda x: x.name)
        return loras
    except Exception as e:
        print(f"Error getting LoRAs: {e}")
        return []

def add_lora_link(name, url, trigger_words=None, strength=0.7):
    """Add a LoRA via link to the configuration."""
    try:
        # Make sure name is valid and unique
        name = name.strip()
        if not name:
            return False, "LoRA name cannot be empty"
        
        # Read existing config
        lora_config = {"loras": []}
        if os.path.exists(LORA_CONFIG_PATH):
            with open(LORA_CONFIG_PATH, 'r') as f:
                lora_config = json.load(f)
        
        # Check if LoRA with this name already exists
        existing_names = [lora.get("name") for lora in lora_config.get("loras", [])]
        
        # For local LoRAs, check filesystem as well
        local_loras = get_available_loras()
        existing_names.extend([lora.name for lora in local_loras if lora.is_local])
        
        if name in existing_names:
            return False, f"LoRA with name '{name}' already exists"
        
        # Validate URL format
        if not is_valid_lora_url(url):
            return False, "Invalid LoRA URL format"
        
        # Create LoRA model
        new_lora = {
            "name": name,
            "source_type": "link",
            "path": "",
            "url": url,
            "trigger_words": trigger_words or [],
            "strength": float(strength)
        }
        
        # Add to config
        lora_config.setdefault("loras", []).append(new_lora)
        
        # Save config
        with open(LORA_CONFIG_PATH, 'w') as f:
            json.dump(lora_config, f, indent=2)
        
        return True, f"LoRA '{name}' added successfully"
    except Exception as e:
        print(f"Error adding LoRA link: {e}")
        return False, f"Error adding LoRA link: {str(e)}"

def is_valid_lora_url(url):
    """Validate if a URL is likely to be a valid LoRA URL."""
    # Check basic URL format
    try:
        result = urllib.parse.urlparse(url)
        if not all([result.scheme, result.netloc]):
            return False
        
        # Common LoRA hosting sites
        known_hosts = [
            'civitai.com', 
            'huggingface.co',
            'cloudflare.com',
            'discord.com',
            'githubusercontent.com'
        ]
        
        # Check if host is a common LoRA hosting site
        host_match = any(host in result.netloc for host in known_hosts)
        
        # Check file extension for direct file links
        path = result.path.lower()
        ext_match = path.endswith(('.safetensors', '.ckpt', '.pt', '.bin'))
        
        # If it's a known host or has a valid extension, consider it valid
        return host_match or ext_match
    except:
        return False

def create_image_filename(title):
    """Create a safe filename for the image."""
    safe_title = "".join(c for c in title if c.isalnum() or c in [' ', '-', '_']).strip()
    safe_title = safe_title.replace(' ', '_')
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{safe_title}.png"

def extract_lora_id_from_civitai(url):
    """Extract the LoRA ID from a Civitai URL."""
    # Example: https://civitai.com/models/12345/my-lora
    try:
        match = re.search(r'/models/(\d+)', url)
        if match:
            return match.group(1)
        return None
    except:
        return None

def get_lora_details_from_civitai(lora_id):
    """Get LoRA details from Civitai API."""
    try:
        response = requests.get(f"https://civitai.com/api/v1/models/{lora_id}")
        if response.status_code == 200:
            data = response.json()
            
            # Extract relevant information
            name = data.get("name", "")
            description = data.get("description", "")
            
            # Get trigger words and download URL from the latest version
            trigger_words = []
            download_url = ""
            
            if "modelVersions" in data and len(data["modelVersions"]) > 0:
                latest_version = data["modelVersions"][0]
                
                # Get trigger words
                if "trainedWords" in latest_version:
                    trigger_words = latest_version["trainedWords"]
                
                # Get download URL - requires authentication, so we'll use the base URL
                download_url = url
            
            return {
                "name": name,
                "description": description,
                "trigger_words": trigger_words,
                "download_url": download_url
            }
        
        return None
    except Exception as e:
        print(f"Error fetching Civitai LoRA details: {e}")
        return None