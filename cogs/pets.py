import discord
from discord.ext import commands
import json
import os
import random
from datetime import datetime, timedelta

dfile = "data.json"  # Same as your economy system
TOKEN = os.getenv("DISCORD_TOKEN")

class Pets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ---------- Data Handling ----------
    def load_data(self):
        if os.path.getsize(dfile) == 0:
            with open(dfile, "w") as f:
                json.dump({}, f)
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
                "fish": "1970-01-01 00:00:00",
                "pet": None,  # store type: bird/cat/dog
                "pet_name": None,
                "last_play": "1970-01-01 00:00:00",
                "last_feed": "1970-01-01 00:00:00",
                "last_bathe": "1970-01-01 00:00:00"
            }
        else:
            # Make sure pet keys exist for old users
            for key in ["pet", "pet_name", "last_play", "last_feed", "last_bathe"]:
                if key not in data[user_id]:
                    if key.startswith("last_"):
                        data[user_id][key] = "1970-01-01 00:00:00"
                    else:
                        data[user_id][key] = None

        return data[user_id]

    # ---------- Cooldown helpers ----------
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

    # ---------- Commands ----------
    @commands.command()
    async def pets(self, ctx):
        """Show the pets you can adopt"""
        embed = discord.Embed(
            title="Available Pets 🐾",
            description="Here are the pets you can adopt and care for:",
            color=discord.Colour.purple()
        )

        pets_list = [
            "Bird 🐦",
            "Cat 🐱",
            "Dog 🐶"
        ]

        for pet in pets_list:
            embed.add_field(name=pet, value="\u200b", inline=False)

        embed.set_footer(text="Adopt a pet using: !adopt <pet> <name>")
        await ctx.send(embed=embed)

    @commands.command()
    async def adopt(self, ctx, pet_type: str, *, pet_name: str):
        """Adopt a pet: bird, cat, dog"""
        pet_type = pet_type.lower()
        if pet_type not in ["bird", "cat", "dog"]:
            await ctx.send("You can only adopt a bird, cat, or dog.")
            return

        data = self.load_data()
        user = self.get_user(data, ctx.author.id)

        if user["pet"] is not None:
            await ctx.send(f"You already have a pet: **{user['pet_name']}** the {user['pet']}.")
            return

        user["pet"] = pet_type
        user["pet_name"] = pet_name
        self.save_data(data)
        await ctx.send(f"🎉 You adopted a **{pet_type}** named **{pet_name}**!")

    @commands.command()
    async def feed(self, ctx):
        """Feed your pet (2h cooldown)"""
        data = self.load_data()
        user = self.get_user(data, ctx.author.id)

        if user["pet"] is None:
            await ctx.send("You don't have a pet yet! Adopt one with `!adopt <pet> <name>`")
            return

        cooldown = 2 * 3600  # 2 hours
        if not self.can_claim(user["last_feed"], cooldown):
            await ctx.send(f"You must wait {self.remaining(user['last_feed'], cooldown)} before feeding again.")
            return

        coins = random.randint(20, 50)
        user["money"] += coins
        user["last_feed"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self.save_data(data)

        await ctx.send(f"🍖 You fed **{user['pet_name']}** and earned **{coins} coins**!")

    @commands.command()
    async def bathe(self, ctx):
        """Bathe your pet (3h cooldown)"""
        data = self.load_data()
        user = self.get_user(data, ctx.author.id)

        if user["pet"] is None:
            await ctx.send("You don't have a pet yet! Adopt one with `!adopt <pet> <name>`")
            return

        cooldown = 3 * 3600  # 3 hours
        if not self.can_claim(user["last_bathe"], cooldown):
            await ctx.send(f"You must wait {self.remaining(user['last_bathe'], cooldown)} before bathing again.")
            return

        coins = random.randint(30, 70)
        user["money"] += coins
        user["last_bathe"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self.save_data(data)

        await ctx.send(f"🛁 You bathed **{user['pet_name']}** and earned **{coins} coins**!")

    @commands.command()
    async def play(self, ctx):
        """Play with your pet (10min cooldown)"""
        data = self.load_data()
        user = self.get_user(data, ctx.author.id)

        if user["pet"] is None:
            await ctx.send("You don't have a pet yet! Adopt one with `!adopt <pet> <name>`")
            return

        cooldown = 10 * 60  # 10 minutes
        if not self.can_claim(user["last_play"], cooldown):
            await ctx.send(f"You must wait {self.remaining(user['last_play'], cooldown)} before playing again.")
            return

        coins = random.randint(15, 40)
        user["money"] += coins
        user["last_play"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self.save_data(data)

        await ctx.send(f"🎾 You played with **{user['pet_name']}** and earned **{coins} coins**!")

    @commands.command()
    async def mypet(self, ctx):
        """View your pet and cooldowns"""
        data = self.load_data()
        user = self.get_user(data, ctx.author.id)

        if user["pet"] is None:
            await ctx.send("You don't have a pet yet! Adopt one with `!adopt <pet> <name>`")
            return

        # Cooldowns
        play_cd = 10 * 60
        feed_cd = 2 * 3600
        bathe_cd = 3 * 3600

        play_rem = "✅ Ready" if self.can_claim(user["last_play"], play_cd) else self.remaining(user["last_play"], play_cd)
        feed_rem = "✅ Ready" if self.can_claim(user["last_feed"], feed_cd) else self.remaining(user["last_feed"], feed_cd)
        bathe_rem = "✅ Ready" if self.can_claim(user["last_bathe"], bathe_cd) else self.remaining(user["last_bathe"], bathe_cd)

        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Pet",
            color=discord.Colour.green()
        )
        embed.add_field(name="Name", value=user["pet_name"])
        embed.add_field(name="Type", value=user["pet"])
        embed.add_field(name="Play cooldown", value=play_rem)
        embed.add_field(name="Feed cooldown", value=feed_rem)
        embed.add_field(name="Bathe cooldown", value=bathe_rem)

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Pets(bot))
