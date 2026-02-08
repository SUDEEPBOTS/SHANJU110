from RessoMusic.misc import mongodb

# Collection names in MongoDB
waifudb = mongodb.waifu_users

async def get_waifu_user(user_id: int):
    user = await waifudb.find_one({"user_id": user_id})
    if not user:
        # Default start: 10k coins aur khali collection
        return {"user_id": user_id, "coins": 10000, "collection": []}
    return user

async def add_coin(user_id: int, amount: int):
    await waifudb.update_one(
        {"user_id": user_id},
        {"$inc": {"coins": amount}},
        upsert=True
    )

async def add_waifu_to_db(user_id: int, waifu_data: dict):
    # Waifu data format: {name, rarity, hp, weapon, img_url}
    await waifudb.update_one(
        {"user_id": user_id},
        {"$push": {"collection": waifu_data}, "$setOnInsert": {"coins": 10000}},
        upsert=True
    )

async def check_waifu_in_collection(user_id: int, waifu_name: str):
    user = await get_waifu_user(user_id)
    for waifu in user.get("collection", []):
        if waifu["name"] == waifu_name:
            return True
    return False
  
