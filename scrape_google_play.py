"""
Google Play Store — Meta AI (eski Meta View) App Yorumları
Çalıştır: python scrape_google_play.py
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

import csv
import time
from google_play_scraper import Sort, reviews, app

APP_ID = "com.facebook.stella"
OUTPUT = "yorumlar_google_play.csv"

print("=" * 60)
print("Google Play Scraper — Meta AI App (Ray-Ban Meta companion)")
print("=" * 60)

info = app(APP_ID, lang="en", country="us")
print(f"Uygulama  : {info['title']}")
print(f"Gelistirici: {info['developer']}")
print(f"Puan      : {info['score']}")
print(f"Inceleme  : {info['reviews']}")
print()

all_reviews = []
continuation_token = None

print("Ingilizce yorumlar cekiliyor...")
for i in range(50):
    try:
        result, continuation_token = reviews(
            APP_ID, lang="en", country="us",
            sort=Sort.NEWEST, count=200,
            continuation_token=continuation_token
        )
        if not result:
            break
        all_reviews.extend(result)
        print(f"  Batch {i+1}: +{len(result)} (toplam: {len(all_reviews)})")
        if continuation_token is None:
            break
        time.sleep(1)
    except Exception as e:
        print(f"  Hata: {e}")
        break

# Ek diller
for lang_code, country in [("en","gb"),("en","ca"),("en","au"),("de","de"),("fr","fr"),("es","es"),("it","it"),("pt","br"),("tr","tr"),("ja","jp"),("ko","kr"),("nl","nl")]:
    try:
        token = None
        for _ in range(5):
            r, token = reviews(APP_ID, lang=lang_code, country=country, sort=Sort.NEWEST, count=200, continuation_token=token)
            if not r:
                break
            all_reviews.extend(r)
            if token is None:
                break
            time.sleep(0.5)
        count = len([x for x in all_reviews if True])
        print(f"  {lang_code.upper()}-{country.upper()}: toplam simdi {len(all_reviews)}")
        time.sleep(1)
    except:
        pass

# Tekrarlari kaldir
seen = set()
unique = []
for r in all_reviews:
    rid = r.get("reviewId", "")
    if rid and rid not in seen:
        seen.add(rid)
        unique.append(r)
all_reviews = unique

print(f"\nToplam benzersiz: {len(all_reviews)} yorum")

with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "review_id","kullanici","puan","yorum_metni",
        "begeni_sayisi","tarih","yanit_metni","yanit_tarihi",
        "uygulama_versiyonu","kaynak"
    ])
    for r in all_reviews:
        writer.writerow([
            r.get("reviewId",""),
            r.get("userName",""),
            r.get("score",""),
            r.get("content",""),
            r.get("thumbsUpCount",0),
            r.get("at",""),
            r.get("replyContent",""),
            r.get("repliedAt",""),
            r.get("appVersion",""),
            "google_play"
        ])

print(f"Kaydedildi: {OUTPUT}")
print("Bitti!")
