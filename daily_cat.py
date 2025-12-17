import discord
import firebase_admin
from firebase_admin import credentials, firestore
import os
import random
import json

# 1. Setup Firebase
# We load the credentials from an Environment Variable (securely stored in GitHub)
cred_dict = json.loads(os.environ.get("FIREBASE_CREDENTIALS"))
cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()

# 2. Setup Discord Client
intents = discord.Intents.default()
client = discord.Client(intents=intents)

try:
    CHANNEL_ID = int(os.environ.get("DISCORD_CHANNEL_ID"))
except (TypeError, ValueError):
    print("Error: CHANNEL_ID is missing or not a number!")
    exit(1) # Stop the script if we don't have an ID

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    channel = client.get_channel(CHANNEL_ID)
    
    if channel:
        # Fetch from Firestore
        docs = db.collection(u'cat_pictures').stream()
        cat_list = [doc.to_dict() for doc in docs]
        
        if cat_list:
            random_cat = random.choice(cat_list)
            image_url = random_cat.get('url')
            if image_url:
                embed = discord.Embed(title="Hourly Cat Delivery! 😺", color=discord.Color.blue())
                embed.set_image(url=image_url)
                await channel.send(embed=embed)
                print("Cat sent!")
            else:
                print("Error: Document found but no URL.")
        else:
            print("No cats found in database.")
    else:
        print("Channel not found. Check the ID.")

    # CRITICAL: Stop the script so GitHub knows we are done
    await client.close() 

# Run the bot
client.run(os.environ.get("DISCORD_TOKEN"))
