import random
import aiohttp
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery, InputMediaPhoto
from RessoMusic import app
from RessoMusic.utils.waifu_db import add_waifu_to_db, check_waifu_in_collection, get_waifu_user
from config import LOG_GROUP_ID 
from RessoMusic.misc import SUDOERS  # <--- IMPORT

# --- SMALL CAPS FONT MAPPING ---
SMALL_CAPS = {
    "a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ғ", "g": "ɢ", "h": "ʜ", "i": "ɪ",
    "j": "ᴊ", "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ", "o": "ᴏ", "p": "ᴘ", "q": "ǫ", "r": "ʀ",
    "s": "s", "t": "ᴛ", "u": "ᴜ", "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ", "z": "ᴢ"
}

def txt(text: str):
    return "".join(SMALL_CAPS.get(char, char) for char in text.lower())

# --- RARITY & STATS ---
RARITY_MAP = {
    "Common": {"chance": 50, "hp": (80, 120), "wpn": ["ᴋɴɪғᴇ 🔪", "sᴛɪᴄᴋ 🪵"], "emoji": "⚪️"},
    "Rare": {"chance": 30, "hp": (150, 200), "wpn": ["ᴘɪsᴛᴏʟ 🔫", "ᴋᴀᴛᴀɴᴀ ⚔️"], "emoji": "🔵"},
    "Epic": {"chance": 15, "hp": (250, 350), "wpn": ["sɴɪᴘᴇʀ 🔭", "ᴍᴀɢɪᴄ 🪄"], "emoji": "🟣"},
    "Legendary": {"chance": 5, "hp": (500, 800), "wpn": ["ᴅᴇᴍᴏɴ sᴡᴏʀᴅ 🗡️", "ᴅʀᴀɢᴏɴ 🔥"], "emoji": "🟡"}
}

# Temporary Storage
PENDING_WAIFUS = {}

async def get_random_waifu_data():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://nekos.best/api/v2/waifu") as resp:
            data = await resp.json()
            result = data["results"][0]
            
            types = list(RARITY_MAP.keys())
            weights = [RARITY_MAP[t]["chance"] for t in types]
            rarity = random.choices(types, weights=weights, k=1)[0]
            r_data = RARITY_MAP[rarity]

            return {
                "name": result["artist_name"], 
                "img": result["url"],
                "rarity": rarity,
                "emoji": r_data["emoji"],
                "hp": random.randint(r_data["hp"][0], r_data["hp"][1]),
                "weapon": random.choice(r_data["wpn"])
            }

# --- ERROR FIX: list(SUDOERS) ---
@app.on_message(filters.command("addwaifu") & filters.user(list(SUDOERS)))
async def waifu_gen(_, message: Message):
    user_id = message.from_user.id
    waifu = await get_random_waifu_data()
    
    PENDING_WAIFUS[user_id] = waifu
    
    caption = (
        f"**☁️ ᴡᴀɪғᴜ ғᴏᴜɴᴅ!**\n\n"
        f"**🏷️ ɴᴀᴍᴇ:** `{waifu['name']}`\n"
        f"**🔮 ʀᴀʀɪᴛʏ:** {waifu['emoji']} {txt(waifu['rarity'])}\n"
        f"**❤️ ʜᴇᴀʟᴛʜ:** {waifu['hp']}\n"
        f"**⚔️ ᴡᴇᴀᴘᴏɴ:** {waifu['weapon']}\n\n"
        f"👇 *ᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴀᴅᴅ ʜᴇʀ?*"
    )
    
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text="ᴀᴅᴅ ✅", callback_data="w_add"),
            InlineKeyboardButton(text="ɴᴇxᴛ ⏭️", callback_data="w_next")
        ],
        [InlineKeyboardButton(text="ᴄᴀɴᴄᴇʟ ❌", callback_data="w_close")]
    ])
    
    await message.reply_photo(waifu['img'], caption=caption, reply_markup=buttons)

@app.on_callback_query(filters.regex("w_"))
async def waifu_callbacks(client, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id
    
    if data == "w_close":
        if user_id in PENDING_WAIFUS:
            del PENDING_WAIFUS[user_id]
        await query.message.delete()
        return

    if data == "w_next":
        if user_id not in PENDING_WAIFUS:
            return await query.answer("⚠️ This is not your session!", show_alert=True)

        waifu = await get_random_waifu_data()
        PENDING_WAIFUS[user_id] = waifu
        
        caption = (
            f"**☁️ ᴡᴀɪғᴜ ғᴏᴜɴᴅ!**\n\n"
            f"**🏷️ ɴᴀᴍᴇ:** `{waifu['name']}`\n"
            f"**🔮 ʀᴀʀɪᴛʏ:** {waifu['emoji']} {txt(waifu['rarity'])}\n"
            f"**❤️ ʜᴇᴀʟᴛʜ:** {waifu['hp']}\n"
            f"**⚔️ ᴡᴇᴀᴘᴏɴ:** {waifu['weapon']}\n\n"
            f"👇 *ᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴀᴅᴅ ʜᴇʀ?*"
        )
        
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(text="ᴀᴅᴅ ✅", callback_data="w_add"),
                InlineKeyboardButton(text="ɴᴇxᴛ ⏭️", callback_data="w_next")
            ],
            [InlineKeyboardButton(text="ᴄᴀɴᴄᴇʟ ❌", callback_data="w_close")]
        ])
        
        await query.message.edit_media(
            media=InputMediaPhoto(waifu['img'], caption=caption),
            reply_markup=buttons
        )
        return

    if data == "w_add":
        if user_id not in PENDING_WAIFUS:
            await query.answer("❌ sᴇssɪᴏɴ ᴇxᴘɪʀᴇᴅ. ᴜsᴇ /addwaifu ᴀɢᴀɪɴ.", show_alert=True)
            return
            
        waifu = PENDING_WAIFUS[user_id]
        
        is_exist = await check_waifu_in_collection(user_id, waifu['name'])
        if is_exist:
            await query.answer("⚠️ ʏᴏᴜ ᴀʟʀᴇᴀᴅʏ ʜᴀᴠᴇ ᴛʜɪs ᴡᴀɪғᴜ!", show_alert=True)
            return

        await add_waifu_to_db(user_id, waifu)
        del PENDING_WAIFUS[user_id]
        
        await query.message.edit_caption(
            caption=f"✅ **sᴜᴄᴄᴇssғᴜʟʟʏ ᴀᴅᴅᴇᴅ!**\n\n**{waifu['name']}** ɪs ɴᴏᴡ ɪɴ ʏᴏᴜʀ ᴄᴏʟʟᴇᴄᴛɪᴏɴ.",
            reply_markup=None
        )
        
        try:
            log_text = (
                f"**#ɴᴇᴡ_ᴡᴀɪғᴜ_ᴀᴅᴅᴇᴅ 👰**\n\n"
                f"**👤 ᴜsᴇʀ:** {query.from_user.mention}\n"
                f"**🏷️ ᴡᴀɪғᴜ:** {waifu['name']}\n"
                f"**🔮 ʀᴀʀɪᴛʏ:** {txt(waifu['rarity'])}\n"
                f"**❤️ ʜᴘ:** {waifu['hp']}"
            )
            await client.send_photo(LOG_GROUP_ID, photo=waifu['img'], caption=log_text)
        except Exception:
            pass
            
