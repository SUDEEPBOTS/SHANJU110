import asyncio
import random
from datetime import datetime
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from RessoMusic import app
from RessoMusic.misc import SUDOERS
from config import BANNED_USERS

# Import Database functions
from RessoMusic.plugins.tools.quiz_db import (
    smcp, add_points, get_leaderboard, reset_leaderboard,
    set_prize, get_prize, add_question, get_random_question,
    get_stored_month, set_stored_month
)

# ================= CONFIGURATION =================
# Put your Main Group ID here (e.g. -100123456789)
MAIN_GROUP_ID = -1003482585012

# Updated Links
PROOF_LINK = "https://t.me/Aura_Hunter"
MAIN_GROUP_LINK = "https://t.me/+wHJrM9GWRgtmMzZl"
# =================================================

# --- GLOBAL VARS ---
MSG_COUNTS = {}
QUIZ_STATE = {}
TRIGGER_LIMIT = 70

# --- REDIRECT HANDLER (For DMs & Other Groups) ---
# Triggers if someone uses quiz commands outside the main group
@app.on_message((filters.private | filters.group) & ~filters.chat(MAIN_GROUP_ID) & ~filters.bot & ~BANNED_USERS)
async def redirect_handler(client, message):
    if not message.text or not message.text.startswith("/"):
        return

    # Removed "/start" from here so it doesn't conflict with your bot's main start
    if message.text.split()[0] in ["/quiz", "/leaderboard", "/top", "/rank"]:
        prizes = await get_prize()
        txt = (
            f"🚫 **{smcp('Wrong Place!')}**\n\n"
            f"🎮 {smcp('The Quiz Tournament is running only in the Main Group.')}\n\n"
            f"🎁 **{smcp('Current Prizes')}:**\n{prizes}"
        )
        btn = InlineKeyboardMarkup([
            [InlineKeyboardButton(text="🔥 JOIN MAIN GROUP", url=MAIN_GROUP_LINK)]
        ])
        await message.reply(txt, reply_markup=btn)

# --- WATCHER: MESSAGE COUNTER (ONLY MAIN GROUP) ---
@app.on_message(filters.chat(MAIN_GROUP_ID) & ~filters.bot & ~BANNED_USERS, group=69)
async def quiz_watcher(client, message):
    if not message.text:
        return
        
    chat_id = message.chat.id
    current = MSG_COUNTS.get(chat_id, 0)
    MSG_COUNTS[chat_id] = current + 1

    if MSG_COUNTS[chat_id] >= TRIGGER_LIMIT:
        MSG_COUNTS[chat_id] = 0
        await send_quiz(chat_id)

# --- AUTO MONTHLY END SYSTEM ---
async def check_season_end():
    while True:
        try:
            now_month = datetime.now().strftime("%Y-%m") # e.g., "2026-01"
            stored_month = await get_stored_month()

            if stored_month is None:
                await set_stored_month(now_month)
            
            elif stored_month != now_month:
                # Month Change Detected! End Season Automatically.
                await end_season_logic(auto=True)
                await set_stored_month(now_month)
        except Exception as e:
            print(f"Auto-End Error: {e}")
        
        # Check every 1 hour
        await asyncio.sleep(3600)

# Start the background task
asyncio.create_task(check_season_end())

async def end_season_logic(auto=False):
    top = await get_leaderboard(3)
    if not top:
        return
        
    txt = f"🏁 **{smcp('Monthly Season Ended')}!** 🏁\n\n"
    for i, user in enumerate(top, 1):
        txt += f"👑 {i}. {user['name']} — {user['points']} {smcp('pts')}\n"
    
    txt += f"\n👉 {smcp('Check Proof Channel for rewards!')}"
    
    # Proof Button in Announcement
    btn = InlineKeyboardMarkup([[InlineKeyboardButton(text="🔎 CHECK PROOF", url=PROOF_LINK)]])
    
    await app.send_message(MAIN_GROUP_ID, txt, reply_markup=btn)
    
    # DMs to Winners
    for user in top:
        try:
            await app.send_message(user['user_id'], f"🎉 {smcp('Congratulations!')} You are in the Top 3!\nContact Admin for prizes.")
        except:
            pass

    await reset_leaderboard()
    await app.send_message(MAIN_GROUP_ID, f"🗑 **{smcp('Leaderboard Reset. New Season Starts Now!')}**")

# --- QUIZ SENDER ---
async def send_quiz(chat_id):
    if chat_id in QUIZ_STATE and QUIZ_STATE[chat_id]['active']:
        return

    question_data = await get_random_question()
    
    # Fallback question if DB is empty
    if not question_data:
        question_data = {
            "q": "Who is Naruto's son?",
            "o": ["Boruto", "Sarada", "Mitsuki", "Kawaki"],
            "a": "Boruto"
        }

    correct_ans = question_data['a']
    options = question_data['o']
    random.shuffle(options)

    keyboard = []
    for opt in options:
        keyboard.append([InlineKeyboardButton(text=opt, callback_data=f"qAns|{opt}")])

    txt = (
        f"🚨 **{smcp('Anime Quiz Event')}** 🚨\n\n"
        f"❓ **{smcp('Question')}:** {question_data['q']}\n\n"
        f"💰 **{smcp('Prize')}:** ₁₀-₂₀ {smcp('Points')}\n"
        f"⏳ **{smcp('Time')}:** ₃₀ {smcp('Seconds')}\n"
    )

    msg = await app.send_message(chat_id, txt, reply_markup=InlineKeyboardMarkup(keyboard))

    QUIZ_STATE[chat_id] = {
        "active": True,
        "answer": correct_ans,
        "attempts": [],
        "msg_id": msg.id
    }

    await asyncio.sleep(30)
    
    if chat_id in QUIZ_STATE and QUIZ_STATE[chat_id]['active']:
        QUIZ_STATE[chat_id]['active'] = False
        try:
            await msg.edit_text(
                f"🛑 **{smcp('Time Up')}!** 🛑\n\n"
                f"✅ {smcp('Correct Answer')}: **{correct_ans}**",
                reply_markup=None
            )
        except:
            pass

# --- CALLBACK: ANSWER HANDLER ---
@app.on_callback_query(filters.regex("qAns"))
async def check_answer(client, query: CallbackQuery):
    chat_id = query.message.chat.id
    user_id = query.from_user.id
    name = query.from_user.first_name
    selected = query.data.split("|")[1]

    if chat_id not in QUIZ_STATE or not QUIZ_STATE[chat_id]['active']:
        return await query.answer(smcp("Quiz Ended!"), show_alert=True)

    state = QUIZ_STATE[chat_id]

    # Anti-Cheat Message
    if user_id in state['attempts']:
        return await query.answer(smcp("You already used your only attempt!"), show_alert=True)

    state['attempts'].append(user_id)

    if selected == state['answer']:
        state['active'] = False
        points = random.randint(10, 20)
        await add_points(user_id, name, points)
        
        txt = (
            f"🎉 **{smcp('Winner Announcement')}** 🎉\n\n"
            f"👤 **{smcp('User')}:** {query.from_user.mention}\n"
            f"✅ **{smcp('Answer')}:** {selected}\n"
            f"📈 **{smcp('Points Won')}:** +{points}"
        )
        await query.message.edit_text(txt, reply_markup=None)
    else:
        # Wrong Answer Message
        await query.answer(smcp("Wrong Answer! You cannot answer again."), show_alert=True)

# --- COMMANDS (Main Group Only) ---

@app.on_message(filters.command(["top", "leaderboard", "rank"]) & filters.chat(MAIN_GROUP_ID) & ~BANNED_USERS)
async def show_lb(client, message):
    data = await get_leaderboard()
    prizes = await get_prize()
    
    txt = f"🏆 **{smcp('Monthly Leaderboard')}** 🏆\n\n"
    if not data:
        txt += smcp("No Data Found.")
    else:
        for i, user in enumerate(data, 1):
            txt += f"{i}. {user['name']} ➾ {user['points']} {smcp('pts')}\n"
    
    txt += f"\n🎁 **{smcp('Current Prizes')}:**\n{prizes}"
    
    # Proof Button
    btn = InlineKeyboardMarkup([[InlineKeyboardButton(text="🔎 CHECK PROOF", url=PROOF_LINK)]])
    await message.reply(txt, reply_markup=btn)

# --- ADMIN COMMANDS ---

@app.on_message(filters.command("addq") & filters.user(SUDOERS))
async def add_q_cmd(client, message):
    try:
        text = message.text.split(None, 1)[1]
        parts = [x.strip() for x in text.split("|")]
        if len(parts) != 6:
            return await message.reply("Usage: `/addq Quest | A | B | C | D | CorrectAnswer`")
        q, opts, ans = parts[0], parts[1:5], parts[5]
        if ans not in opts:
            return await message.reply("⚠️ The correct answer is not in the options!")
        await add_question(q, opts, ans)
        await message.reply(f"✅ **{smcp('Question Added')}!**")
    except:
        await message.reply("Error in format.")

@app.on_message(filters.command("setprize") & filters.user(SUDOERS))
async def set_p_cmd(client, message):
    try:
        text = message.text.split(None, 1)[1]
        await set_prize(smcp(text))
        await message.reply(f"✅ **{smcp('Prizes Updated')}!**")
    except:
        pass

# Manual End Season Command
@app.on_message(filters.command("endseason") & filters.user(SUDOERS))
async def manual_end_season(client, message):
    await end_season_logic(auto=False)
  
