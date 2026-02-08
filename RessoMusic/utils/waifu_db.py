import random
from RessoMusic.misc import mongodb

# Collection names in MongoDB
waifudb = mongodb.waifu_users

# ==========================================
# 🔹 BASIC USER & COIN FUNCTIONS
# ==========================================

async def get_waifu_user(user_id: int):
    """User data lata hai, agar nahi hai to naya banata hai"""
    user = await waifudb.find_one({"user_id": user_id})
    if not user:
        return {"user_id": user_id, "coins": 10000, "collection": [], "married_to": None}
    return user

async def add_coin(user_id: int, amount: int):
    """Coins add ya subtract karta hai"""
    await waifudb.update_one(
        {"user_id": user_id},
        {"$inc": {"coins": amount}},
        upsert=True
    )

async def add_waifu_to_db(user_id: int, waifu_data: dict):
    """Waifu ko collection mein add karta hai"""
    await waifudb.update_one(
        {"user_id": user_id},
        {"$push": {"collection": waifu_data}, "$setOnInsert": {"coins": 10000}},
        upsert=True
    )

async def check_waifu_in_collection(user_id: int, waifu_name: str):
    """Check karta hai ki waifu pehle se hai ya nahi"""
    user = await get_waifu_user(user_id)
    for waifu in user.get("collection", []):
        if waifu["name"] == waifu_name:
            return True
    return False

# ==========================================
# 🔹 FIGHTING SYSTEM HELPERS
# ==========================================

async def get_random_waifu_from_user(user_id: int):
    """User ke collection se ek random waifu nikalta hai fight ke liye"""
    user = await get_waifu_user(user_id)
    collection = user.get("collection", [])
    if not collection:
        return None
    return random.choice(collection)

async def remove_waifu(user_id: int, waifu_name: str):
    """Waifu ko collection se delete karta hai"""
    await waifudb.update_one(
        {"user_id": user_id},
        {"$pull": {"collection": {"name": waifu_name}}}
    )

async def steal_waifu(loser_id: int, winner_id: int, waifu_data: dict):
    """Fight haarne wale se waifu nikal kar jeetne wale ko deta hai"""
    # 1. Loser se hatao
    await remove_waifu(loser_id, waifu_data["name"])
    # 2. Winner ko do
    await add_waifu_to_db(winner_id, waifu_data)

async def transfer_coins(from_user: int, to_user: int, amount: int):
    """Coins transfer karta hai (Agar waifu nahi chura paya toh)"""
    user = await get_waifu_user(from_user)
    if user["coins"] < amount:
        amount = user["coins"] # Jitna hai utna hi le lo
    
    if amount > 0:
        await waifudb.update_one({"user_id": from_user}, {"$inc": {"coins": -amount}})
        await waifudb.update_one({"user_id": to_user}, {"$inc": {"coins": amount}})
    return amount

# ==========================================
# 🔹 MARRIAGE, HEAL & TRADE HELPERS
# ==========================================

async def set_married_waifu(user_id: int, waifu_name: str):
    """User ki wife set karta hai"""
    await waifudb.update_one(
        {"user_id": user_id},
        {"$set": {"married_to": waifu_name}}
    )

async def heal_waifu_data(user_id: int, waifu_name: str):
    """Waifu ki HP badhata hai (+50)"""
    user = await get_waifu_user(user_id)
    collection = user.get("collection", [])
    
    target_waifu = None
    for w in collection:
        if w["name"] == waifu_name:
            target_waifu = w
            break
            
    if not target_waifu:
        return False
        
    # Old delete, New Add (MongoDB array update hack)
    await remove_waifu(user_id, waifu_name)
    target_waifu["hp"] += 50
    await add_waifu_to_db(user_id, target_waifu)
    return True

async def swap_waifus(user1_id, waifu1_name, user2_id, waifu2_name):
    """Trading ke liye waifus exchange karta hai"""
    u1 = await get_waifu_user(user1_id)
    u2 = await get_waifu_user(user2_id)
    
    w1_data = next((w for w in u1['collection'] if w['name'] == waifu1_name), None)
    w2_data = next((w for w in u2['collection'] if w['name'] == waifu2_name), None)
    
    if not w1_data or not w2_data:
        return False
        
    # Swap Execution
    await remove_waifu(user1_id, waifu1_name)
    await add_waifu_to_db(user1_id, w2_data)
    
    await remove_waifu(user2_id, waifu2_name)
    await add_waifu_to_db(user2_id, w1_data)
    
    return True
    
