import discord
from discord.ext import commands, tasks
import firebase_admin
from firebase_admin import credentials, firestore
import random
import os

# 1. Initialize Firebase
cred = credentials.Certificate("path/to/your/service-account-key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# 2. Bot Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

CHANNEL_ID = 123456789012345678 # Replace with your Discord Channel ID

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    scheduled_cat_sender.start() # Start the loop

# 3. The Scheduled Task (Hourly)
@tasks.loop(hours=1)
async def scheduled_cat_sender():
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        # Fetch all cat docs
        docs = db.collection(u'cat_pictures').stream()
        cat_list = [doc.to_dict() for doc in docs]
        
        if cat_list:
            # Pick a random cat
            random_cat = random.choice(cat_list)
            image_url = random_cat.get('url')
            
            if image_url:
                await channel.send(f"Hourly Cat Delivery! 😺\n{image_url}")
            else:
                print("Found a doc but no URL.")
        else:
            print("No cats found in database :(")

# 4. Manual Command (Custom)
@bot.command()
async def cat(ctx):
    """Manually triggers a cat picture send"""
    docs = db.collection(u'cat_pictures').stream()
    cat_list = [doc.to_dict() for doc in docs]
    
    if cat_list:
        random_cat = random.choice(cat_list)
        await ctx.send(random_cat.get('url'))
    else:
        await ctx.send("No cats in the database yet! Upload some via the Android app.")

bot.run('YOUR_DISCORD_BOT_TOKEN')
