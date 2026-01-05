import aiohttp
# Config file se keys uthana (Make sure config.py me ye keys hon)
from config import MUSIC_API_URL, MUSIC_API_KEY 

async def get_api_video(query: str):
    """
    Tere Render API ko call karke Video Details layega.
    """
    # Agar URL me slash nahi hai to laga do
    base_url = MUSIC_API_URL.rstrip("/")
    url = f"{base_url}/getvideo"
    
    params = {
        "query": query,
        "key": MUSIC_API_KEY
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=60) as resp:
                if resp.status != 200:
                    print(f"❌ API Error: Status {resp.status}")
                    return None
                
                data = await resp.json()
                
                # Agar API ne error diya
                if data.get("status") != 200:
                    return None
                
                return data # (title, link, duration, id) sab isme hai

    except Exception as e:
        print(f"❌ API Connection Failed: {e}")
        return None
      
