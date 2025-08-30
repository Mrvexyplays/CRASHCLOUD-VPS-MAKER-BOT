import logging
import subprocess
import sys
import os
import re
import time
import random
import discord
from discord.ext import commands
from discord import app_commands

# Bot token यहाँ डालें
TOKEN = ""

# RAM लिमिट (example)
RAM_LIMIT = "2g"

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# सिर्फ एडमिन के लिए चेक
def is_admin():
    async def predicate(ctx):
        return ctx.author.guild_permissions.administrator
    return commands.check(predicate)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Sync error: {e}")

# Simple ping command
@bot.tree.command(name="ping", description="Check if bot is alive")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong! Bot is running.")

# Deploy command (Admin only)
@bot.tree.command(name="deploy", description="Deploy VPS (Admin Only)")
@is_admin()
async def deploy(interaction: discord.Interaction):
    await interaction.response.defer()  # thinking...
    try:
        # Example deploy command
        cmd = [
            "docker", "run", "--rm",
            f"--memory={RAM_LIMIT}",
            "ubuntu:22.04", "echo", "VPS Deployed ✅"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            await interaction.followup.send(f"✅ VPS Deployed Successfully!\n```{result.stdout}```")
        else:
            await interaction.followup.send(f"❌ Error deploying VPS\n```{result.stderr}```")
    except Exception as e:
        await interaction.followup.send(f"⚠️ Exception: {e}")

# Run bot
bot.run(TOKEN)
