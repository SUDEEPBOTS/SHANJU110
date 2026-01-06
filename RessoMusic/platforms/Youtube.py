import asyncio
import os
import re
from typing import Union
import aiohttp
import aiofiles
import yt_dlp 
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
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "-g",
            "-f",
            "best[height<=?720][width<=?1280]",
            f"{link}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            return 1, stdout.decode().split("\n")[0]
        else:
            return 0, stderr.decode()

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        
        cookie_arg = "--cookies cookies.txt" if os.path.exists("cookies.txt") else ""
        playlist = await shell_cmd(
            f"yt-dlp -i --get-id --flat-playlist --playlist-end {limit} --skip-download {cookie_arg} {link}"
        )
        try:
            result = playlist.split("\n")
            for key in result:
                if key == "":
                    result.remove(key)
        except:
            result = []
        return result

    async def track(self, link: str, videoid: Union[bool, str] = None):
        
        # 1. API Call
        if MUSIC_API_URL and not videoid:
            api_data = await self.get_api_video(link)
            if api_data:
                return {
                    "title": api_data["title"],
                    "link": api_data["link"], 
                    "vidid": api_data["id"],
                    "duration_min": api_data["duration"],
                    "thumb": f"https://img.youtube.com/vi/{api_data['id']}/hqdefault.jpg",
                }, api_data["id"]

        # 2. Local Fallback (Metadata)
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
        if os.path.exists("cookies.txt"):
            ytdl_opts["cookiefile"] = "cookies.txt"
            
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

    # 🔥 DOWNLOAD FUNCTION (HYBRID: DIRECT + LOCAL FALLBACK)
    async def download(
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
        
        # ✅ 1. DIRECT DOWNLOAD (API/Catbox)
        if "catbox.moe" in link or "files.catbox" in link or "http" in link:
            # Check: Agar Youtube link nahi hai tabhi direct try karo
            if "youtube.com" not in link and "youtu.be" not in link:
                print(f"🚀 DEBUG: Attempting Direct Download: {link}")
                try:
                    if not os.path.exists("downloads"):
                        os.makedirs("downloads")
                    
                    filename = link.split("/")[-1]
                    xyz = os.path.join("downloads", filename)

                    if os.path.exists(xyz):
                        return xyz, True

                    # Headers + Timeout to fix Disconnects
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    }
                    timeout = aiohttp.ClientTimeout(total=600)

                    async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
                        async with session.get(link) as resp:
                            if resp.status == 200:
                                async with aiofiles.open(xyz, mode="wb") as f:
                                    async for chunk in resp.content.iter_chunked(1024 * 512):
                                        await f.write(chunk)
                                print("✅ DEBUG: Direct Download Complete")
                                return xyz, True
                            else:
                                print(f"❌ DEBUG: Failed HTTP: {resp.status}")
                except Exception as e:
                    print(f"🔥 DEBUG: Direct Download Crash: {e}")
                # Crash hua toh niche Local Fallback chalega 👇

        # ✅ 2. LOCAL DOWNLOAD FALLBACK (YouTube DL)
        # Ye tabhi chalega jab upar wala fail ho ya link YouTube ka ho
        print("🐢 DEBUG: Switching to Local YouTube Download...")
        if videoid:
            link = self.base + link
        loop = asyncio.get_running_loop()

        def get_opts(tmpl, fmt):
            opts = {
                "format": fmt,
                "outtmpl": tmpl,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
            }
            if os.path.exists("cookies.txt"):
                opts["cookiefile"] = "cookies.txt"
            return opts

        def audio_dl():
            x = yt_dlp.YoutubeDL(get_opts("downloads/%(id)s.%(ext)s", "bestaudio/best"))
            info = x.extract_info(link, False)
            xyz = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(xyz):
                return xyz
            x.download([link])
            return xyz

        def video_dl():
            x = yt_dlp.YoutubeDL(get_opts("downloads/%(id)s.%(ext)s", "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])"))
            info = x.extract_info(link, False)
            xyz = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(xyz):
                return xyz
            x.download([link])
            return xyz

        def song_video_dl():
            opts = get_opts(f"downloads/{title}", f"{format_id}+140")
            opts["prefer_ffmpeg"] = True
            opts["merge_output_format"] = "mp4"
            x = yt_dlp.YoutubeDL(opts)
            x.download([link])

        def song_audio_dl():
            opts = get_opts(f"downloads/{title}.%(ext)s", format_id)
            opts["prefer_ffmpeg"] = True
            opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ]
            x = yt_dlp.YoutubeDL(opts)
            x.download([link])

        # Execute in Thread
        try:
            if songvideo:
                await loop.run_in_executor(None, song_video_dl)
                fpath = f"downloads/{title}.mp4"
                return fpath
            elif songaudio:
                await loop.run_in_executor(None, song_audio_dl)
                fpath = f"downloads/{title}.mp3"
                return fpath
            elif video:
                if await is_on_off(1):
                    direct = True
                    downloaded_file = await loop.run_in_executor(None, video_dl)
                else:
                    cmd_list = ["yt-dlp", "-g", "-f", "best[height<=?720][width<=?1280]", f"{link}"]
                    if os.path.exists("cookies.txt"):
                        cmd_list.extend(["--cookies", "cookies.txt"])
                    proc = await asyncio.create_subprocess_exec(
                        *cmd_list,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, stderr = await proc.communicate()
                    if stdout:
                        downloaded_file = stdout.decode().split("\n")[0]
                        direct = None
                    else:
                        return
            else:
                direct = True
                downloaded_file = await loop.run_in_executor(None, audio_dl)
            
            return downloaded_file, direct
        
        except Exception as e:
            print(f"❌ Local DL Error: {e}")
            return None, False
            
