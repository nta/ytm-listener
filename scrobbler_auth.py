import pylast
import os
import time
from dotenv import load_dotenv

load_dotenv()

network = pylast.LastFMNetwork(os.getenv("LASTFM_API_KEY", ""), os.getenv("LASTFM_API_SECRET", ""))
skg = pylast.SessionKeyGenerator(network)
url = skg.get_web_auth_url()

print(f"Please authorize this script to access your account: {url}\n")

while True:
    try:
        session_key = skg.get_web_auth_session_key(url)
        break
    except pylast.WSError:
        time.sleep(1)

print("session key: " + session_key)