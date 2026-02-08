from pyrogram import filters
from pyrogram.types import Message
from RessoMusic import app
from RessoMusic.utils.waifu_db import get_waifu_user, transfer_coins

@app.on_message(filters.command(["balance", "coins", "bal"]))
async def check_balance(_, message: Message):
    user_id = message.from_user.id
    user_data = await get_waifu_user(user_id)
    coins = user_data.get("coins", 0)
    
    await message.reply_text(f"💰 **ʏᴏᴜʀ ʙᴀʟᴀɴᴄᴇ:** `{coins}` ᴄᴏɪɴs")

@app.on_message(filters.command(["pay", "give"]))
async def pay_coins(_, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("⚠️ **ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴛᴏ ᴘᴀʏ!**")
        
    try:
        amount = int(message.text.split()[1])
    except:
        return await message.reply_text("⚠️ **ᴜsᴀɢᴇ:** `/pay 100`")
        
    sender_id = message.from_user.id
    receiver_id = message.reply_to_message.from_user.id
    
    if sender_id == receiver_id:
        return await message.reply_text("⚠️ **ʏᴏᴜ ᴄᴀɴ'ᴛ ᴘᴀʏ ʏᴏᴜʀsᴇʟғ!**")
        
    # Transfer Function Call
    sent_amount = await transfer_coins(sender_id, receiver_id, amount)
    
    if sent_amount > 0:
        await message.reply_text(f"✅ **sᴜᴄᴄᴇssғᴜʟʟʏ sᴇɴᴛ** `{sent_amount}` **ᴄᴏɪɴs!**")
    else:
        await message.reply_text("❌ **ɪɴsᴜғғɪᴄɪᴇɴᴛ ғᴜɴᴅs!**")
      
