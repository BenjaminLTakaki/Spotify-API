import requests
import json
from config import GEMINI_API_KEY, GEMINI_API_URL

def generate_title(playlist_data, mood=""):
    """Generate album title using Gemini API"""
    if not GEMINI_API_KEY:
        print("ERROR: Missing Gemini API key. Please set GEMINI_API_KEY in your .env file.")
        return "New Album"
    
    genres = ", ".join(playlist_data.get("genres", ["music"]))
    mood_to_use = mood if mood else playlist_data.get("mood_descriptor", "")
    
    style_elements = playlist_data.get("style_elements", [])
    style_text = ", ".join(style_elements) if style_elements else ""
    
    prompt = f"""You are creating a unique, evocative album title. 
Create a single, short album title (3-5 words) for a {genres} music album. 
The album cover has these visual elements: {style_text}. Avoid clichés like 
'Neon', 'Tokyo', 'Bloom', 'Sakura' or other stereotypical words. This is just 
an example for the genre j-pop but obviously don't reuse generic titles for other genres too.
Create a title that is poetic, emotionally resonant, and truly original.
Create a title that reflects both the music genres and these visual elements.
Respond with only the title, nothing else."""

    try:
        # Prepare the request to Gemini API
        headers = {
            "Content-Type": "application/json",
        }
        
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.9,
                "maxOutputTokens": 20,
                "topP": 0.8
            }
        }
        
        # Add API key to URL
        url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
        
        # Make the request
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            response_json = response.json()
            # Extract the title from the response
            if 'candidates' in response_json and len(response_json['candidates']) > 0:
                text = response_json['candidates'][0]['content']['parts'][0]['text']
                # Clean up the title
                title = text.strip().replace('"', '').replace("'", "")
                return title[:50] if title and len(title) >= 3 else "New Album"
        
        print(f"Error generating title: {response.text}")
        return "New Album"
        
    except Exception as e:
        print(f"Error generating title: {e}")
        return "New Album"