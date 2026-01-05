import asyncio
import os
import re
from typing import Union
import aiohttp
import aiofiles
import yt_dlp # Sirf metadata ke liye rakha hai
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch

from RessoMusic.utils.database import is_on_off
from RessoMusic.utils.formatters import time_to_seconds
from config import MUSIC_API_URL, MUSIC_API_KEY


async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    if errorz:
        if "unavailable videos are hidden" in (errorz.decode("utf-8")).lower():
            return out.decode("utf-8")
        else:
            return errorz.decode("utf-8")
    return out.decode("utf-8")


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    # 🔥 API FUNCTION
    async def get_api_video(self, query: str):
        if not MUSIC_API_URL:
            return None
            
        base_url = MUSIC_API_URL.rstrip("/")
        url = f"{base_url}/getvideo"
        params = {"query": query, "key": MUSIC_API_KEY}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=30) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("status") == 200:
                            return data
        except Exception as e:
            print(f"⚠️ API Error: {e}")
        return None

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if re.search(self.regex, link):
            return True
        else:
            return False

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        text = ""
        offset = None
        length = None
        for message in messages:
            if offset:
                break
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        offset, length = entity.offset, entity.length
                        break
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        if offset in (None,):
            return None

        umm = text[offset : offset + length]
        if "?si=" in umm:
            umm = umm.split("?si=")[0]
        return umm

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]
            if str(duration_min) == "None":
                duration_sec = 0
            else:
                duration_sec = int(time_to_seconds(duration_min))
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
        return title

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            duration = result["duration"]
        return duration

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        return thumbnail

    async def video(self, link: str, videoid: Union[bool, str] = None):
        # ⚠️ LOCAL STREAM LINK GENERATION DISABLED
        # Humne isko disable kar diya hai taki ye YouTube se connect na ho
        return 0, "Local YouTube Disabled"

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        # Playlist Metadata fetch is Safe (No Download)
        playlist = await shell_cmd(
            f"yt-dlp -i --get-id --flat-playlist --playlist-end {limit} --skip-download {link}"
        )
        try:
            result = playlist.split("\n")
            for key in result:
                if key == "":
                    result.remove(key)
        except:
            result = []
        return result

    # 🔥 TRACK FUNCTION
async def track(self, link: str, videoid: Union[bool, str] = None):

    # 1. API Call (Yehi Main Hai)
    if MUSIC_API_URL and not videoid:
        api_data = await self.get_api_video(link)
        if api_data:
            file_url = api_data["link"]

            file_path, ok = await self.download(file_url, None)
            if not ok or not file_path:
                print("❌ API file download failed")
                return None, None

            return {
                "title": api_data["title"],
                "link": file_url,
                "path": file_path,   # ✅ LOCAL FILE PATH
                "vidid": api_data["id"],
                "duration_min": api_data["duration"],
                "thumb": f"https://img.youtube.com/vi/{api_data['id']}/hqdefault.jpg",
            }, api_data["id"]
        # 2. Metadata Fallback (Sirf Naam Pata karne ke liye)
        # Download nahi karega, bas agar API fail hui to user ko error dikhane ke liye naam layega
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            vidid = result["id"]
            yturl = result["link"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        
        track_details = {
            "title": title,
            "link": yturl,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }
        return track_details, vidid

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        ytdl_opts = {"quiet": True}
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for format in r["formats"]:
                formats_available.append(
                    {
                        "format": format.get("format"),
                        "filesize": format.get("filesize"),
                        "ext": format.get("ext"),
                        "yturl": link,
                    }
                )
        return formats_available, link

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        a = VideosSearch(link, limit=10)
        result = (await a.next()).get("result")
        title = result[query_type]["title"]
        duration_min = result[query_type]["duration"]
        vidid = result[query_type]["id"]
        thumbnail = result[query_type]["thumbnails"][0]["url"].split("?")[0]
        return title, duration_min, thumbnail, vidid


    async def download(   # ✅ SAME INDENT LEVEL
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        if "catbox.moe" in link or "files.catbox" in link or "http" in link:
            print(f"🚀 Direct Download Started: {link}")
            try:
                if not os.path.exists("downloads"):
                    os.makedirs("downloads")
                
                filename = link.split("/")[-1]
                xyz = os.path.join("downloads", filename)

                if os.path.exists(xyz):
                    return xyz, True

                timeout = aiohttp.ClientTimeout(total=600)
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }

                async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                    async with session.get(link) as resp:
                        if resp.status == 200:
                            async with aiofiles.open(xyz, mode="wb") as f:
                                async for chunk in resp.content.iter_chunked(1024 * 512):
                                    await f.write(chunk)
                            print(f"✅ Download Complete: {xyz}")
                            return xyz, True
                        else:
                            print(f"❌ HTTP Status: {resp.status}")
                            return None, False
            except Exception as e:
                print(f"🔥 Download Crash: {e}")
                return None, False

        print("⛔ Local YouTube Download is OFF.")
        return None, False
