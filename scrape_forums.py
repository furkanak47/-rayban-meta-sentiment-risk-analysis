"""
Reddit + Technopat — Ray-Ban Meta tartışma verileri
Reddit: Pushshift/Pullpush arsiv API (auth gerektirmez, 403 yok)
Technopat: Google cache uzerinden konu bulma
Çalıştır: python scrape_forums.py
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

import requests
from bs4 import BeautifulSoup
import csv
import time
import json

OUTPUT = "yorumlar_forumlar.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
}

all_posts = []

# ──────────────────────────────────────────────────────
# 1. REDDIT — Pullpush.io arsiv API (auth gerektirmez)
# ──────────────────────────────────────────────────────
print("=" * 60)
print("1/2 — Reddit (Pullpush Arsiv API)")
print("=" * 60)

SEARCH_TERMS = ["ray-ban meta", "rayban meta", "ray ban meta glasses", "meta smart glasses", "meta ray ban display"]
SUBREDDITS = ["RayBanMeta", "smartglasses", "MetaQuest", "gadgets", "technology", "apple", "Android"]

# Submission (post) ara
for term in SEARCH_TERMS:
    print(f"\n  Aranıyor: '{term}'")
    url = f"https://api.pullpush.io/reddit/search/submission/?q={term.replace(' ', '+')}&size=100&sort=desc&sort_type=score"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            for d in data:
                all_posts.append({
                    "post_id": d.get("id", ""),
                    "tip": "post",
                    "forum": f"reddit_r/{d.get('subreddit', '')}",
                    "konu_basligi": d.get("title", ""),
                    "konu_url": f"https://reddit.com{d.get('permalink', '')}",
                    "kullanici": d.get("author", ""),
                    "yorum_metni": d.get("selftext", d.get("title", ""))[:5000],
                    "tarih_unix": d.get("created_utc", ""),
                    "skor": d.get("score", 0),
                    "yorum_sayisi": d.get("num_comments", 0),
                    "kaynak": "reddit_pullpush"
                })
            print(f"    +{len(data)} post")
        else:
            print(f"    HTTP {resp.status_code}")
        time.sleep(1)
    except Exception as e:
        print(f"    Hata: {e}")

# Comment (yorum) ara
for term in SEARCH_TERMS[:3]:
    print(f"\n  Yorum aranıyor: '{term}'")
    url = f"https://api.pullpush.io/reddit/search/comment/?q={term.replace(' ', '+')}&size=100&sort=desc&sort_type=score"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            for d in data:
                all_posts.append({
                    "post_id": d.get("id", ""),
                    "tip": "comment",
                    "forum": f"reddit_r/{d.get('subreddit', '')}",
                    "konu_basligi": "",
                    "konu_url": f"https://reddit.com{d.get('permalink', '')}" if d.get("permalink") else "",
                    "kullanici": d.get("author", ""),
                    "yorum_metni": d.get("body", "")[:5000],
                    "tarih_unix": d.get("created_utc", ""),
                    "skor": d.get("score", 0),
                    "yorum_sayisi": 0,
                    "kaynak": "reddit_pullpush"
                })
            print(f"    +{len(data)} yorum")
        else:
            print(f"    HTTP {resp.status_code}")
        time.sleep(1)
    except Exception as e:
        print(f"    Hata: {e}")

# Subreddit bazli da cek
for sub in SUBREDDITS:
    url = f"https://api.pullpush.io/reddit/search/submission/?subreddit={sub}&q=ray-ban+OR+rayban+OR+meta+glasses&size=50&sort=desc&sort_type=score"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            for d in data:
                all_posts.append({
                    "post_id": d.get("id", ""),
                    "tip": "post",
                    "forum": f"reddit_r/{sub}",
                    "konu_basligi": d.get("title", ""),
                    "konu_url": f"https://reddit.com{d.get('permalink', '')}",
                    "kullanici": d.get("author", ""),
                    "yorum_metni": d.get("selftext", d.get("title", ""))[:5000],
                    "tarih_unix": d.get("created_utc", ""),
                    "skor": d.get("score", 0),
                    "yorum_sayisi": d.get("num_comments", 0),
                    "kaynak": "reddit_pullpush"
                })
            if data:
                print(f"  r/{sub}: +{len(data)} post")
        time.sleep(1)
    except:
        pass

# Tekrarlari kaldir
seen = set()
unique_reddit = []
for p in all_posts:
    pid = p["post_id"]
    if pid and pid not in seen:
        seen.add(pid)
        unique_reddit.append(p)
all_posts = unique_reddit

print(f"\n  Reddit toplam (benzersiz): {len(all_posts)} post/yorum")

# ──────────────────────────────────────────────────────
# 2. TECHNOPAT — Dogrudan konu URL'leri dene
# ──────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("2/2 — Technopat Forum")
print("=" * 60)

technopat_before = len(all_posts)

# Bilinen/aranabilecek URL pattern'leri
technopat_search_urls = [
    "https://www.technopat.net/sosyal/ara/?q=ray+ban+meta&t=post&o=date",
    "https://www.technopat.net/sosyal/ara/?q=akıllı+gözlük&t=post&o=date",
    "https://www.technopat.net/sosyal/ara/?q=meta+gözlük&t=post&o=date",
    "https://www.technopat.net/sosyal/ara/?q=smart+glasses&t=post&o=date",
]

thread_urls = set()

for search_url in technopat_search_urls:
    try:
        resp = requests.get(search_url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "lxml")
            # Tum konu linklerini bul
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/konu/" in href and "sik-sorulan" not in href and "kurallari" not in href:
                    full = href if href.startswith("http") else f"https://www.technopat.net{href}"
                    thread_urls.add(full)
        time.sleep(2)
    except:
        pass

print(f"  {len(thread_urls)} konu bulundu")

for thread_url in list(thread_urls)[:20]:
    try:
        resp = requests.get(thread_url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            continue

        soup = BeautifulSoup(resp.text, "lxml")
        title_el = soup.select_one("h1.p-title-value")
        title = title_el.get_text(strip=True) if title_el else ""

        messages = soup.select("article.message")
        msg_count = 0
        for msg in messages:
            author = ""
            try:
                author = msg.select_one("a.username").text.strip()
            except:
                pass

            body = ""
            try:
                body = msg.select_one("div.bbWrapper").get_text(separator=" ", strip=True)
            except:
                pass

            date = ""
            try:
                date = msg.select_one("time.u-dt").get("datetime", "")
            except:
                pass

            if body and len(body) > 10:
                all_posts.append({
                    "post_id": msg.get("data-content", ""),
                    "tip": "forum_post",
                    "forum": "technopat",
                    "konu_basligi": title,
                    "konu_url": thread_url,
                    "kullanici": author,
                    "yorum_metni": body[:5000],
                    "tarih_unix": date,
                    "skor": 0,
                    "yorum_sayisi": 0,
                    "kaynak": "technopat"
                })
                msg_count += 1

        if msg_count > 0:
            print(f"  {title[:50]}... -> {msg_count} mesaj")
        time.sleep(2)
    except:
        pass

technopat_count = len(all_posts) - technopat_before
print(f"\n  Technopat toplam: {technopat_count} mesaj")

# CSV kaydet
print(f"\n{'=' * 60}")
print(f"GENEL TOPLAM: {len(all_posts)} post/yorum")

if all_posts:
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_posts[0].keys())
        writer.writeheader()
        writer.writerows(all_posts)
    print(f"Kaydedildi: {OUTPUT}")
else:
    print("Veri cekilemedi!")

print("Bitti!")
