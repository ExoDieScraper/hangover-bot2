import discord
from discord.ext import commands
from datetime import datetime, timedelta
import json
import asyncio
import os
import random
from PIL import Image, ImageDraw, ImageFont
import io
import aiohttp

dfile = "data.json"
images = "./images"

class User(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # ---------- JSON helpers ----------
    def load_data(self):
        if not os.path.exists(dfile) or os.path.getsize(dfile) == 0:
            with open(dfile, "w") as f:
                json.dump({}, f)
            return {}
        with open(dfile, "r") as f:
            return json.load(f)

    def save_data(self, data):
        with open(dfile, "w") as f:
            json.dump(data, f, indent=4)

    def get_user(self, user_id):
        data = self.load_data()
        user_id = str(user_id)

        if user_id not in data:
            # First time user: initialize all fields
            data[user_id] = {
                "money": 0,
                "work": "1970-01-01 00:00:00",
                "daily": "1970-01-01 00:00:00",
                "weekly": "1970-01-01 00:00:00",
                "rob": "1970-01-01 00:00:00",
                "fish": "1970-01-01 00:00:00",
                "xp": 0,
                "level": 1,
                "profile_image": None,
                "owned_images": []
            }
            self.save_data(data)
        else:
            defaults = {
                "xp": 0,
                "level": 1,
                "profile_image": None,
                "owned_images": []
            }
            for key,value in defaults.items():
                if key not in data[user_id]:
                    data[user_id][key] = value
            self.save_data(data)
        return data[user_id]
    # ---------- Leveling helpers ----------
    def xp_to_next(self, level):
        """XP required for next level"""
        return 100 * (level ** 2)

    def add_xp(self, user_data, amount):
        """Add XP, handle level-ups and coin rewards"""
        user_data["xp"] += amount
        leveled_up = False
        coins_rewarded = 0

        while user_data["xp"] >= self.xp_to_next(user_data["level"]):
            user_data["xp"] -= self.xp_to_next(user_data["level"])
            user_data["level"] += 1
            leveled_up = True

            # Reward coins for leveling up
            reward = 50 * user_data["level"]
            user_data["money"] += reward
            coins_rewarded += reward

        return leveled_up, coins_rewarded

    # ---------- Buy preset profile image ----------
    @commands.command()
    async def buy_image(self, ctx, image_name: str):
        user_data = self.get_user(ctx.author.id)
        data = self.load_data()

        matching_files = [f for f in os.listdir(images) if f.lower().startswith(image_name.lower())]
        if not matching_files:
            await ctx.send("❌ This image does not exist.")
            return

        file_name = matching_files[0]

        if file_name in user_data["owned_images"]:
            await ctx.send("✅ You already own this image.")
            return

        price = 100
        if user_data.get("money", 0) < price:
            await ctx.send(f"❌ You need {price} coins to buy this image.")
            return

        user_data["money"] -= price
        user_data["owned_images"].append(file_name)
        data[str(ctx.author.id)] = user_data
        self.save_data(data)

        await ctx.send(f"🎉 You bought **{file_name}**! Set it with `!set_image {image_name}`")

    # ---------- Set profile image ----------
    @commands.command()
    async def set_image(self, ctx, image_name: str):
        user_data = self.get_user(ctx.author.id)
        data = self.load_data()

        matching_files = [f for f in user_data.get("owned_images", []) if f.lower().startswith(image_name.lower())]
        if not matching_files:
            await ctx.send("❌ You do not own this image. Buy it first with `!buy_image`.")
            return

        file_name = matching_files[0]
        user_data["profile_image"] = file_name
        data[str(ctx.author.id)] = user_data
        self.save_data(data)
        await ctx.send(f"✅ Your profile image has been set to **{file_name}**!")

    # ---------- Profile card command ----------
    @commands.command()
    async def profile(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author

        user_data = self.get_user(member.id)
        profile_image_name = user_data.get("profile_image")

        # If no custom image, fallback to regular embed
        if not profile_image_name or not os.path.exists(os.path.join(images, profile_image_name)):
            embed = discord.Embed(colour=member.colour)
            embed.set_author(name=member.name, icon_url=member.display_avatar.url)
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="Name", value=member.name, inline=False)
            embed.add_field(name="ID", value=member.id, inline=False)
            embed.add_field(name="Account Created", value=str(member.created_at).split(".")[0], inline=False)
            embed.add_field(name="Server Join Date", value=str(member.joined_at).split(".")[0], inline=False)
            embed.add_field(name="Coins", value=user_data.get("money", 0), inline=False)
            embed.add_field(name="Level", value=user_data.get("level", 1))
            embed.add_field(name="XP", value=f"{user_data.get('xp',0)}/{self.xp_to_next(user_data.get('level',1))}")
            await ctx.send(embed=embed)
            return
        # ---------- Generate profile card ----------
        base = Image.open(os.path.join(images, profile_image_name)).convert("RGBA")
        base = base.resize((600, 300))  # fixed card size

        draw = ImageDraw.Draw(base)

        # Font setup
        font_path = "arial.ttf"  # make sure you have this or any ttf font
        font_bold = ImageFont.truetype(font_path, 28)
        font_regular = ImageFont.truetype(font_path, 22)

        # Draw user info text
        draw.text((20, 20), f"{member.name}", fill="white", font=font_bold)
        draw.text((20, 60), f"Level: {user_data.get('level',1)}", fill="white", font=font_regular)
        draw.text((20, 90), f"Coins: {user_data.get('money',0)}", fill="white", font=font_regular)
        draw.text((20, 120), f"Joined: {str(member.joined_at).split('.')[0]}", fill="white", font=font_regular)

        # Draw XP bar
        xp = user_data.get("xp",0)
        level = user_data.get("level",1)
        xp_next = self.xp_to_next(level)
        bar_width = 400
        bar_height = 25
        bar_x = 20
        bar_y = 160

        # Background bar
        draw.rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + bar_height], fill=(100,100,100,255))
        # Filled XP
        fill_width = int((xp / xp_next) * bar_width)
        draw.rectangle([bar_x, bar_y, bar_x + fill_width, bar_y + bar_height], fill=(0,255,0,255))
        draw.text((bar_x + bar_width + 10, bar_y), f"{xp}/{xp_next} XP", fill="white", font=font_regular)

        # Draw user avatar
        avatar_bytes = await member.display_avatar.read()
        avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
        avatar_img = avatar_img.resize((100,100))
        # Circle crop avatar
        mask = Image.new("L", (100,100), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0,0,100,100), fill=255)
        base.paste(avatar_img, (480,20), mask)

        # Save to bytes
        with io.BytesIO() as image_binary:
            base.save(image_binary, "PNG")
            image_binary.seek(0)
            await ctx.send(file=discord.File(fp=image_binary, filename="profile.png"))
    # ---------- List available preset images ----------
    @commands.command()
    async def images(self, ctx):
        """Show all available preset profile images"""
        if not os.path.exists(images):
            await ctx.send("No preset images folder found.")
            return

        image_files = [f for f in os.listdir(images) if os.path.isfile(os.path.join(images, f))]
        if not image_files:
            await ctx.send("No preset images available.")
            return

        embed = discord.Embed(title="Available Profile Images", color=discord.Colour.purple())
        # Show filenames as code so users know what to buy
        embed.description = "\n".join([f"`{f}`" for f in image_files])
        embed.set_footer(text="Buy an image with !buy_image <name>")

        # Only the first image can be shown in embed preview
        embed.set_image(url=f"attachment://{image_files[0]}")

        # Prepare all files as attachments
        files = [discord.File(os.path.join(images, f)) for f in image_files]

        await ctx.send(embed=embed, files=files)

    # ---------- XP from messages ----------
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return  # Ignore bots

        user_data = self.get_user(message.author.id)
        data = self.load_data()

        # Check 1-minute cooldown
        last_xp_time = datetime.strptime(user_data.get("last_xp", "1970-01-01 00:00:00"), "%Y-%m-%d %H:%M:%S")
        if datetime.utcnow() >= last_xp_time + timedelta(minutes=1):
            # Give random XP
            xp_gain = random.randint(5, 10)
            leveled_up, coins_rewarded = self.add_xp(user_data, xp_gain)

            # Update last XP timestamp
            user_data["last_xp"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            data[str(message.author.id)] = user_data
            self.save_data(data)

            # Optional: notify channel of level-up
            if leveled_up:
                await message.channel.send(
                    f"🎉 {message.author.mention} leveled up to **{user_data['level']}**! "
                    f"You earned **{coins_rewarded} coins**!"
                )


async def setup(bot):
    await bot.add_cog(User(bot))
