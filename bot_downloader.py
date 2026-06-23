import os
import re
import json
import logging
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# TOKEN BOT TELEGRAM CỦA ANH THUYẾT
BOT_TOKEN = "8860560486:AAGvyOYCG3UlnP6crQKZdcW-NH9EVNUHTvA"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

headers_global = {
    'user-agent': 'Mozilla/5.0 (Linux; Android 8.0; Pixel 2 Build/OPD3.170816.012) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Mobile Safari/537.36'
}

def extract_douyin_video(clean_url):
    out_filename = "douyin_final.mp4"
    if os.path.exists(out_filename): os.remove(out_filename)
        
    try:
        r = requests.get(url=clean_url, headers=headers_global, allow_redirects=True, timeout=10)
        final_url = r.url
        
        item_id_match = re.search(r'video/(\d+)', final_url)
        if not item_id_match: return None
        item_id = item_id_match.group(1)
        
        jx_url = f'https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids={item_id}'
        response = requests.get(url=jx_url, headers=headers_global, timeout=10)
        js = json.loads(response.text)
        
        if js and 'item_list' in js and len(js['item_list']) > 0:
            uri = js['item_list'][0]['video']['play_addr']['uri']
            high_quality_url = f'https://aweme.snssdk.com/aweme/v1/play/?video_id={uri}&radio=1080p&line=0'
            
            video_content = requests.get(url=high_quality_url, headers=headers_global, timeout=15).content
            with open(out_filename, 'wb') as f:
                f.write(video_content)
            return out_filename
    except:
        pass
    return None

def extract_tiktok_video(clean_url):
    out_filename = "tiktok_final.mp4"
    if os.path.exists(out_filename): os.remove(out_filename)
        
    try:
        api_url = "https://www.tikwm.com/api/?url=" + requests.utils.quote(clean_url)
        res = requests.get(api_url, headers=headers_global, timeout=10).json()
        if res and res.get("code") == 0 and "data" in res:
            play_url = res["data"].get("hdplay") or res["data"].get("play")
            download_url = play_url if play_url.startswith("http") else "https://www.tikwm.com" + play_url
            video_content = requests.get(download_url, timeout=15).content
            with open(out_filename, 'wb') as f:
                f.write(video_content)
            return out_filename
    except:
        pass
    return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.message.chat_id
    
    match = re.search(r'https?://[^\s]+', text)
    if not match: return

    clean_url = match.group(0).replace('〉', '').replace('】', '').replace('」', '')
    lower_url = clean_url.lower()
    
    if not any(x in lower_url for x in ["tiktok.com", "douyin.com", "x.com", "twitter.com"]):
        return

    waiting_msg = await context.bot.send_message(chat_id=chat_id, text="⏳ Em đang xử lý rồi ạ!")
    
    try:
        video_file_path = None
        if "douyin.com" in lower_url:
            video_file_path = extract_douyin_video(clean_url)
        else:
            video_file_path = extract_tiktok_video(clean_url)
            
        if video_file_path and os.path.exists(video_file_path) and os.path.getsize(video_file_path) > 0:
            with open(video_file_path, 'rb') as video:
                await context.bot.send_video(
                    chat_id=chat_id, 
                    video=video, 
                    caption="🎬 *Tải thành công!*\n\n🤖 _Bot Online 24/7 by Thuyet Nguyen_",
                    parse_mode="Markdown"
                )
            os.remove(video_file_path)
        else:
            await context.bot.send_message(chat_id=chat_id, text="❌ Cổng bẻ khóa link hiện tại đang bận hoặc dải IP đám mây bị nghẽn. Anh thử gửi lại link sau ít phút nhé!")
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text="⚠️ Lỗi: " + str(e))
        
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=waiting_msg.message_id)
    except:
        pass

def main():
    print("🚀 Bot Downloader Online đang chạy...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()