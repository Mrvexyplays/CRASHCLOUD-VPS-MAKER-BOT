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

# Bot Token डालें
TOKEN = ""

# RAM Limit Example
RAM_LIMIT = "2g"

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# सिर्फ Admin Allow करने का check
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
        print(f"❌ Sync error: {e}")

# Normal Ping Command
@bot.tree.command(name="ping", description="Check if bot is alive")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong! Bot is alive!")

# Deploy Command (Admin Only)
@bot.tree.command(name="deploy", description="Deploy VPS (Admin Only)")
@is_admin()
async def deploy(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        # Example: Docker command (आप अपनी VPS deploy command डाल सकते हैं)
        cmd = [
            "docker", "run", "--rm",
            f"--memory={RAM_LIMIT}",
            "ubuntu:22.04", "echo", "VPS Deployed ✅"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            await interaction.followup.send(
                f"✅ VPS Deployed Successfully!\n```{result.stdout}```"
            )
        else:
            await interaction.followup.send(
                f"❌ Error deploying VPS\n```{result.stderr}```"
            )
    except Exception as e:
        await interaction.followup.send(f"⚠️ Exception: {e}")

# Run Bot
bot.run(TOKEN)  return

    await remove_everything_task(interaction)
    await interaction.response.send_message(embed=discord.Embed(description="### All user VPS instances have been terminated.", color=0x00ff00))

def add_to_database(userid, container_name, ssh_command):
    with open(database_file, 'a') as f:
        f.write(f"{userid}|{container_name}|{ssh_command}\n")

def remove_from_database(ssh_command):
    if not os.path.exists(database_file):
        return
    with open(database_file, 'r') as f:
        lines = f.readlines()
    with open(database_file, 'w') as f:
        for line in lines:
            if ssh_command not in line:
                f.write(line)

async def capture_ssh_session_line(process):
    while True:
        output = await process.stdout.readline()
        if not output:
            break
        output = output.decode('utf-8').strip()
        if "ssh session:" in output:
            return output.split("ssh session:")[1].strip()
    return None

whitelist_ids = {"1128161197766746213"}  # Replace with actual user IDs

@bot.tree.command(name="remove-everything", description="Removes all data and containers")
async def remove_everything(interaction: discord.Interaction):
    userid = str(interaction.user.id)
    if userid not in whitelist_ids:
        await interaction.response.send_message(embed=discord.Embed(description="You do not have permission to use this command.", color=0xff0000))
        return

    # Remove all Docker containers
    try:
        subprocess.run("docker rm -f $(sudo docker ps -a -q)", shell=True, check=True)
        await interaction.response.send_message(embed=discord.Embed(description="All Docker containers have been removed.", color=0x00ff00))
    except subprocess.CalledProcessError as e:
        await interaction.response.send_message(embed=discord.Embed(description="Failed to remove Docker containers.", color=0xff0000))

    # Remove database and port files
    try:
        os.remove(database_file)
        os.remove(port_db_file)
        await interaction.response.send_message(embed=discord.Embed(description="Database and port files have been cleared. Service has been restarted. Please start the bot in the shell", color=0x00ff00))
        subprocess.run("pkill pytho*", shell=True, check=True)
    except Exception as e:
        await interaction.response.send_message(embed=discord.Embed(description=f"Failed to clear database or restart service: {str(e)}", color=0xff0000))

#@tasks.loop(seconds=5)
#async def change_status():
#    try:
#        if os.path.exists(database_file):
#            with open(database_file, 'r') as f:
#                lines = f.readlines()
#                instance_count = len(lines)
#        else:
#            instance_count = 0
#
#        status = f"with {instance_count} Cloud Instances"
#        await bot.change_presence(activity=discord.Game(name=status))
#    except Exception as e:
#        print(f"Failed to update status: {e}")

def get_ssh_command_from_database(container_id):
    if not os.path.exists(database_file):
        return None
    with open(database_file, 'r') as f:
        for line in f:
            if container_id in line:
                return line.split('|')[2]
    return None

def get_user_servers(user):
    if not os.path.exists(database_file):
        return []
    servers = []
    with open(database_file, 'r') as f:
        for line in f:
            if line.startswith(user):
                servers.append(line.strip())
    return servers

def count_user_servers(userid):
    return len(get_user_servers(userid))

def get_container_id_from_database(userid):
    servers = get_user_servers(userid)
    if servers:
        return servers[0].split('|')[1]
    return None

@bot.event
async def on_ready():
    #change_status.start()
    print(f'Bot is ready. Logged in as {bot.user}')
    await bot.tree.sync()

async def regen_ssh_command(interaction: discord.Interaction, container_name: str):
#    await interaction.response.defer()
    user = str(interaction.user)
    container_id = get_container_id_from_database(user, container_name)

    if not container_id:
        await interaction.response.send_message(embed=discord.Embed(description="### No active instance found for your user.", color=0xff0000))
        return

    try:
        exec_cmd = await asyncio.create_subprocess_exec("docker", "exec", container_id, "tmate", "-F",
                                                        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        await interaction.response.send_message(embed=discord.Embed(description=f"Error executing tmate in Docker container: {e}", color=0xff0000))
        return

    ssh_session_line = await capture_ssh_session_line(exec_cmd)
    if ssh_session_line:
        await interaction.user.send(embed=discord.Embed(description=f"### New SSH Session Command: ```{ssh_session_line}```", color=0x00ff00))
        await interaction.response.send_message(embed=discord.Embed(description="### New SSH session generated. Check your DMs for details.", color=0x00ff00))
    else:
        await interaction.response.send_message(embed=discord.Embed(description="### Failed to generate new SSH session.", color=0xff0000))

async def start_server(interaction: discord.Interaction, container_name: str):
#    await interaction.response.defer()
    userid = str(interaction.user.id)
    container_id = get_container_id_from_database(user, container_name)

    if not container_id:
        await interaction.response.send_message(embed=discord.Embed(description="### No instance found for your user.", color=0xff0000))
        return

    try:
        subprocess.run(["docker", "start", container_id], check=True)
        exec_cmd = await asyncio.create_subprocess_exec("docker", "exec", container_id, "tmate", "-F",
                                                        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        ssh_session_line = await capture_ssh_session_line(exec_cmd)
        if ssh_session_line:
            await interaction.user.send(embed=discord.Embed(description=f"### Instance Started\nSSH Session Command: ```{ssh_session_line}```", color=0x00ff00))
            await interaction.response.send_message(embed=discord.Embed(description="### Instance started successfully. Check your DMs for details.", color=0x00ff00))
        else:
            await interaction.response.send_message(embed=discord.Embed(description="### Instance started, but failed to get SSH session line.", color=0xff0000))
    except subprocess.CalledProcessError as e:
        await interaction.response.send_message(embed=discord.Embed(description=f"Error starting instance: {e}", color=0xff0000))

async def stop_server(interaction: discord.Interaction, container_name: str):
#    await interaction.response.defer()
    userid = str(interaction.user.id)
    container_id = get_container_id_from_database(user, container_name)

    if not container_id:
        await interaction.response.send_message(embed=discord.Embed(description="### No instance found for your user.", color=0xff0000))
        return

    try:
        subprocess.run(["docker", "stop", container_id], check=True)
        await interaction.response.send_message(embed=discord.Embed(description="### Instance stopped successfully.", color=0x00ff00))
    except subprocess.CalledProcessError as e:
        await interaction.response.send_message(embed=discord.Embed(description=f"### Error stopping instance: {e}", color=0xff0000))

async def restart_server(interaction: discord.Interaction, container_name: str):
#    await interaction.response.defer()
    userid = str(interaction.user.id)
    container_id = get_container_id_from_database(userid, container_name)

    if not container_id:
        await interaction.response.send_message(embed=discord.Embed(description="### No instance found for your user.", color=0xff0000))
        return

    try:
        subprocess.run(["docker", "restart", container_id], check=True)
        exec_cmd = await asyncio.create_subprocess_exec("docker", "exec", container_id, "tmate", "-F",
                                                        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        ssh_session_line = await capture_ssh_session_line(exec_cmd)
        if ssh_session_line:
            await interaction.user.send(embed=discord.Embed(description=f"### Instance Restarted\nSSH Session Command: ```{ssh_session_line}```\nOS: Ubuntu 22.04", color=0x00ff00))
            await interaction.response.send_message(embed=discord.Embed(description="### Instance restarted successfully. Check your DMs for details.", color=0x00ff00))
        else:
            await interaction.response.send_message(embed=discord.Embed(description="### Instance restarted, but failed to get SSH session line.", color=0xff0000))
    except subprocess.CalledProcessError as e:
        await interaction.response.send_message(embed=discord.Embed(description=f"Error restarting instance: {e}", color=0xff0000))

def get_container_id_from_database(userid, container_name):
    if not os.path.exists(database_file):
        return None
    with open(database_file, 'r') as f:
        for line in f:
            if line.startswith(userid) and container_name in line:
                return line.split('|')[1]
    return None

def generate_random_port():
    return random.randint(1025, 65535)

async def create_server_task(interaction):
    await interaction.response.send_message(embed=discord.Embed(description="### Creating Instance, This takes a few seconds. Powered by [CrashOfGuys](<https://discord.com/invite/VWm8zUEQN8>)", color=0x00ff00))
    userid = str(interaction.user.id)
    if count_user_servers(userid) >= SERVER_LIMIT:
        await interaction.followup.send(embed=discord.Embed(description="```Error: Instance Limit-reached```", color=0xff0000))
        return

    image = "ubuntu-22.04-with-tmate"

    try:
        container_id = subprocess.check_output([
           "docker", "run", "-itd", "--privileged", "--hostname", "crashcloud", "--cap-add=ALL", image
        ]).strip().decode('utf-8')
    except subprocess.CalledProcessError as e:
        await interaction.followup.send(embed=discord.Embed(description=f"### Error creating Docker container: {e}", color=0xff0000))
        return

    try:
        exec_cmd = await asyncio.create_subprocess_exec("docker", "exec", container_id, "tmate", "-F",
                                                        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        await interaction.followup.send(embed=discord.Embed(description=f"### Error executing tmate in Docker container: {e}", color=0xff0000))
        subprocess.run(["docker", "kill", container_id])
        subprocess.run(["docker", "rm", container_id])
        return

    ssh_session_line = await capture_ssh_session_line(exec_cmd)
    if ssh_session_line:
        await interaction.user.send(embed=discord.Embed(description=f"### Successfully created Instance\nSSH Session Command: ```{ssh_session_line}```\nOS: Ubuntu 22.04\nPassword: root", color=0x00ff00))
        add_to_database(userid, container_id, ssh_session_line)
        await interaction.followup.send(embed=discord.Embed(description="### Instance created successfully. Check your DMs for details.", color=0x00ff00))
    else:
        await interaction.followup.send(embed=discord.Embed(description="### Something went wrong or the Instance is taking longer than expected. If this problem continues, Contact Support.", color=0xff0000))
        subprocess.run(["docker", "kill", container_id])
        subprocess.run(["docker", "rm", container_id])

@bot.tree.command(name="deploy", description="Creates a new Instance with Ubuntu 22.04")
async def deploy_ubuntu(interaction: discord.Interaction):
    await create_server_task(interaction)

#@bot.tree.command(name="deploy-debian", description="Creates a new Instance with Debian 12")
#async def deploy_ubuntu(interaction: discord.Interaction):
#    await create_server_task_debian(interaction)

@bot.tree.command(name="regen-ssh", description="Generates a new SSH session for your instance")
@app_commands.describe(container_name="The name/ssh-command of your Instance")
async def regen_ssh(interaction: discord.Interaction, container_name: str):
    await regen_ssh_command(interaction, container_name)

@bot.tree.command(name="start", description="Starts your instance")
@app_commands.describe(container_name="The name/ssh-command of your Instance")
async def start(interaction: discord.Interaction, container_name: str):
    await start_server(interaction, container_name)

@bot.tree.command(name="stop", description="Stops your instance")
@app_commands.describe(container_name="The name/ssh-command of your Instance")
async def stop(interaction: discord.Interaction, container_name: str):
    await stop_server(interaction, container_name)

@bot.tree.command(name="restart", description="Restarts your instance")
@app_commands.describe(container_name="The name/ssh-command of your Instance")
async def restart(interaction: discord.Interaction, container_name: str):
    await restart_server(interaction, container_name)

@bot.tree.command(name="ping", description="Check the bot's latency.")
async def ping(interaction: discord.Interaction):
    await interaction.response.defer()
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Latency: {latency}ms",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="list", description="Lists all your Instances")
async def list_servers(interaction: discord.Interaction):
    await interaction.response.defer()
    userid = str(interaction.user.id)
    servers = get_user_servers(userid)
    if servers:
        embed = discord.Embed(title="Your Instances", color=0x00ff00)
        for server in servers:
            _, container_name, _ = server.split('|')
            embed.add_field(name=container_name, value="32GB RAM - Premuim - 4 cores", inline=False)
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send(embed=discord.Embed(description="You have no servers.", color=0xff0000))

async def execute_command(command):
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return stdout.decode(), stderr.decode()

PUBLIC_IP = '138.68.79.95'

async def capture_output(process, keyword):
    while True:
        output = await process.stdout.readline()
        if not output:
            break
        output = output.decode('utf-8').strip()
        if keyword in output:
            return output
    return None

@bot.tree.command(name="port-add", description="Adds a port forwarding rule")
@app_commands.describe(container_name="The name of the container", container_port="The port in the container")
async def port_add(interaction: discord.Interaction, container_name: str, container_port: int):
#    await interaction.response.defer()
    await interaction.response.send_message(embed=discord.Embed(description="### Setting up port forwarding. This might take a moment...", color=0x00ff00))

    public_port = generate_random_port()

    # Set up port forwarding inside the container
    command = f"ssh -o StrictHostKeyChecking=no -R {public_port}:localhost:{container_port} serveo.net -N -f"

    try:
        # Run the command in the background using Docker exec
        await asyncio.create_subprocess_exec(
            "docker", "exec", container_name, "bash", "-c", command,
            stdout=asyncio.subprocess.DEVNULL,  # No need to capture output
            stderr=asyncio.subprocess.DEVNULL  # No need to capture errors
        )

        # Respond immediately with the port and public IP
        await interaction.followup.send(embed=discord.Embed(description=f"### Port added successfully. Your service is hosted on {PUBLIC_IP}:{public_port}.", color=0x00ff00))

    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(description=f"### An unexpected error occurred: {e}", color=0xff0000))

@bot.tree.command(name="port-http", description="Forward HTTP traffic to your container")
@app_commands.describe(container_name="The name of your container", container_port="The port inside the container to forward")
async def port_forward_website(interaction: discord.Interaction, container_name: str, container_port: int):
 #   await interaction.response.defer()
    try:
        exec_cmd = await asyncio.create_subprocess_exec(
            "docker", "exec", container_name, "ssh", "-o StrictHostKeyChecking=no", "-R", f"80:localhost:{container_port}", "serveo.net",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        url_line = await capture_output(exec_cmd, "Forwarding HTTP traffic from")
        if url_line:
            url = url_line.split(" ")[-1]
            await interaction.response.send_message(embed=discord.Embed(description=f"### Website forwarded successfully. Your website is accessible at {url}.", color=0x00ff00))
        else:
            await interaction.response.send_message(embed=discord.Embed(description="### Failed to capture forwarding URL.", color=0xff0000))
    except subprocess.CalledProcessError as e:
        await interaction.response.send_message(embed=discord.Embed(description=f"### Error executing website forwarding: {e}", color=0xff0000))

@bot.tree.command(name="remove", description="Removes an Instance")
@app_commands.describe(container_name="The name/ssh-command of your Instance")
async def remove_server(interaction: discord.Interaction, container_name: str):
    await interaction.response.defer()
    userid = str(interaction.user.id)
    container_id = get_container_id_from_database(userid, container_name)

    if not container_id:
        await interaction.response.send_message(embed=discord.Embed(description="### No Instance found for your user with that name.", color=0xff0000))
        return

    try:
        subprocess.run(["docker", "stop", container_id], check=True)
        subprocess.run(["docker", "rm", container_id], check=True)

        remove_from_database(container_id)

        await interaction.response.send_message(embed=discord.Embed(description=f"Instance '{container_name}' removed successfully.", color=0x00ff00))
    except subprocess.CalledProcessError as e:
        await interaction.response.send_message(embed=discord.Embed(description=f"Error removing instance: {e}", color=0xff0000))

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        # --- Row 1: Deploy ---
        self.add_item(discord.ui.Button(label="🚀 Deploy", style=discord.ButtonStyle.success, custom_id="deploy"))

        # --- Row 2: List / Node / Ping ---
        self.add_item(discord.ui.Button(label="📋 List", style=discord.ButtonStyle.primary, custom_id="list"))
        self.add_item(discord.ui.Button(label="🖥️ Node", style=discord.ButtonStyle.secondary, custom_id="node"))
        self.add_item(discord.ui.Button(label="🏓 Ping", style=discord.ButtonStyle.secondary, custom_id="ping"))

        # --- Row 3: Start / Stop / Restart / Regen / Remove ---
        self.add_item(discord.ui.Button(label="▶️ Start", style=discord.ButtonStyle.success, custom_id="start"))
        self.add_item(discord.ui.Button(label="⏹️ Stop", style=discord.ButtonStyle.danger, custom_id="stop"))
        self.add_item(discord.ui.Button(label="🔄 Restart", style=discord.ButtonStyle.primary, custom_id="restart"))
        self.add_item(discord.ui.Button(label="🔑 Regen SSH", style=discord.ButtonStyle.secondary, custom_id="regen"))
        self.add_item(discord.ui.Button(label="🗑️ Remove", style=discord.ButtonStyle.danger, custom_id="remove"))

        # --- Row 4: Ports ---
        self.add_item(discord.ui.Button(label="🔌 Port Add", style=discord.ButtonStyle.secondary, custom_id="portadd"))
        self.add_item(discord.ui.Button(label="🌐 HTTP Forward", style=discord.ButtonStyle.secondary, custom_id="http"))

        # --- Row 5: Credits ---
        self.add_item(discord.ui.Button(label="💰 Balance", style=discord.ButtonStyle.secondary, custom_id="bal"))
        self.add_item(discord.ui.Button(label="🎯 Earn Credit", style=discord.ButtonStyle.secondary, custom_id="earn"))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        cid = interaction.data["custom_id"]

        if cid == "deploy":
            await create_server_task(interaction)
        elif cid == "list":
            await list_servers(interaction)
        elif cid == "node":
            await node_status(interaction)
        elif cid == "ping":
            await ping(interaction)
        elif cid == "start":
            await interaction.response.send_modal(ContainerActionModal("Start Instance", start_server))
        elif cid == "stop":
            await interaction.response.send_modal(ContainerActionModal("Stop Instance", stop_server))
        elif cid == "restart":
            await interaction.response.send_modal(ContainerActionModal("Restart Instance", restart_server))
        elif cid == "regen":
            await interaction.response.send_modal(ContainerActionModal("Regenerate SSH", regen_ssh_command))
        elif cid == "remove":
            await interaction.response.send_modal(ContainerActionModal("Remove Instance", remove_server))
        elif cid == "portadd":
            async def _action(i: discord.Interaction, name: str, port: int):
                await port_add(i, name, port)
            await interaction.response.send_modal(PortActionModal("Add Port Forward", _action))
        elif cid == "http":
            async def _action(i: discord.Interaction, name: str, port: int):
                await port_forward_website(i, name, port)
            await interaction.response.send_modal(PortActionModal("HTTP Forward", _action))
        elif cid == "bal":
            await bal(interaction)
        elif cid == "earn":
            await earncredit(interaction)

        return True


@bot.tree.command(name="help", description="Shows the help panel")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚡ Crash Cloud Help",
        description="Click the buttons below to use commands:",
        color=0x2ecc71
    )

    embed.add_field(
        name="🚀 Deploy",
        value="Click button to create a new server.\nWorks same as `/deploy`.",
        inline=False
    )
    embed.add_field(
        name="📋 List / 🖥️ Node / 🏓 Ping",
        value="Check your servers, node status, or test bot ping.",
        inline=False
    )
    embed.add_field(
        name="▶️ Start / ⏹️ Stop / 🔄 Restart / 🔑 Regen / 🗑️ Remove",
        value="Manage your instances with these actions.",
        inline=False
    )
    embed.add_field(
        name="🔌 Port / 🌐 HTTP Forward",
        value="Forward ports or expose HTTP sites.",
        inline=False
    )
    embed.add_field(
        name="💰 Balance / 🎯 Earn",
        value="Check credits and earn more.",
        inline=False
    )

    await interaction.response.send_message(embed=embed, view=HelpView())

# run the bot
bot.run(TOKEN)
