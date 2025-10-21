import requests
from bs4 import BeautifulSoup
import time
import json
import os
from datetime import datetime, timedelta, timezone

TOKEN = os.environ.get('TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
URL = 'https://indodax.com/newsflash'
LAST_POST_FILE = 'last_newsflash.json'

def get_latest_newsflash():
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    # Ambil <p> pertama yang punya <a> (posting terbaru)
    p = soup.find('p', style=lambda value: value and '#333333' in value)
    if p:
        a = p.find('a', href=True)
        span = p.find('span')
        # Ambil ringkasan (teks setelah <img>)
        img = p.find('img')
        summary = ""
        if img and img.next_sibling:
            summary = img.next_sibling.strip()
        elif img and img.parent:
            # Kadang ringkasan ada di parent setelah <img>
            summary = img.parent.get_text(separator=" ", strip=True)
        elif a and a.next_sibling:
            summary = a.next_sibling.strip()
        return {
            'title': a.get_text(strip=True) if a else '',
            'url': a['href'] if a else '',
            'date': span.get_text(strip=True) if span else '',
            'summary': summary
        }
    return None

def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    data = {
        'chat_id': CHAT_ID,
        'text': message,
        'disable_web_page_preview': False
    }
    requests.post(url, data=data)

def load_last_post():
    if os.path.exists(LAST_POST_FILE):
        with open(LAST_POST_FILE, 'r') as f:
            return json.load(f).get('last_post')
    return None

def save_last_post(post_url):
    with open(LAST_POST_FILE, 'w') as f:
        json.dump({'last_post': post_url}, f)

def main():
    while True:
        latest = get_latest_newsflash()
        last = load_last_post()
        if latest and latest['url'] != last:
            wib = timezone(timedelta(hours=7))
            now = datetime.now(wib).strftime('%Y-%m-%d %H:%M:%S')
            message = (
                f"Update Newsflash Indodax:\n\n"
                f"{latest['title']}\n"
                f"{latest['url']}\n"
                f"Tanggal: {latest['date']}\n"
                f"Ringkasan: {latest['summary']}\n\n"
                f"Waktu update (WIB): {now}"
            )
            send_telegram_message(message)
            save_last_post(latest['url'])
            print("Notifikasi dikirim:", latest['title'])
        else:
            print("Belum ada update baru.")
        time.sleep(30)  # Cek waktu

if __name__ == '__main__':
    main()
