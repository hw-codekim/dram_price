import requests
import json
import os
from telegram import Bot

# 텔레그램 봇 토큰과 채팅 ID
# GitHub Actions에서는 환경변수, 로컬에서는 bot_key.json
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

if not BOT_TOKEN or not CHAT_ID:
    # 로컬에서 bot_key.json 읽기
    with open('bot_key.json', 'r') as file:
        data = json.load(file)
        BOT_TOKEN = data['BOT_TOKEN']
        CHAT_ID = data['CHAT_ID']

bot = Bot(token=BOT_TOKEN)

# 전송할 파일 경로
FILE_PATH = "DDR5_16G.png"

def send_photo(file_path=FILE_PATH, bot_token=BOT_TOKEN, chat_id=CHAT_ID):
    """
    텔레그램으로 PNG 파일 전송
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    with open(file_path, "rb") as f:
        files = {"photo": f}
        data = {"chat_id": chat_id}
        response = requests.post(url, files=files, data=data)
    if response.status_code == 200:
        print("✅ Telegram 전송 성공")
    else:
        print(f"❌ 전송 실패: {response.status_code}, {response.text}")

if __name__ == "__main__":
    send_photo()