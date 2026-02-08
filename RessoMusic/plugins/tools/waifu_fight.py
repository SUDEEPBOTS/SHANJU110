import random
import asyncio
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from RessoMusic import app
from RessoMusic.utils.waifu_db import (
    get_waifu_user, 
    get_random_waifu_from_user, 
    steal_waifu, 
    transfer_coins
)
from config import LOG_GROUP_ID

# --- SMALL CAPS FUNCTION ---
SMALL_CAPS = {
    "a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ғ", "g": "ɢ", "h": "ʜ", "i": "ɪ",
    "j": "ᴊ", "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ", "o": "ᴏ", "p": "ᴘ", "q": "ǫ", "r": "ʀ",
    "s": "s", "t": "ᴛ", "u": "ᴜ", "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ", "z": "ᴢ"
}
def txt(text: str):
    return "".join(SMALL_CAPS.get(char, char) for char in text.lower())

# Store Active Challenges: {message_id: (challenger_id, opponent_id)}
FIGHTS = {}

@app.on_message(filters.command("fight") & filters.group)
async def fight_handler(_, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("⚠️ **ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴛᴏ ғɪɢʜᴛ!**")
    
    challenger = message.from_user
    opponent = message.reply_to_message.from_user
    
    if opponent.id == challenger.id or opponent.is_bot:
        return await message.reply_text("⚠️ **ʏᴏᴜ ᴄᴀɴ'ᴛ ғɪɢʜᴛ ʏᴏᴜʀsᴇʟғ ᴏʀ ʙᴏᴛs!**")

    # Check if both have Waifus
    c_waifu = await get_random_waifu_from_user(challenger.id)
    o_waifu = await get_random_waifu_from_user(opponent.id)

    if not c_waifu:
        return await message.reply_text("❌ **ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀɴʏ ᴡᴀɪғᴜ!**\nᴜsᴇ /addwaifu ғɪʀsᴛ.")
    if not o_waifu:
        return await message.reply_text("❌ **ᴏᴘᴘᴏɴᴇɴᴛ ʜᴀs ɴᴏ ᴡᴀɪғᴜs!**\nᴛʜᴇʏ ᴀʀᴇ ᴛᴏᴏ ᴡᴇᴀᴋ.")

    # Send Challenge
    msg = await message.reply_text(
        f"⚔️ **ᴡᴀɪғᴜ ᴡᴀʀs!**\n\n"
        f"👑 **{challenger.mention}** ʜᴀs ᴄʜᴀʟʟᴇɴɢᴇᴅ **{opponent.mention}**!\n\n"
        f"👇 **ᴅᴏ ʏᴏᴜ ᴀᴄᴄᴇᴘᴛ?**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("ᴀᴄᴄᴇᴘᴛ ⚔️", callback_data=f"f_acc_{challenger.id}_{opponent.id}"),
             InlineKeyboardButton("ᴅᴇᴄʟɪɴᴇ ❌", callback_data=f"f_dec_{challenger.id}_{opponent.id}")]
        ])
    )

@app.on_callback_query(filters.regex("f_"))
async def fight_callback(client, query: CallbackQuery):
    data = query.data.split("_")
    action = data[1]
    challenger_id = int(data[2])
    opponent_id = int(data[3])
    user_id = query.from_user.id

    if action == "dec":
        if user_id == opponent_id:
            await query.message.edit_text("❌ **ғɪɢʜᴛ ᴅᴇᴄʟɪɴᴇᴅ!**")
        elif user_id == challenger_id:
            await query.message.edit_text("❌ **ʏᴏᴜ ᴄᴀɴᴄᴇʟʟᴇᴅ ᴛʜᴇ ғɪɢʜᴛ.**")
        else:
            await query.answer("⚠️ ᴛʜɪs ɪs ɴᴏᴛ ғᴏʀ ʏᴏᴜ!", show_alert=True)
        return

    if action == "acc":
        if user_id != opponent_id:
            return await query.answer("⚠️ ᴏɴʟʏ ᴛʜᴇ ᴏᴘᴘᴏɴᴇɴᴛ ᴄᴀɴ ᴀᴄᴄᴇᴘᴛ!", show_alert=True)

        # Start Fight Logic
        await query.message.edit_text("⏳ **ᴘʀᴇᴘᴀʀɪɴɢ ʙᴀᴛᴛʟᴇғɪᴇʟᴅ...**")
        
        # 1. Fetch Fighters (Randomly chosen)
        p1_waifu = await get_random_waifu_from_user(challenger_id)
        p2_waifu = await get_random_waifu_from_user(opponent_id)

        # Safety Check
        if not p1_waifu or not p2_waifu:
            return await query.message.edit_text("⚠️ **ᴇʀʀᴏʀ:** sᴏᴍᴇᴏɴᴇ ʟᴏsᴛ ᴛʜᴇɪʀ ᴡᴀɪғᴜ ʙᴇғᴏʀᴇ ᴛʜᴇ ғɪɢʜᴛ!")

        # 2. Display Matchup
        text = (
            f"🥊 **ʙᴀᴛᴛʟᴇ sᴛᴀʀᴛ!**\n\n"
            f"🔵 **ᴘʟᴀʏᴇʀ 1:** {txt(p1_waifu['name'])}\n"
            f"   ❤️ ʜᴘ: {p1_waifu['hp']} | ⚔️ {p1_waifu['weapon']}\n\n"
            f"🔴 **ᴘʟᴀʏᴇʀ 2:** {txt(p2_waifu['name'])}\n"
            f"   ❤️ ʜᴘ: {p2_waifu['hp']} | ⚔️ {p2_waifu['weapon']}\n\n"
            f"⚡ **ғɪɢʜᴛɪɴɢ...**"
        )
        await query.message.edit_text(text)
        await asyncio.sleep(2) # Suspense

        # 3. Calculate Winner (HP based logic)
        # Luck factor: Add random -20 to +20 to HP for surprise wins
        p1_score = p1_waifu['hp'] + random.randint(-20, 20)
        p2_score = p2_waifu['hp'] + random.randint(-20, 20)

        winner_id = None
        loser_id = None
        win_waifu = None
        lose_waifu = None

        if p1_score >= p2_score:
            winner_id = challenger_id
            loser_id = opponent_id
            win_waifu = p1_waifu
            lose_waifu = p2_waifu
        else:
            winner_id = opponent_id
            loser_id = challenger_id
            win_waifu = p2_waifu
            lose_waifu = p1_waifu

        # 4. Process Rewards (Steal Waifu)
        # Try to steal the specific waifu used in battle
        try:
            await steal_waifu(loser_id, winner_id, lose_waifu)
            reward_text = f"🎁 **ᴡɪɴɴᴇʀ sᴛᴏʟᴇ:** {txt(lose_waifu['name'])}!"
            log_reward = f"Waifu Stolen: {lose_waifu['name']}"
        except Exception:
            # Fallback: Agar steal fail ho gaya (waifu missing), coins lo
            amt = await transfer_coins(loser_id, winner_id, 500)
            reward_text = f"💰 **ᴡɪɴɴᴇʀ ɢᴏᴛ:** {amt} ᴄᴏɪɴs!"
            log_reward = f"Coins Won: {amt}"

        # 5. Final Message
        final_text = (
            f"🏆 **ᴡɪɴɴᴇʀ:** <a href='tg://user?id={winner_id}'>ᴡɪɴɴᴇʀ</a> 🎉\n"
            f"💀 **ʟᴏsᴇʀ:** <a href='tg://user?id={loser_id}'>ʟᴏsᴇʀ</a>\n\n"
            f"{reward_text}\n"
            f"🗡️ **ᴡᴇᴀᴘᴏɴ ᴜsᴇᴅ:** {win_waifu['weapon']}"
        )
        
        # Image of Winning Waifu
        await query.message.reply_photo(
            photo=win_waifu['img'],
            caption=final_text
        )
        
        # Log to Channel
        try:
            await client.send_message(
                LOG_GROUP_ID,
                f"**#WAIFU_WAR_RESULT**\nWinner: {winner_id}\nLoser: {loser_id}\nReward: {log_reward}"
            )
        except:
            pass
      
