import discord
from discord.ext import commands
import random
import asyncio
import json
import os
from datetime import datetime, timedelta

dfile = "data.json"

class Work(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # -----------DATA-----------
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
        return data[user_id]

    def can_claim(self, last_time, cooldown):
        last = datetime.strptime(last_time, "%Y-%m-%d %H:%M:%S")
        return datetime.utcnow() >= last + timedelta(seconds=cooldown)

    def remaining(self, last_time, cooldown, show_days=False):
        last = datetime.strptime(last_time, "%Y-%m-%d %H:%M:%S")
        remaining = (last + timedelta(seconds=cooldown)) - datetime.utcnow()
        total_seconds = int(remaining.total_seconds())
        if show_days:
            days, remainder = divmod(total_seconds, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, _ = divmod(remainder, 60)
            return f"{days}d {hours}h {minutes}m"
        else:
            hours, remainder = divmod(total_seconds, 3600)
            minutes, _ = divmod(remainder, 60)

            return f"{hours}h {minutes}m"

    # -----------COMMANDS-----------

    @commands.command()
    async def work(self, ctx):
        data = self.load_data()
        user = self.get_user(data, ctx.author.id)

        if not self.can_claim(user["work"], 3600):
            await ctx.send(f"You must wait {self.remaining(user['work'], 3600)} before working again")
            return

        amount = random.randint(20,80)
        user["money"] += amount
        user["work"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        self.save_data(data)
        await ctx.send(f"You worked and earned **{amount} coins**")

    @commands.command()
    async def daily(self, ctx):
        data = self.load_data()
        user = self.get_user(data, ctx.author.id)

        if not self.can_claim(user["daily"], 86400):
            await ctx.send(f"You already claimed daily. Wait {self.remaining(user['daily'], 86400)}")
            return

        amount = random.randint(150, 300)
        user["money"] += amount
        user["daily"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        self.save_data(data)
        await ctx.send(f"Daily reward: **{amount} coins**")

    @commands.command()
    async def weekly(self, ctx):
        data = self.load_data()
        user = self.get_user(data, ctx.author.id)

        if not self.can_claim(user["weekly"], 604800):
            await ctx.send(f"You already claimed weekly. Wait {self.remaining(user['weekly'], 604800, show_days=True)}.")
            return

        amount = random.randint(800, 1500)
        user["money"] += amount
        user["weekly"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        self.save_data(data)
        await ctx.send(f"Weekly reward: **{amount} coins**")

    @commands.command(aliases=["bal"])
    async def balance(self, ctx):
        data = self.load_data()
        user = self.get_user(data, ctx.author.id)
        await ctx.send(f"You have **{user['money']} coins**")

    @commands.command(aliases=["lb","top"])
    async def leaderboard(self, ctx):
        data = self.load_data()
        guild_users = {
            uid: info["money"]
            for uid, info in data.items()
            if ctx.guild.get_member(int(uid)) is not None
        }

        if not guild_users:
            await ctx.send("No leaderboard data yet.")
            return

        sorted_users = sorted(guild_users.items(), key=lambda x: x[1], reverse=True)

        top_10 = sorted_users[:10]

        e = discord.Embed(
            title="Top 10 Richest",
            color=discord.Colour.gold()
        )
        lines = []
        medals = ["🥇","🥈","🥉"]

        for rank, (user_id, money) in enumerate(top_10, start=1):
            member = ctx.guild.get_member(int(user_id))
            name = member.display_name if member else f"User {uid}"

            prefix = medals[rank-1] if rank <= 3 else f"#{rank}"
            lines.append(f"{prefix} **{name}** - {money} coins")
        e.description = "\n".join(lines)
        await ctx.send(embed=e)

    @commands.command()
    async def rob(self, ctx, target: discord.Member = None):
        data = self.load_data()
        robber = self.get_user(data, ctx.author.id)

        # ---------- Cooldown check (30 min = 1800 sec) ----------
        if not self.can_claim(robber["rob"], 1800):
            await ctx.send(
                f"You must wait {self.remaining(robber['rob'], 1800)} before robbing again."
            )
            return

        # ---------- Pick random target ----------
        if target is None:
            possible_targets = []

            for uid, info in data.items():
                member = ctx.guild.get_member(int(uid))
                if (
                    member is not None
                    and member != ctx.author
                    and not member.bot
                    and info["money"] > 0
                ):
                    possible_targets.append(member)

            if not possible_targets:
                await ctx.send("No one to rob")
                return

            target = random.choice(possible_targets)

        # ---------- Checks ----------
        if target == ctx.author:
            await ctx.send("You can't rob yourself")
            return

        if target.bot:
            await ctx.send("You can't rob bots")
            return

        victim = self.get_user(data, target.id)

        if victim["money"] <= 0:
            await ctx.send(f"{target.display_name} has no money.")
            return

        # ---------- Set cooldown time ----------
        robber["rob"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        # ---------- 70% success ----------
        if random.random() < 0.7:
            percent = random.uniform(0.1, 0.4)
            amount = max(1, int(victim["money"] * percent))

            victim["money"] -= amount
            robber["money"] += amount

            self.save_data(data)

            await ctx.send(
                f"You robbed **{target.display_name}** and stole **{amount} coins**!"
            )

        else:
            fine = random.randint(5, 25)
            robber["money"] = max(0, robber["money"] - fine)

            self.save_data(data)

            await ctx.send(
                f"You got caught and paid **{fine} coins** in fines."
            )
    @commands.command()
    async def cd(self, ctx):
        data = self.load_data()
        user = self.get_user(data, ctx.author.id)

        commands_cd = {
            "Work": ("work", 3600),
            "Daily": ("daily", 86400),
            "Weekly": ("weekly", 604800),
            "Rob": ("rob", 1800),
            "Fish": ("fish", 1200)
        }

        embed = discord.Embed(
            title="⏳ Your Cooldowns",
            color=discord.Colour.blue()
        )

        for name, (key, cd) in commands_cd.items():
            if self.can_claim(user[key], cd):
                value = "✅ Ready"
            else:
                if name == "Weekly":
                    value = self.remaining(user[key], cd, show_days=True)
                else:
                    value = self.remaining(user[key], cd)

            embed.add_field(name=name, value=value, inline=False)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Work(bot))
