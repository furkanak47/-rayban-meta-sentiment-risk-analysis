"""
Apple App Store — Meta AI App Yorumları (iTunes RSS API)
Çalıştır: python scrape_appstore.py
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

import requests
import csv
import time

APP_ID = "1558240027"  # Meta AI (eski Meta View)
OUTPUT = "yorumlar_appstore.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

COUNTRIES = ["us","gb","ca","au","de","fr","it","es","nl","se","dk","no","ie","br","mx","jp","kr","in","sg","ae","za","tr"]

print("=" * 60)
print("App Store Scraper — Meta AI (Ray-Ban Meta companion)")
print("=" * 60)

all_reviews = []

for country in COUNTRIES:
    country_count = 0
    for page in range(1, 11):
        url = f"https://itunes.apple.com/{country}/rss/customerreviews/id={APP_ID}/page={page}/sortby=mostrecent/json"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code != 200:
                break

            data = resp.json()
            entries = data.get("feed", {}).get("entry", [])

            if not entries:
                break

            for entry in entries:
                if "im:rating" not in entry:
                    continue
                all_reviews.append({
                    "review_id": entry.get("id", {}).get("label", ""),
                    "ulke": country.upper(),
                    "kullanici": entry.get("author", {}).get("name", {}).get("label", ""),
                    "puan": entry.get("im:rating", {}).get("label", ""),
                    "baslik": entry.get("title", {}).get("label", ""),
                    "yorum_metni": entry.get("content", {}).get("label", ""),
                    "tarih": entry.get("updated", {}).get("label", ""),
                    "uygulama_versiyonu": entry.get("im:version", {}).get("label", ""),
                    "kaynak": "appstore"
                })
                country_count += 1

            time.sleep(0.5)
        except:
            break

    if country_count > 0:
        print(f"  {country.upper()}: {country_count} yorum")

# Tekrarlari kaldir
seen = set()
unique = []
for r in all_reviews:
    rid = r["review_id"]
    if rid and rid not in seen:
        seen.add(rid)
        unique.append(r)
all_reviews = unique

print(f"\nToplam benzersiz: {len(all_reviews)} yorum")

if all_reviews:
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_reviews[0].keys())
        writer.writeheader()
        writer.writerows(all_reviews)
    print(f"Kaydedildi: {OUTPUT}")
else:
    print("Yorum bulunamadi!")

print("Bitti!")
