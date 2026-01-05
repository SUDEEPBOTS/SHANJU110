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

    # 🔥 MODIFIED: API DEBUG FUNCTION
    async def get_api_video(self, query: str):
        # 1. Config Check
        if not MUSIC_API_URL:
            print("❌ DEBUG: MUSIC_API_URL is missing in config!")
            return None
            
        base_url = MUSIC_API_URL.rstrip("/")
        url = f"{base_url}/getvideo"
        params = {"query": query, "key": MUSIC_API_KEY}
        
        print(f"📡 DEBUG: Requesting -> {url} | Query: {query}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=30) as resp:
                    # 2. Status Check
                    print(f"📡 DEBUG: HTTP Status Code: {resp.status}")
                    
                    if resp.status == 200:
                        data = await resp.json()
                        print(f"📦 DEBUG: API Data Received: {data}") # Ye dikhayega API ne kya bheja
                        
                        if data.get("status") == 200:
                            print("✅ DEBUG: API Success!")
                            return data
                        else:
                            print(f"⚠️ DEBUG: API Internal Status not 200: {data.get('status')}")
                    else:
                        text = await resp.text()
                        print(f"❌ DEBUG: API Failed. Body: {text}")
                        
        except Exception as e:
            print(f"🔥 DEBUG: API Connection Crash: {e}")
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
            
        # Cookies Check (Crash Prevention)
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

    # 🔥 MODIFIED: TRACK FUNCTION with Debugging
    async def track(self, link: str, videoid: Union[bool, str] = None):
        
        # 1. Try Sudeep API First
        if MUSIC_API_URL and not videoid:
            print(f"🔎 DEBUG: Starting API Search for: {link}")
            api_data = await self.get_api_video(link)
            
            if api_data:
                print("✅ DEBUG: Using API Data for Track")
                track_details = {
                    "title": api_data["title"],
                    "link": api_data["link"],
                    "vidid": api_data["id"],
                    "duration_min": api_data["duration"],
                    "thumb": f"https://img.youtube.com/vi/{api_data['id']}/hqdefault.jpg",
                }
                return track_details, api_data["id"]
            else:
                print("❌ DEBUG: API returned None, switching to Local YouTube")

        # 2. Fallback to Local YouTube Search
        print("🐢 DEBUG: Executing Local VideosSearch...")
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
        
        # Cookies Safe Options
        ydl_opts = {"quiet": True}
        if os.path.exists("cookies.txt"):
            ydl_opts["cookiefile"] = "cookies.txt"

        ydl = yt_dlp.YoutubeDL(ydl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for format in r["formats"]:
                try:
                    str(format["format"])
                except:
                    continue
                if not "dash" in str(format["format"]).lower():
                    try:
                        format["format"]
                        format["filesize"]
                        format["format_id"]
                        format["ext"]
                        format["format_note"]
                    except:
                        continue
                    formats_available.append(
                        {
                            "format": format["format"],
                            "filesize": format["filesize"],
                            "format_id": format["format_id"],
                            "ext": format["ext"],
                            "format_note": format["format_note"],
                            "yturl": link,
                        }
                    )
        return formats_available, link

    async def slider(
        self,
        link: str,
        query_type: int,
        videoid: Union[bool, str] = None,
    ):
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

    # 🔥 MODIFIED: DOWNLOAD FUNCTION
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
        
        # 1. Catbox / Direct Link Check
        if "catbox.moe" in link or "files.catbox" in link:
            print(f"🚀 DEBUG: Attempting Direct Download: {link}")
            try:
                if not os.path.exists("downloads"):
                    os.makedirs("downloads")
                
                filename = link.split("/")[-1]
                xyz = os.path.join("downloads", filename)

                if os.path.exists(xyz):
                    print("✅ DEBUG: File already exists in cache")
                    return xyz, True

                async with aiohttp.ClientSession() as session:
                    async with session.get(link) as resp:
                        if resp.status == 200:
                            async with aiofiles.open(xyz, mode="wb") as f:
                                async for chunk in resp.content.iter_chunked(1024 * 1024):
                                    await f.write(chunk)
                            print("✅ DEBUG: Direct Download Complete")
                            return xyz, True
                        else:
                            print(f"❌ DEBUG: Direct Download HTTP Error: {resp.status}")
            except Exception as e:
                print(f"🔥 DEBUG: Direct Download Crash: {e}")

        # 2. Normal YouTube DL Logic (Cookie Safe)
        if videoid:
            link = self.base + link
        loop = asyncio.get_running_loop()

        # Helper to get options safely
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
            
