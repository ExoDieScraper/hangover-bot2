import discord
from discord.ext import commands
import random
import json
import os
from datetime import datetime

dfile = "data.json"

class Gambling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ---------- Helper Functions ----------
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
                "rob": "1970-01-01 00:00:00"
            }
        return data[user_id]

    # ---------- Gambling Commands ----------

    @commands.command(aliases=["cf"])
    async def coinflip(self, ctx, choice: str, bet: int):
        """Flip a coin. Choice: heads/tails"""
        data = self.load_data()
        user = self.get_user(data, ctx.author.id)

        if bet > user["money"]:
            await ctx.send("You don't have enough coins!")
            return

        choice = choice.lower()
        if choice not in ["heads", "tails"]:
            await ctx.send("Choose either 'heads' or 'tails'.")
            return

        result = random.choice(["heads", "tails"])
        if result == choice:
            user["money"] += bet
            await ctx.send(f"You won! The coin landed on **{result}**. You gained {bet} coins!")
        else:
            user["money"] -= bet
            await ctx.send(f"You lost! The coin landed on **{result}**. You lost {bet} coins!")

        self.save_data(data)

    @commands.command()
    async def slots(self, ctx, bet: int):
        """Play a simple 3-symbol slot machine"""
        data = self.load_data()
        user = self.get_user(data, ctx.author.id)

        if bet > user["money"]:
            await ctx.send("You don't have enough coins!")
            return

        symbols = ["🍒","🍋","🔔","⭐","💎"]
        result = [random.choice(symbols) for _ in range(3)]

        await ctx.send(" | ".join(result))

        # Check win conditions
        if result[0] == result[1] == result[2]:
            winnings = bet * 5
            user["money"] += winnings
            await ctx.send(f"Jackpot! You won {winnings} coins!")
        elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
            winnings = bet * 2
            user["money"] += winnings
            await ctx.send(f"Two in a row! You won {winnings} coins!")
        else:
            user["money"] -= bet
            await ctx.send(f"No match! You lost {bet} coins.")

        self.save_data(data)

    @commands.command()
    async def dice(self, ctx, bet: int):
        """Roll 3d6 against the bot"""
        data = self.load_data()
        user = self.get_user(data, ctx.author.id)

        if bet > user["money"]:
            await ctx.send("You don't have enough coins!")
            return

        user_rolls = [random.randint(1,6) for _ in range(3)]
        bot_rolls = [random.randint(1,6) for _ in range(3)]

        user_total = sum(user_rolls)
        bot_total = sum(bot_rolls)

        await ctx.send(f"You rolled: {user_rolls} (Total: {user_total})\nBot rolled: {bot_rolls} (Total: {bot_total})")

        if user_total > bot_total:
            user["money"] += bet
            await ctx.send(f"You win! You gained {bet} coins.")
        elif user_total < bot_total:
            user["money"] -= bet
            await ctx.send(f"You lose! You lost {bet} coins.")
        else:
            await ctx.send("It's a tie! No coins lost or gained.")

        self.save_data(data)

    @commands.command(aliases=["bj"])
    async def blackjack(self, ctx, bet: int):
        """Play an interactive blackjack against the bot"""
        data = self.load_data()
        user = self.get_user(data, ctx.author.id)

        if bet > user["money"]:
            await ctx.send("You don't have enough coins!")
            return

        def draw_card():
            return random.randint(1, 11)

        user_cards = [draw_card(), draw_card()]
        bot_cards = [draw_card(), draw_card()]

        user_total = sum(user_cards)
        bot_total = sum(bot_cards)

        # Send initial hand
        msg = await ctx.send(
            f"Your cards: {user_cards} (Total: {user_total})\n"
            f"Bot shows: [{bot_cards[0]}, ?]\n"
            "Type `hit` to draw another card or `stand` to hold."
        )

        # Interactive loop
        while user_total < 21:
            try:
                response = await self.bot.wait_for(
                    "message",
                    check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["hit", "stand"],
                    timeout=30.0  # 30 seconds to respond
                )
            except asyncio.TimeoutError:
                await ctx.send("Time's up! You automatically stand.")
                break

            if response.content.lower() == "hit":
                card = draw_card()
                user_cards.append(card)
                user_total = sum(user_cards)
                if user_total > 21:
                    await ctx.send(f"You drew {card}. Your total is {user_total} — busted!")
                    user["money"] -= bet
                    self.save_data(data)
                    return
                else:
                    await ctx.send(f"You drew {card}. Your total is now {user_total}. Type `hit` or `stand`.")
            else:  # stand
                await ctx.send(f"You stand with {user_total}.")
                break

        # Bot's turn (hit until 17 or higher)
        while bot_total < 17:
            bot_cards.append(draw_card())
            bot_total = sum(bot_cards)

        await ctx.send(f"Bot's cards: {bot_cards} (Total: {bot_total})")

        # Determine winner
        if bot_total > 21 or user_total > bot_total:
            user["money"] += bet
            await ctx.send(f"You win! You gained {bet} coins.")
        elif user_total < bot_total:
            user["money"] -= bet
            await ctx.send(f"You lose! You lost {bet} coins.")
        else:
            await ctx.send("It's a tie! No coins lost or gained.")

        self.save_data(data)

async def setup(bot):
    await bot.add_cog(Gambling(bot))
