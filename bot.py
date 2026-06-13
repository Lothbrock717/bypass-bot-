import base64
import httpx
import cloudscraper
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

async def try_decode_ad_form(ad_form_data: str) -> str:
    try:
        decoded = base64.b64decode(ad_form_data).decode('utf-8', errors='ignore')
        # Look for t.me link inside decoded data
        match = re.search(r'https?://t\.me/\S+', decoded)
        if match:
            return match.group(0)
    except:
        pass
    return None

async def bypass_link(url: str) -> dict:
    debug = {}
    
    # Method 1: cloudscraper
    try:
        scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )
        r = scraper.get(url, timeout=30)
        debug["method1_status"] = r.status_code
        
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            
            # Try get-link button
            link = soup.find("a", {"id": "get-link"})
            if link and link.get("href") and "void" not in link["href"]:
                return {"url": link["href"], "method": "get-link"}
            
            # Try ad_form_data decode
            ad_input = soup.find("input", {"name": "ad_form_data"})
            if ad_input:
                ad_data = ad_input.get("value", "")
                debug["ad_form_found"] = True
                
                # Try base64 decode
                decoded_url = await try_decode_ad_form(ad_data)
                if decoded_url:
                    return {"url": decoded_url, "method": "base64_decode"}
                
                # Try POST to /links/go
                csrf_input = soup.find("input", {"name": "_csrfToken"})
                if csrf_input:
                    csrf = csrf_input.get("value")
                    res = scraper.post(
                        "https://inshorturl.in/links/go",
                        data={
                            "_method": "POST",
                            "_csrfToken": csrf,
                            "ad_form_data": ad_data,
                            "cf_turnstile_response": "free_bypass"
                        },
                        headers={
                            "X-Requested-With": "XMLHttpRequest",
                            "Referer": str(r.url),
                            "Origin": "https://inshorturl.in"
                        }
                    )
                    debug["post_status"] = res.status_code
                    debug["post_response"] = res.text[:200]
                    try:
                        json_res = res.json()
                        if json_res.get("status") == "success":
                            return {"url": json_res["url"], "method": "post"}
                    except:
                        pass
            
            # Try find any t.me link in page
            tme = re.search(r'https?://t\.me/\S+', r.text)
            if tme:
                return {"url": tme.group(0), "method": "regex_scan"}
            
            debug["html_snippet"] = r.text[:300]
        
    except Exception as e:
        debug["method1_error"] = str(e)
    
    # Method 2: httpx with different headers
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            headers = {
                "User-Agent": UA,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
            }
            r2 = await client.get(url, headers=headers)
            debug["method2_status"] = r2.status_code
            
            if r2.status_code == 200:
                tme = re.search(r'https?://t\.me/\S+', r2.text)
                if tme:
                    return {"url": tme.group(0), "method": "httpx_regex"}
                
                soup2 = BeautifulSoup(r2.text, "html.parser")
                link2 = soup2.find("a", {"id": "get-link"})
                if link2 and link2.get("href") and "void" not in link2["href"]:
                    return {"url": link2["href"], "method": "httpx_getlink"}
                    
                debug["method2_html"] = r2.text[:200]
    except Exception as e:
        debug["method2_error"] = str(e)
    
    return {"url": None, "debug": debug}

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
    if not text.startswith("http"):
        await message.reply("Please send a valid URL.")
        return
    if "inshorturl.in" not in text:
        await message.reply("Please send a valid `inshorturl.in` link.")
        return
    
    msg = await message.reply("⏳ Bypassing link, please wait...")
    
    try:
        result = await bypass_link(text)
        if result.get("url"):
            await msg.edit(
                f"✅ **Bypassed Successfully!**\n\n"
                f"**Method:** `{result.get('method')}`\n"
                f"**Final Link:**\n`{result['url']}`"
            )
        else:
            debug_text = "\n".join([f"`{k}`: {v}" for k, v in result.get("debug", {}).items()])
            await msg.edit(
                f"❌ **Could not bypass.**\n\n"
                f"**Debug:**\n{debug_text}"
            )
    except Exception as e:
        await msg.edit(f"❌ Error: `{str(e)}`")

app.run()
