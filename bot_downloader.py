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
    'user-agent': 'Mozilla/5.0 (Linux; Android 8.0; Pixel 2 Build/OPD3.170816.012) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Mobile Safari/537.36'
}

def send_message(chat_id, text):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    return requests.post(url, json=payload)

def delete_message(chat_id, message_id):
    url = f"{TELEGRAM_API}/deleteMessage"
    payload = {"chat_id": chat_id, "message_id": message_id}
    requests.post(url, json=payload)

def send_video(chat_id, video_path):
    url = f"{TELEGRAM_API}/sendVideo"
    with open(video_path, 'rb') as video:
        files = {'video': video}
        data = {
            'chat_id': chat_id,
            'caption': "🎬 *Tải thành công!*\n\n🤖 _Bot Online 24/7 by Thuyet Nguyen_",
            'parse_mode': 'Markdown'
        }
        requests.post(url, data=data, files=files)

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
        js = requests.get(url=jx_url, headers=headers_global, timeout=10).json()
        if js and 'item_list' in js and len(js['item_list']) > 0:
            uri = js['item_list'][0]['video']['play_addr']['uri']
            high_quality_url = f'https://aweme.snssdk.com/aweme/v1/play/?video_id={uri}&radio=1080p&line=0'
            video_content = requests.get(url=high_quality_url, headers=headers_global, timeout=15).content
            with open(out_filename, 'wb') as f:
                f.write(video_content)
            return out_filename
    except Exception as e:
        print(f"Lỗi Douyin: {e}")
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
    except Exception as e:
        print(f"Lỗi TikTok: {e}")
    return None

# --- XỬ LÝ LIÊN KẾT WEBHOOK VÀ PHẢN HỒI RENDER ---
class WebhookHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        # Trả lời nhanh yêu cầu quét thử của Render để báo hệ thống Live
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot Telegram is Live!")

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
            
            if not any(x in lower_url for x in ["tiktok.com", "douyin.com", "x.com", "twitter.com"]):
                return

            # Gửi tin nhắn trạng thái và lấy message_id để xóa sau
            res_msg = send_message(chat_id, "⏳ Em đang xử lý rồi ạ!")
            waiting_id = res_msg.json().get("result", {}).get("message_id") if res_msg.status_code == 200 else None
            
            try:
                if "douyin.com" in lower_url:
                    video_file_path = extract_douyin_video(clean_url)
                else:
                    video_file_path = extract_tiktok_video(clean_url)
                    
                if video_file_path and os.path.exists(video_file_path) and os.path.getsize(video_file_path) > 0:
                    send_video(chat_id, video_file_path)
                    os.remove(video_file_path)
                else:
                    send_message(chat_id, "❌ Bẻ khóa link thất bại hoặc dải mạng bận. Anh gửi lại link sau ít phút nhé.")
            except Exception as e:
                send_message(chat_id, f"⚠️ Lỗi: {str(e)}")
                
            if waiting_id:
                delete_message(chat_id, waiting_id)

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), WebhookHandler)
    logging.info(f"🚀 Hệ thống Webhook đang mở tại cổng PORT: {port}")
    
    # TỰ ĐỘNG THIẾT LẬP WEBHOOK VỚI TELEGRAM KHI HOẠT ĐỘNG
    # Render tự động cấp biến RENDER_EXTERNAL_URL chứa link web của anh
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if render_url:
        set_webhook_url = f"{TELEGRAM_API}/setWebhook?url={render_url}"
        requests.get(set_webhook_url)
        logging.info(f"📡 Đã móc nối tín hiệu thành công tới URL: {render_url}")
        
    server.serve_forever()

if __name__ == '__main__':
    run_server()
