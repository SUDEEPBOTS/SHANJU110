import aiohttp
import os
import aiofiles

# Jahan gaane save honge
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Fake Headers taaki Catbox block na kare
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36"
}

async def download_from_catbox(url: str) -> str:
    if not url:
        return None
        
    filename = url.split("/")[-1]
    path = os.path.join(DOWNLOAD_DIR, filename)

    # 1. Agar pehle se download hai, to wahi de do (Cache)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path

    # 2. Download from URL
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    print(f"❌ Catbox Error: {resp.status}")
                    return None

                async with aiofiles.open(path, mode="wb") as f:
                    async for chunk in resp.content.iter_chunked(1024 * 1024): # 1MB chunks
                        await f.write(chunk)
        return path
        
    except Exception as e:
        print(f"❌ Download Failed: {e}")
        if os.path.exists(path):
            os.remove(path)
        return None
