import argparse
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv
from manifest import Manifest

from marsbots.platforms.discord.externals import init_llm
from marsbots.platforms.discord.models import MarsbotMetadata

UNLIKELY_PREFIX = ["438974983724798uyfsduhfksdhfjhksdbfhjgsdyfgsdygfusfd"]

load_dotenv()


class MarsBot(commands.Bot):
    def __init__(self, bot_id: str) -> None:
        self.bot_id = bot_id

        self.metadata = MarsbotMetadata(
            name=bot_id,
        )

        intents = discord.Intents.default()
        self.set_intents(intents)

        self.llm = Manifest(
            client_name="openai",
            client_connection=os.getenv("OPENAI_API_KEY"),
            max_tokens=200,
            temperature=1.0,
            stop_token="\n",
        )

        super().__init__(
            command_prefix=UNLIKELY_PREFIX,
            intents=intents,
        )

    def set_intents(self, intents: discord.Intents) -> None:
        intents.message_content = True
        intents.messages = True
        if self.metadata.intents:
            if "presence" in self.metadata.intents:
                intents.presences = True
            if "members" in self.metadata.intents:
                intents.members = True

    async def on_ready(self) -> None:
        print(f"Running {self.metadata.name}...")

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        await self.process_commands(message)


def start(
    bot_id: str,
) -> None:
    print("Launching bot....")
    bot = MarsBot(bot_id)
    bot.load_extension("cogs.tarot")
    bot.run(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MarsBot")
    parser.add_argument("bot_id", help="ID of bot to load from /bots directory")
    args = parser.parse_args()
    start(args.bot_id)
