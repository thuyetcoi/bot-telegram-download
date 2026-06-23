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
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def send_message(chat_id, text):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
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

# 🔄 TRỤC BẺ KHÓA SIÊU TỐC ĐA NĂNG (BAO SÂN CẢ DOUYIN VÀ TIKTOK)
def extract_media_api(clean_url):
    try:
        # Sử dụng API phân tích link video chuyên dụng, bypass mọi tường lửa IP đám mây
        api_endpoint = f"https://api.vvevveapps.com/v1/video/parse?url={requests.utils.quote(clean_url)}"
        res = requests.get(api_endpoint, headers=headers_global, timeout=15).json()
        
        if res and res.get("code") == 200 and "data" in res:
            video_data = res["data"]
            video_url = video_data.get("video_nowatermark") or video_data.get("video")
            title = video_data.get("title", "Video không tiêu đề")
            
            if video_url:
                # Trả về đường link video sạch logo trực tiếp để Telegram tự up, tiết kiệm bộ nhớ máy chủ
                return {"video_url": video_url, "title": title}
    except Exception as e:
        print(f"Lỗi trục bẻ khóa API: {e}")
    return None

# --- XỬ LÝ LIÊN KẾT WEBHOOK VÀ PHẢN HỒI RENDER ---
class WebhookHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot Telegram is Live and Ready!")

    def do_POST(self):
        self.send_response(200)
        self.end_headers()
        
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        update = json.loads(post_data.decode('utf-8'))
        
        if "message" in update and "text" in update["message"]:
            text = update["message"]["text"]
            chat_id = update["message"]["chat"]["id"]
            
            match = re.search(r'https?://[^\s]+', text)
            if not match: return

            clean_url = match.group(0).replace('〉', '').replace('】', '').replace('」', '')
            lower_url = clean_url.lower()
            
            if not any(x in lower_url for x in ["tiktok.com", "douyin.com", "kuaishou.com"]):
                return

            # Gửi thông báo đang xử lý
            res_msg = send_message(chat_id, "⏳ Em đang bẻ khóa link video rồi sếp ạ!")
            waiting_id = res_msg.json().get("result", {}).get("message_id") if res_msg.status_code == 200 else None
            
            try:
                # Gọi trục bẻ khóa chung cho cả Douyin/Tiktok
                media_data = extract_media_api(clean_url)
                
                if media_data and media_data["video_url"]:
                    # Bắn video trực tiếp qua URL cực nhanh, không lo nghẽn băng thông ổ đĩa Render
                    video_res = send_video(chat_id, media_data["video_url"], media_data["title"])
                    if video_res.status_code != 200:
                        send_message(chat_id, "❌ Kích thước video quá lớn hoặc Telegram từ chối tải file từ nguồn này. Sếp thử lại link khác nhé!")
                else:
                    send_message(chat_id, "❌ Cổng bẻ khóa thất bại do link lỗi hoặc tài khoản này cài đặt riêng tư. Sếp kiểm tra lại link nhé!")
            except Exception as e:
                send_message(chat_id, f"⚠️ Lỗi phát sinh: {str(e)}")
                
            if waiting_id:
                delete_message(chat_id, waiting_id)

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), WebhookHandler)
    logging.info(f"🚀 Hệ thống Webhook đang mở tại cổng PORT: {port}")
    
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if render_url:
        set_webhook_url = f"{TELEGRAM_API}/setWebhook?url={render_url}"
        requests.get(set_webhook_url)
        logging.info(f"📡 Đã cấu hình đồng bộ Webhook tới Render: {render_url}")
        
    server.serve_forever()

if __name__ == '__main__':
    run_server()
