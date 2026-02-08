from pyrogram import filters
from pyrogram.types import Message
from RessoMusic import app
from RessoMusic.misc import mongodb

# --- SMALL CAPS FUNCTION ---
SMALL_CAPS = {
    "a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ғ", "g": "ɢ", "h": "ʜ", "i": "ɪ",
    "j": "ᴊ", "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ", "o": "ᴏ", "p": "ᴘ", "q": "ǫ", "r": "ʀ",
    "s": "s", "t": "ᴛ", "u": "ᴜ", "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ", "z": "ᴢ"
}
def txt(text: str):
    return "".join(SMALL_CAPS.get(char, char) for char in text.lower())

waifudb = mongodb.waifu_users

@app.on_message(filters.command(["top", "leaderboard"]))
async def leaderboard(_, message: Message):
    text = "🏆 **ᴛᴏᴘ 10 ᴡᴀɪғᴜ ᴄᴏʟʟᴇᴄᴛᴏʀs** 🏆\n\n"
    
    # Database se sab users nikalo
    async for user in waifudb.find().sort("collection", -1).limit(10):
        try:
            # User ka naam Telegram se fetch karte hain
            t_user = await app.get_users(user["user_id"])
            name = t_user.first_name
        except:
            name = "ᴜɴᴋɴᴏᴡɴ ᴜsᴇʀ"
            
        count = len(user.get("collection", []))
        coins = user.get("coins", 0)
        
        text += f"🔹 **{name}**\n"
        text += f"   ├── 👰 **ᴡᴀɪғᴜs:** {count}\n"
        text += f"   └── 💰 **ᴄᴏɪɴs:** {coins}\n\n"
        
    await message.reply_text(text)
  
