import os
import asyncio
import threading
from flask import Flask
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
PORT = int(os.getenv("PORT", 10000))

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True

app = Flask(__name__)

@app.route("/")
def index():
    return "ok"

@app.route("/health")
def health():
    return "ok"

def run_flask():
    app.run(host="0.0.0.0", port=PORT)

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")

@bot.command(name="delete")
@commands.has_permissions(administrator=True)
async def delete_all_channels(ctx):
    confirm_msg = await ctx.send(
        "本当にすべてのチャンネルを削除しますか？\nはいなら `はい`、キャンセルなら `いいえ` とチャットで入力してください。"
    )

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content in ["はい", "いいえ"]

    try:
        reply = await bot.wait_for("message", check=check, timeout=60)
    except asyncio.TimeoutError:
        await ctx.send("時間切れです。キャンセルしました。")
        return

    if reply.content == "いいえ":
        await ctx.send("キャンセルしました。")
        return

    await ctx.send("チャンネルの削除を開始します。")

    guild = ctx.guild
    channels = list(guild.channels)

    for ch in channels:
        try:
            await ch.delete(reason=f"!delete コマンド実行者: {ctx.author}")
            await asyncio.sleep(0.3)
        except Exception:
            continue

threading.Thread(target=run_flask, daemon=True).start()
bot.run(TOKEN)
