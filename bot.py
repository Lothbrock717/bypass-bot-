import httpx
from bs4 import BeautifulSoup
from pyrogram import Client, filters
from pyrogram.types import Message
import os

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client("bypass_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"

async def bypass_link(url: str) -> dict:
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    async with httpx.AsyncClient(follow_redirects=True, headers=headers, timeout=30) as client:
        r = await client.get(url)
        
        debug = {
            "status": r.status_code,
            "final_url": str(r.url),
            "html_snippet": r.text[:300]
        }
        
        soup = BeautifulSoup(r.text, "html.parser")
        
        csrf_input = soup.find("input", {"name": "_csrfToken"})
        ad_input = soup.find("input", {"name": "ad_form_data"})
        
        debug["csrf_found"] = bool(csrf_input)
        debug["ad_form_found"] = bool(ad_input)
        
        if csrf_input and ad_input:
            csrf = csrf_input.get("value")
            ad_form_data = ad_input.get("value")
            
            post_headers = {
                "User-Agent": UA,
                "X-Requested-With": "XMLHttpRequest",
                "Referer": str(r.url),
                "Origin": "https://inshorturl.in",
            }
            data = {
                "_method": "POST",
                "_csrfToken": csrf,
                "ad_form_data": ad_form_data,
                "cf_turnstile_response": "test"
            }
            res = await client.post(
                "https://inshorturl.in/links/go",
                data=data,
                headers=post_headers
            )
            debug["post_status"] = res.status_code
            debug["post_response"] = res.text[:300]
        
        return debug

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply("**URL Bypass Bot** 🔗\n\nSend me any `inshorturl.in` link!")

@app.on_message(filters.text & filters.private)
async def handle_link(client, message: Message):
    text = message.text.strip()
    if "inshorturl.in" not in text:
        await message.reply("Please send a valid `inshorturl.in` link.")
        return
    msg = await message.reply("⏳ Debugging...")
    try:
        result = await bypass_link(text)
        debug_text = "\n".join([f"`{k}`: `{v}`" for k, v in result.items()])
        await msg.edit(f"**Debug Info:**\n\n{debug_text}")
    except Exception as e:
        await msg.edit(f"❌ Error: `{str(e)}`")

app.run()
