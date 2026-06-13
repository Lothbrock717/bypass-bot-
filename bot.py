import asyncio
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

async def bypass_link(url: str) -> str:
    headers = {"User-Agent": UA}
    async with httpx.AsyncClient(follow_redirects=True, headers=headers, timeout=30) as client:
        r = await client.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        link = soup.find("a", {"id": "get-link"})
        if link and link.get("href") and link["href"] != "javascript: void(0)":
            return link["href"]
        meta = soup.find("meta", attrs={"http-equiv": "refresh"})
        if meta:
            content = meta.get("content", "")
            if "url=" in content.lower():
                return content.split("url=")[-1]
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
            await msg.edit("❌ Could not bypass. Try again.")
    except Exception as e:
        await msg.edit(f"❌ Error: `{str(e)}`")

app.run()
