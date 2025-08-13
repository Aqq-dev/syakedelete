import os
import asyncio
import threading
from flask import Flask
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

app = Flask(__name__)

@app.route("/")
def index():
    return "ok"

@app.route("/health")
def health():
    return "ok"

def run_flask():
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)

class ConfirmView(discord.ui.View):
    def __init__(self, author_id: int, *, timeout: float | None = 180):
        super().__init__(timeout=timeout)
        self.author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("実行者のみ操作できます。", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="はい", style=discord.ButtonStyle.danger, custom_id="confirm_yes")
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        try:
            await interaction.response.edit_message(view=self)
        except Exception:
            pass
        await interaction.followup.send("削除を開始します。", ephemeral=True)
        guild = interaction.guild
        await asyncio.sleep(1)
        channels = list(guild.channels)
        for ch in channels:
            try:
                await ch.delete(reason=f"/delete 実行者: {interaction.user}")
                await asyncio.sleep(0.3)
            except Exception:
                continue

    @discord.ui.button(label="いいえ", style=discord.ButtonStyle.secondary, custom_id="confirm_no")
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        try:
            await interaction.response.edit_message(content="キャンセルしました。", view=self)
        except Exception:
            await interaction.response.send_message("キャンセルしました。", ephemeral=True)

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.synced = False

    async def setup_hook(self):
        pass

    async def on_ready(self):
        if not self.synced:
            try:
                await self.tree.sync()
                self.synced = True
            except Exception:
                pass
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="/delete"))

bot = Bot()

@bot.tree.command(name="delete", description="サーバー内のチャンネルをすべて削除します")
@app_commands.default_permissions(administrator=True)
@app_commands.checks.has_permissions(administrator=True)
async def delete_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="最終判断", description="本当にすべてのチャンネルを削除しますか？")
    view = ConfirmView(author_id=interaction.user.id, timeout=180)
    await interaction.response.send_message(embed=embed, view=view)

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    bot.run(TOKEN)

if __name__ == "__main__":
    main()