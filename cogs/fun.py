import discord
from discord.ext import commands
import random
import json
import os
from datetime import datetime, timedelta

dfile = "data.json"  # Same JSON as your work system

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ---------- Data Handling ----------
    def load_data(self):
        if os.path.getsize(dfile) == 0:
            with open(dfile,"w") as f:
                json.dump({},f)
            return {}
        with open(dfile, "r") as f:
            return json.load(f)

    def save_data(self, data):
        with open(dfile, "w") as f:
            json.dump(data, f, indent=4)

    def get_user(self, data, user_id):
        user_id = str(user_id)
        if user_id not in data:
            data[user_id] = {
                "money": 0,
                "work": "1970-01-01 00:00:00",
                "daily": "1970-01-01 00:00:00",
                "weekly": "1970-01-01 00:00:00",
                "rob": "1970-01-01 00:00:00",
                "fish": "1970-01-01 00:00:00"
            }
        else:
            if "fish" not in data[user_id]:
                data[user_id]["fish"] = "1970-01-01 00:00:00"
        return data[user_id]

    # ---------- Helper Functions ----------
    def can_claim(self, last_time, cooldown):
        last = datetime.strptime(last_time, "%Y-%m-%d %H:%M:%S")
        return datetime.utcnow() >= last + timedelta(seconds=cooldown)

    def remaining(self, last_time, cooldown):
        last = datetime.strptime(last_time, "%Y-%m-%d %H:%M:%S")
        remaining_time = (last + timedelta(seconds=cooldown)) - datetime.utcnow()
        total_seconds = int(remaining_time.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{hours}h {minutes}m"

    # ---------- Fishing Command ----------
    @commands.command()
    async def fish(self, ctx):
        data = self.load_data()
        user = self.get_user(data, ctx.author.id)

        cooldown = 20 * 60  # 20 minutes in seconds

        if not self.can_claim(user["fish"], cooldown):
            await ctx.send(f"🎣 You must wait {self.remaining(user['fish'], cooldown)} before fishing again.")
            return

        # Determine fish rarity
        roll = random.random()
        if roll <= 0.001:  # 0.1% extremely rare
            fish = "Extremely Rare Fish 🦑"
            coins = random.randint(500, 800)
        elif roll <= 0.011:  # 1% very rare
            fish = "Very Rare Fish 🐡"
            coins = random.randint(200, 400)
        elif roll <= 0.061:  # 5% rare
            fish = "Rare Fish 🐠"
            coins = random.randint(50, 100)
        else:  # common
            fish = "Common Fish 🐟"
            coins = random.randint(10, 25)

        user["money"] += coins
        user["fish"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self.save_data(data)

        await ctx.send(f"🎣 You caught a **{fish}** and earned **{coins} coins**!")

async def setup(bot):
    await bot.add_cog(Fun(bot))
