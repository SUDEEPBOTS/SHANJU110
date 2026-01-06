import os
import aiohttp
import aiofiles
from config import YOUTUBE_IMG_URL

async def gen_thumb(videoid, title=None, duration=None, thumb_url=None, views=None, channel=None):
    # 1. Cache Check
    filename = f"cache/thumb{videoid}.png"
    if os.path.isfile(filename):
        return filename

    # 2. URL Fallback
    if not thumb_url:
        thumb_url = f"https://img.youtube.com/vi/{videoid}/hqdefault.jpg"

    # 3. Download with HEADERS (Ye zaruri hai!)
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(thumb_url) as resp:
                if resp.status == 200:
                    if not os.path.exists("cache"):
                        os.makedirs("cache")
                    
                    async with aiofiles.open(filename, mode="wb") as f:
                        await f.write(await resp.read())
                    
                    return filename
                else:
                    return None
    except Exception as e:
        print(f"❌ Thumbnail Error: {e}")
        return None
        
