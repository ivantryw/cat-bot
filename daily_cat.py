import discord
import firebase_admin
from firebase_admin import credentials, firestore
import os
import random
import json
import asyncio
import requests  # <--- Needed for the internet fallback

# --- CONFIGURATION ---
discord_token = os.environ.get("DISCORD_TOKEN")
channel_id_env = os.environ.get("DISCORD_CHANNEL_ID")
firebase_creds_json = os.environ.get("FIREBASE_CREDENTIALS")

if not all([discord_token, channel_id_env, firebase_creds_json]):
    print("Error: One or more Environment Variables are missing!")
    exit(1)

CHANNEL_ID = int(channel_id_env)

# --- FIREBASE SETUP ---
try:
    cred_dict = json.loads(firebase_creds_json)
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    print(f"Error initializing Firebase: {e}")
    exit(1)

# --- DISCORD SETUP ---
intents = discord.Intents.default()
intents.message_content = True 
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    
    try:
        channel = client.get_channel(CHANNEL_ID)
        
        if channel:
            # 1. Get all docs
            docs = db.collection(u'cat_pictures').stream()
            
            # 2. Filter for "Unused" images
            unused_cats = []
            for doc in docs:
                data = doc.to_dict()
                # Check if 'used' is missing OR false
                if not data.get('used', False): 
                    unused_cats.append(doc)

            if unused_cats:
                # --- SCENARIO A: PERSONAL UPLOAD FOUND ---
                print(f"Found {len(unused_cats)} unused personal images.")
                
                chosen_doc = random.choice(unused_cats)
                data = chosen_doc.to_dict()
                image_url = data.get('url')
                
                # Check for optional caption
                user_caption = data.get('caption')
                
                # Logic: Use caption if exists, otherwise default text
                if user_caption:
                    title_text = user_caption
                else:
                    title_text = "Fresh from the collection! 📸"

                if image_url:
                    embed = discord.Embed(title=title_text, color=discord.Color.green())
                    embed.set_image(url=image_url)
                    
                    if user_caption:
                        embed.set_footer(text="Uploaded from Android App")
                    
                    await channel.send(embed=embed)
                    print(f"Sent personal image: {image_url}")

                    # MARK AS USED so it doesn't send again
                    db.collection(u'cat_pictures').document(chosen_doc.id).update({u'used': True})
                else:
                    print("Error: Document existed but had no URL.")

            else:
                # --- SCENARIO B: FALLBACK TO INTERNET ---
                print("No unused personal images. Fetching from Internet...")
                
                try:
                    response = requests.get("https://api.thecatapi.com/v1/images/search")
                    if response.status_code == 200:
                        data = response.json()
                        fallback_url = data[0]['url']
                        
                        embed = discord.Embed(title="Internet Cat Delivery ☁️", color=discord.Color.orange())
                        embed.set_image(url=fallback_url)
                        embed.set_footer(text="Upload more photos to see your own cats!")
                        
                        await channel.send(embed=embed)
                        print("Sent internet fallback cat.")
                    else:
                        print(f"API Error: {response.status_code}")
                except Exception as e:
                    print(f"Fallback failed: {e}")
        else:
            print(f"Could not find channel {CHANNEL_ID}")
            
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        # CRITICAL FOR GITHUB ACTIONS:
        # We must close the connection so the script finishes and GitHub sees "Success"
        await client.close()

client.run(discord_token)
