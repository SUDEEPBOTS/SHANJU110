import os
import aiohttp
import aiofiles
from config import YOUTUBE_IMG_URL

async def gen_thumb(videoid, title=None, duration=None, thumb_url=None, views=None, channel=None):
    # 1. Agar pehle se downloaded hai, wahi use karo (Super Fast)
    filename = f"cache/thumb{videoid}.png"
    if os.path.isfile(filename):
        return filename

    # 2. Agar URL nahi aaya, toh bana lo
    if not thumb_url:
        thumb_url = f"https://img.youtube.com/vi/{videoid}/hqdefault.jpg"

    # 3. Chup-chap download karo (No Drawing, No Editing)
    try:
        async with aiohttp.ClientSession() as session:
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
        
