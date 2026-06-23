import os
import re
import json
import logging
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer

# TOKEN BOT TELEGRAM CỦA ANH THUYẾT
BOT_TOKEN = "8860560486:AAGvyOYCG3UlnP6crQKZdcW-NH9EVNUHTvA"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

headers_global = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
}

def send_message(chat_id, text, parse_mode=None):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    return requests.post(url, json=payload)

def delete_message(chat_id, message_id):
    url = f"{TELEGRAM_API}/deleteMessage"
    payload = {"chat_id": chat_id, "message_id": message_id}
    requests.post(url, json=payload)

def send_video(chat_id, video_url, caption_text):
    url = f"{TELEGRAM_API}/sendVideo"
    payload = {
        'chat_id': chat_id,
        'video': video_url,
        'caption': f"🎬 *Tải thành công!*\n\n📝 _Tiêu đề:_ {caption_text}\n🤖 _Bot Online 24/7 by Thuyet Nguyen_",
        'parse_mode': 'Markdown'
    }
    return requests.post(url, json=payload)

# 🚀 TRỤC GIẢI MÃ 1: LÕI CAO CẤP TIKWM
def extract_axis_1(clean_url):
    try:
        api_url = f"https://www.tikwm.com/api/?url={requests.utils.quote(clean_url)}"
        res = requests.get(api_url, headers=headers_global, timeout=10).json()
        if res and res.get("code") == 0 and "data" in res:
            v_data = res["data"]
            play_url = v_data.get("hdplay") or v_data.get("play")
            download_url = play_url if play_url.startswith("http") else "https://www.tikwm.com" + play_url
            return {"video_url": download_url, "title": v_data.get("title", "Video Media")}
    except:
        pass
    return None

# 🚀 TRỤC GIẢI MÃ 2: LÕI DỰ PHÒNG HYBRID
def extract_axis_2(clean_url):
    try:
        api_endpoint = f"https://api.vvevveapps.com/v1/video/parse?url={requests.utils.quote(clean_url)}"
        res = requests.get(api_endpoint, headers=headers_global, timeout=10).json()
        if res and res.get("code") == 200 and "data" in res:
            v_data = res["data"]
            v_url = v_data.get("video_nowatermark") or v_data.get("video")
            if v_url:
                return {"video_url": v_url, "title": v_data.get("title", "Video Media")}
    except:
        pass
    return None

# 🚀 TRỤC GIẢI MÃ 3: LÕI SIÊU TỐC LOẠI C
def extract_axis_3(clean_url):
    try:
        api_url = f"https://api.douyin.wtf/api?url={requests.utils.quote(clean_url)}"
        res = requests.get(api_url, headers=headers_global, timeout=10).json()
        if res and res.get("status") == "success":
            return {"video_url": res.get("nwm_video_url"), "title": res.get("desc", "Video Media")}
    except:
        pass
    return None

# --- LUỒNG WEBHOOK PHẢN HỒI RENDER ---
class WebhookHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot Telegram 3 Axis with Welcome is Live!")

    def do_POST(self):
        self.send_response(200)
        self.end_headers()
        
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        update = json.loads(post_data.decode('utf-8'))
        
        if "message" in update and "text" in update["message"]:
            text = update["message"]["text"].strip()
            chat_id = update["message"]["chat"]["id"]
            
            # 1. XỬ LÝ LỆNH /START HOẶC /HELP CHÀO HỎI NGƯỜI DÙNG
            if text.startswith("/start"):
                welcome_txt = (
                    "🚀 *Chào mừng anh Thuyết đã kích hoạt Bot thành công!*\n\n"
                    "🤖 Con Bot này chạy online đám mây vĩnh viễn 24/7, chuyên dùng để "
                    "bẻ khóa lấy video sạch logo phục vụ cày re-up MMO.\n\n"
                    "📌 *Cách dùng cực kỳ đơn giản:*\n"
                    "Anh chỉ cần sao chép link video từ *Douyin, TikTok, hoặc Kuaishou* "
                    "rồi dán thẳng vào đây. Hệ thống tự động gọt logo và bắn file về điện thoại cho anh nhé sếp!"
                )
                send_message(chat_id, welcome_txt, parse_mode="Markdown")
                return

            if text.startswith("/help"):
                help_txt = "💡 *Hướng dẫn:* Anh chỉ cần mở app Douyin/TikTok ➔ Bấm chia sẻ video ➔ Sao chép liên kết ➔ Gửi link đó vào đây là xong ạ!"
                send_message(chat_id, help_txt, parse_mode="Markdown")
                return
            
            # 2. XỬ LÝ KHI NGƯỜI DÙNG GỬI LINK VIDEO
            match = re.search(r'https?://[^\s]+', text)
            if not match: 
                send_message(chat_id, "⚠️ Tin nhắn không chứa liên kết hợp lệ. Anh vui lòng gửi đúng link Douyin hoặc TikTok nhé sếp!")
                return

            clean_url = match.group(0).replace('〉', '').replace('】', '').replace('」', '')
            lower_url = clean_url.lower()
            
            if not any(x in lower_url for x in ["tiktok.com", "douyin.com", "kuaishou.com", "twitter.com", "x.com"]):
                send_message(chat_id, "❌ Hệ thống hiện tại chỉ hỗ trợ bẻ khóa link từ Douyin, TikTok và Kuaishou thôi ạ.")
                return

            res_msg = send_message(chat_id, "⏳ Em đang bẻ khóa link video rồi sếp ạ!")
            waiting_id = res_msg.json().get("result", {}).get("message_id") if res_msg.status_code == 200 else None
            
            media_data = None
            # Quét tuần tự qua các trục giải mã
            for extract_func in [extract_axis_1, extract_axis_2, extract_axis_3]:
                media_data = extract_func(clean_url)
                if media_data and media_data["video_url"]:
                    break
            
            try:
                if media_data and media_data["video_url"]:
                    video_res = send_video(chat_id, media_data["video_url"], media_data["title"])
                    if video_res.status_code != 200:
                        send_message(chat_id, "❌ Kích thước video vượt quá giới hạn tải lên của Telegram đám mây. Anh thử link khác xem nhé!")
                else:
                    send_message(chat_id, "❌ Cả 3 cổng bẻ khóa dự phòng hiện tại đều đang bận xử lý dải IP này. Sếp gửi lại link sau ít phút nhé!")
            except Exception as e:
                send_message(chat_id, f"⚠️ Lỗi phát sinh: {str(e)}")
                
            if waiting_id:
                delete_message(chat_id, waiting_id)

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), WebhookHandler)
    
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if render_url:
        requests.get(f"{TELEGRAM_API}/setWebhook?url={render_url}")
        
    server.serve_forever()

if __name__ == '__main__':
    run_server()
