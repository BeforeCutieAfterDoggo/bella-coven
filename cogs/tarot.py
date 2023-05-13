from enum import Enum
import io
import random
from typing import Optional
import aiohttp
import discord
from discord.ext import commands

from marsbots.platforms.discord.util import is_mentioned, replace_bot_mention, replace_mentions_with_usernames
from marsbots.util import generate_run_id

from . import prompts
from . import resources


class NextActions(Enum):
    NEXT_CARD = 1
    ADVICE_CARD = 2
    END_READING = 3


class NextActionButtonView(discord.ui.View):
    def __init__(self, *items, timeout=180):
        super().__init__(*items, timeout=timeout)
        self.selection = None

    @discord.ui.button(label="Next Card", style=discord.ButtonStyle.blurple)
    async def next_card(self, button, interaction):
        self.selection = NextActions.NEXT_CARD
        self.stop()
        await interaction.response.defer()

    # @discord.ui.button(label="Advice Card", style=discord.ButtonStyle.green)
    # async def advice_card(self, button, interaction):
    #     self.selection = NextActions.ADVICE_CARD
    #     self.stop()

    # @discord.ui.button(label="End Reading", style=discord.ButtonStyle.red)
    # async def end_reading(self, button, interaction):
    #     self.selection = NextActions.END_READING
    #     self.stop()


class TarotCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.active_major_deck = resources.BCAD_TAROT
        self.active_minor_deck = resources.BCAD_TAROT
        self.is_reading = False
        self.prefix_fns = [prompts.q1_prefix, prompts.q2_prefix, prompts.q3_prefix]

    @commands.Cog.listener("on_message")
    async def on_message(self, message: discord.Message) -> None:
        if is_mentioned(message, self.bot.user) and not message.author.bot:
            try:
                await self.get_reading(message)
            except Exception as e:
                ctx = await self.bot.get_context(message)
                await ctx.send("Something went wrong. :(")
                print(e)
                self.is_reading = False

    async def get_reading(self, message: discord.Message):
        if self.is_reading:
            await message.reply("I'm already doing a reading. Get in line :)")
            return

        self.is_reading = True
        reading_idx = 0
        question = self.message_preprocessor(message)
        ctx = await self.bot.get_context(message)
        prompt = f'{prompts.PREFIX} "{question}"'
        prompt += "\n\n---\n\n"
        for prefix_fn in self.prefix_fns:
            async with ctx.channel.typing():
                should_have_next_button = reading_idx < len(self.prefix_fns) - 1
                prompt, button_container = await self.get_partial_reading(
                    ctx, prompt, prefix_fn, should_have_next_button
                )
                reading_idx += 1
            if button_container:
                await button_container.wait()
                if button_container.selection is None:
                    await ctx.send(
                        "Okay, I see you've lost interest. I'll stop reading now."
                    )
                    self.is_reading = False
                    return
        self.is_reading = False

    async def get_partial_reading(
        self, ctx, prompt, prefix_fn, should_have_next_button
    ):
        card = self.pull_card()
        completion = prefix_fn(card)
        completion += self.bot.llm.run(
            prompt + completion, run_id=generate_run_id()
        )
        card_image = await self.get_card_image(card)
        button_container = NextActionButtonView() if should_have_next_button else None
        await ctx.send(completion, file=card_image, view=button_container)
        new_prompt = prompt + completion + "\n\n"
        return new_prompt, button_container

    def message_preprocessor(self, message: discord.Message) -> str:
        message_content = replace_bot_mention(message.content, only_first=True)
        message_content = replace_mentions_with_usernames(
            message_content, message.mentions
        )
        message_content = message_content.strip()
        return message_content

    def pull_card(self, major_prob: Optional[float] = None):
        if major_prob is None:
            tarot = resources.MAJOR_ARCANA + resources.MINOR_ARCANA
            return tarot[random.randint(0, len(tarot) - 1)]
        else:
            rand = random.random()
            if rand < major_prob:
                return resources.MAJOR_ARCANA[
                    random.randint(0, len(resources.MAJOR_ARCANA) - 1)
                ]
            else:
                return resources.MINOR_ARCANA[
                    random.randint(0, len(resources.MINOR_ARCANA) - 1)
                ]

    async def get_card_image(self, card_name):
        is_major = card_name in resources.MAJOR_ARCANA
        deck = self.active_major_deck if is_major else self.active_minor_deck
        image_url = f"{deck['base_url']}{deck['cards'][card_name]['fname']}"
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                if resp.status != 200:
                    raise Exception(f"Error getting image: {resp.status}")
                data = io.BytesIO(await resp.read())
                file = discord.File(data, f"{card_name}.png")
                return file


def setup(bot: commands.Bot) -> None:
    bot.add_cog(TarotCog(bot))
