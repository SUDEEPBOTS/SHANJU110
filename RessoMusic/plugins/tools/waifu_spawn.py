import asyncio
import random
import aiohttp
from pyrogram import filters, enums
from pyrogram.types import Message
from RessoMusic import app
from RessoMusic.utils.waifu_db import add_waifu_to_db, check_waifu_in_collection

# --- CONFIG ---
SPAWN_FREQUENCY = 100  # Har 100 message pe spawn hoga
MESSAGE_COUNTS = {}    # Har group ka message count store karega
SPAWNED_WAIFU = {}     # Kis group mein konsi waifu aayi hai
LAST_SPAWNED_NAMES = {} # Har group ke last spawn ko track karega (Duplicate rokne ke liye)

# --- SMALL CAPS FONT ---
SMALL_CAPS = {
    "a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ғ", "g": "ɢ", "h": "ʜ", "i": "ɪ",
    "j": "ᴊ", "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ", "o": "ᴏ", "p": "ᴘ", "q": "ǫ", "r": "ʀ",
    "s": "s", "t": "ᴛ", "u": "ᴜ", "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ", "z": "ᴢ"
}
def txt(text: str):
    return "".join(SMALL_CAPS.get(char, char) for char in text.lower())

# --- RARITY DATA ---
RARITY_MAP = {
    "Common": {"chance": 50, "hp": (80, 120), "wpn": ["ᴋɴɪғᴇ 🔪", "sᴛɪᴄᴋ 🪵"], "emoji": "⚪️"},
    "Rare": {"chance": 30, "hp": (150, 200), "wpn": ["ᴘɪsᴛᴏʟ 🔫", "ᴋᴀᴛᴀɴᴀ ⚔️"], "emoji": "🔵"},
    "Epic": {"chance": 15, "hp": (250, 350), "wpn": ["sɴɪᴘᴇʀ 🔭", "ᴍᴀɢɪᴄ 🪄"], "emoji": "🟣"},
    "Legendary": {"chance": 5, "hp": (500, 800), "wpn": ["ᴅᴇᴍᴏɴ sᴡᴏʀᴅ 🗡️", "ᴅʀᴀɢᴏɴ 🔥"], "emoji": "🟡"}
}

async def get_random_waifu_data(chat_id=None):
    async with aiohttp.ClientSession() as session:
        # Retry loop to avoid immediate duplicates
        for _ in range(3): 
            async with session.get("https://nekos.best/api/v2/waifu") as resp:
                data = await resp.json()
                result = data["results"][0]
                name = result["artist_name"]
                
                # Agar chat_id diya hai, toh check karo ki pichli waifu same to nahi hai?
                if chat_id and LAST_SPAWNED_NAMES.get(chat_id) == name:
                    continue # Skip this and try again
                
                # Agar naya naam hai, toh loop break karo
                if chat_id:
                    LAST_SPAWNED_NAMES[chat_id] = name
                
                types = list(RARITY_MAP.keys())
                weights = [RARITY_MAP[t]["chance"] for t in types]
                rarity = random.choices(types, weights=weights, k=1)[0]
                r_data = RARITY_MAP[rarity]

                return {
                    "name": name, 
                    "img": result["url"],
                    "rarity": rarity,
                    "emoji": r_data["emoji"],
                    "hp": random.randint(r_data["hp"][0], r_data["hp"][1]),
                    "weapon": random.choice(r_data["wpn"])
                }

# --- 1. WATCHER (Message Counter) ---
@app.on_message(filters.group & ~filters.bot, group=10)
async def message_watcher(_, message: Message):
    chat_id = message.chat.id
    
    if chat_id not in MESSAGE_COUNTS:
        MESSAGE_COUNTS[chat_id] = 0
        
    MESSAGE_COUNTS[chat_id] += 1
    
    if MESSAGE_COUNTS[chat_id] >= SPAWN_FREQUENCY:
        MESSAGE_COUNTS[chat_id] = 0 
        await spawn_waifu(chat_id)

async def spawn_waifu(chat_id):
    waifu = await get_random_waifu_data(chat_id)
    SPAWNED_WAIFU[chat_id] = waifu
    
    caption = (
        f"⚡ **ᴀ ᴡɪʟᴅ ᴡᴀɪғᴜ ᴀᴘᴘᴇᴀʀᴇᴅ!** ⚡\n\n"
        f"🏷️ **ɴᴀᴍᴇ:** `???` (ɢᴜᴇss ᴛʜᴇ ɴᴀᴍᴇ!)\n"
        f"🔮 **ʀᴀʀɪᴛʏ:** {waifu['emoji']} {txt(waifu['rarity'])}\n"
        f"❤️ **ʜᴘ:** {waifu['hp']}\n\n"
        f"👇 **ᴛᴏ ᴄᴏʟʟᴇᴄᴛ ʜᴇʀ:**\n"
        f"Tyᴘᴇ: `/collect {waifu['name']}`\n"
        f"Or just: `/grab {waifu['name']}`"
    )
    
    # SPOILER Added (has_spoiler=True)
    await app.send_photo(chat_id, photo=waifu['img'], caption=caption, has_spoiler=True)


# --- 2. COLLECT COMMAND ---
@app.on_message(filters.command(["collect", "grab", "catch"]))
async def collect_waifu(_, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if chat_id not in SPAWNED_WAIFU:
        return await message.reply_text("❌ **ᴛʜᴇʀᴇ ɪs ɴᴏ ᴡᴀɪғᴜ ᴛᴏ ᴄᴏʟʟᴇᴄᴛ!**\nWait for the next spawn.")
        
    waifu = SPAWNED_WAIFU[chat_id]
    
    if len(message.command) < 2:
        return await message.reply_text(f"⚠️ **ɢɪᴠᴇ ᴍᴇ ᴀ ɴᴀᴍᴇ!**\nExample: `/collect {waifu['name']}`", quote=True)
        
    input_name = " ".join(message.command[1:]).lower()
    waifu_name = waifu["name"].lower()
    
    if input_name == waifu_name:
        if await check_waifu_in_collection(user_id, waifu['name']):
             return await message.reply_text("⚠️ **ʏᴏᴜ ᴀʟʀᴇᴀᴅʏ ʜᴀᴠᴇ ᴛʜɪs ᴡᴀɪғᴜ!**\nLet someone else grab her.")

        await add_waifu_to_db(user_id, waifu)
        del SPAWNED_WAIFU[chat_id]
        
        await message.reply_text(
            f"🎉 **ᴄᴏɴɢʀᴀᴛᴜʟᴀᴛɪᴏɴs!**\n\n"
            f"👤 {message.from_user.mention} just collected **{txt(waifu['name'])}**!\n"
            f"Added to your collection."
        )
    else:
        await message.reply_text("❌ **ᴡʀᴏɴɢ ɴᴀᴍᴇ!** ᴛʀʏ ᴀɢᴀɪɴ.")

# --- 3. TEST COMMAND (ADMIN ONLY OPTIONAL) ---
# Isse tu manually spawn kar sakta hai check karne ke liye
@app.on_message(filters.command("wtest") & filters.group)
async def test_spawn(_, message: Message):
    await message.reply_text("⚙️ **Fᴏʀᴄɪɴɢ ᴀ Sᴘᴀᴡɴ...**")
    await spawn_waifu(message.chat.id)
                
