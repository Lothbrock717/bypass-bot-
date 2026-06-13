import httpx
from bs4 import BeautifulSoup
from pyrogram import Client, filters
from pyrogram.types import Message
import os
import re

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client("bypass_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"

async def bypass_link(url: str) -> str:
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    async with httpx.AsyncClient(follow_redirects=True, headers=headers, timeout=30) as client:
        # Step 1: Get the page
        r = await client.get(url)
        soup = BeautifulSoup(r.text, "html.parser")

        # Step 2: Extract form data
        csrf = None
        ad_form_data = None

        csrf_input = soup.find("input", {"name": "_csrfToken"})
        if csrf_input:
            csrf = csrf_input.get("value")

        ad_input = soup.find("input", {"name": "ad_form_data"})
        if ad_input:
            ad_form_data = ad_input.get("value")

        if not csrf or not ad_form_data:
            return None

        # Step 3: POST to /links/go
        post_headers = {
            "User-Agent": UA,
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRF-Token": csrf,
            "Referer": str(r.url),
            "Origin": "https://inshorturl.in",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {
            "_method": "POST",
            "_csrfToken": csrf,
            "ad_form_data": ad_form_data,
            "cf_turnstile_response": "bypass_token"
        }

        res = await client.post(
            "https://inshorturl.in/links/go",
            data=data,
            headers=post_headers
        )

        try:
            json_res = res.json()
            if json_res.get("status") == "success":
                return json_res.get("url")
        except:
            pass

        return None

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply(
        "**URL Bypass Bot** 🔗\n\n"
        "Send me any `inshorturl.in` link and I'll bypass it!\n\n"
        "Just send the link directly."
    )

@app.on_message(filters.text & filters.private)
async def handle_link(client, message: Message):
    text = message.text.strip()
    if "inshorturl.in" not in text:
        await message.reply("Please send a valid `inshorturl.in` link.")
        return
    msg = await message.reply("⏳ Bypassing link, please wait...")
    try:
        result = await bypass_link(text)
        if result:
            await msg.edit(
                f"✅ **Bypassed Successfully!**\n\n"
                f"**Final Link:**\n`{result}`"
            )
        else:
            await msg.edit("❌ Could not bypass. Cloudflare Turnstile blocking.")
    except Exception as e:
        await msg.edit(f"❌ Error: `{str(e)}`")

app.run()
