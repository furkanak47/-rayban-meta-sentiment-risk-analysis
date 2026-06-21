"""
Amazon — Ray-Ban Meta Smart Glasses Yorumları (Selenium)
Çalıştır: python scrape_amazon.py

Not: chromedriver otomatik indirilir (selenium 4.6+)
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

import csv
import time
import re

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("Eksik paket. Yuklemek icin:")
    print("  pip install selenium webdriver-manager")
    sys.exit(1)

OUTPUT = "yorumlar_amazon.csv"

# Dogrulanmis ASIN'ler
PRODUCTS = [
    {"asin": "B0CGXYNWBH", "urun": "Ray-Ban Meta Wayfarer Large Gen1 Matte Black"},
    {"asin": "B0CGXYM9TP", "urun": "Ray-Ban Meta Wayfarer Gen1 Shiny Black Clear"},
    {"asin": "B0CGXYVQ1P", "urun": "Ray-Ban Meta Wayfarer Gen1 Matte Black Polarized"},
    {"asin": "B0FRN9L85M", "urun": "Ray-Ban Meta Wayfarer Large Gen2 Transitions Grey"},
    {"asin": "B0FLYDWQDZ", "urun": "Ray-Ban Meta Wayfarer Gen2 Matte Black Polarized"},
    {"asin": "B0FLYJM9DC", "urun": "Ray-Ban Meta Wayfarer Large Gen2 Transitions Grey v2"},
]

print("=" * 60)
print("Amazon Scraper (Selenium) — Ray-Ban Meta Smart Glasses")
print("=" * 60)

# Chrome headless baslat
options = Options()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")

try:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
except Exception as e:
    print(f"Chrome baslatilamadi: {e}")
    print("Google Chrome tarayicisinin yuklu oldugundan emin olun.")
    sys.exit(1)

print("Chrome baslatildi.\n")

all_reviews = []

for product in PRODUCTS:
    asin = product["asin"]
    urun = product["urun"]
    print(f">>> {urun} (ASIN: {asin})")

    for page in range(1, 16):
        url = f"https://www.amazon.com/product-reviews/{asin}?pageNumber={page}&sortBy=recent"

        try:
            driver.get(url)
            time.sleep(3)

            # Captcha kontrolu
            if "captcha" in driver.page_source.lower():
                print(f"  CAPTCHA engeli! Sayfa {page}'de durduruluyor.")
                break

            review_els = driver.find_elements(By.CSS_SELECTOR, "div[data-hook='review']")

            if not review_els:
                print(f"  Sayfa {page}: Yorum yok, durduruluyor.")
                break

            for el in review_els:
                try:
                    author = ""
                    try:
                        author = el.find_element(By.CSS_SELECTOR, "span.a-profile-name").text
                    except:
                        pass

                    rating = ""
                    try:
                        rating_text = el.find_element(By.CSS_SELECTOR, "i[data-hook='review-star-rating'] span").get_attribute("textContent")
                        match = re.search(r"(\d+\.?\d*)", rating_text)
                        rating = float(match.group(1)) if match else ""
                    except:
                        pass

                    date_text = ""
                    try:
                        date_text = el.find_element(By.CSS_SELECTOR, "span[data-hook='review-date']").text
                    except:
                        pass

                    title = ""
                    try:
                        title = el.find_element(By.CSS_SELECTOR, "a[data-hook='review-title'] span:last-child").text
                    except:
                        try:
                            title = el.find_element(By.CSS_SELECTOR, "a[data-hook='review-title']").text
                        except:
                            pass

                    body = ""
                    try:
                        body = el.find_element(By.CSS_SELECTOR, "span[data-hook='review-body']").text
                    except:
                        pass

                    verified = "Hayir"
                    try:
                        el.find_element(By.CSS_SELECTOR, "span[data-hook='avp-badge']")
                        verified = "Evet"
                    except:
                        pass

                    helpful = "0"
                    try:
                        helpful = el.find_element(By.CSS_SELECTOR, "span[data-hook='helpful-vote-statement']").text
                    except:
                        pass

                    review_id = el.get_attribute("id") or ""

                    if body:
                        all_reviews.append({
                            "review_id": review_id,
                            "urun": urun,
                            "asin": asin,
                            "kullanici": author,
                            "puan": rating,
                            "baslik": title,
                            "yorum_metni": body,
                            "tarih": date_text,
                            "dogrulanmis": verified,
                            "faydali": helpful,
                            "kaynak": "amazon"
                        })
                except:
                    pass

            print(f"  Sayfa {page}: +{len(review_els)} yorum (toplam: {len(all_reviews)})")
            time.sleep(2)

        except Exception as e:
            print(f"  Sayfa {page} hata: {e}")
            break

driver.quit()
print("\nChrome kapatildi.")

print(f"\nToplam: {len(all_reviews)} yorum")
if all_reviews:
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_reviews[0].keys())
        writer.writeheader()
        writer.writerows(all_reviews)
    print(f"Kaydedildi: {OUTPUT}")
else:
    print("Yorum cekilemedi. Amazon Turkiye IP'sini engelliyor olabilir.")
    print("VPN ile ABD IP'si kullanarak tekrar deneyin.")

print("Bitti!")
