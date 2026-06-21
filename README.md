# Ray-Ban Meta Smart Glasses — Çoklu Platform Marka Risk Tahmini

**YBS Python ile Veri Bilimi | Final Projesi | 132230044 Furkan Akdemir**

Tema 1: Yapılandırılmış & Yapılandırılmamış Veri ile Risk Tahmini (Karma Model)

## Proje Özeti

YouTube, Google Play, App Store ve Reddit'ten toplanan 64,792 gerçek yorum ile Google Trends, hisse fiyatı ve haber olaylarını 5 katmanlı füzyon stratejisiyle birleştirerek, negatif duygu riskini yapısal sinyallerden tahmin eden bir makine öğrenmesi modeli.

## Sonuçlar

| Metrik | Değer |
|---|---|
| Test AUC | 0.8186 |
| Accuracy | %77 |
| En İyi Model | Random Forest |
| Veri Kaynağı | 8 farklı kaynak, 4 platform |
| Sentiment Modeli | RoBERTa (cardiffnlp/twitter-roberta-base-sentiment-latest) |
| Finansal Etki | $33,917/ay net kazanç, %267 ROI |

## Çalıştırma

```bash
# Ana pipeline (veri yükleme → sentiment → füzyon → model → SHAP → simülasyon)
python main.py

# PDF rapor üretimi
python build_report.py
```

**Not:** İlk çalıştırmada RoBERTa sentiment analizi ~90 dakika sürer (CPU). Sonraki çalıştırmalarda cache'ten okunur.

## Veri Kaynakları

| # | Kaynak | Tür | Dosya |
|---|---|---|---|
| 1 | YouTube Yorumları | Yapılandırılmamış | `youtube_urun_incelemeleri.csv`, `youtube_deneyim.csv` |
| 2 | Google Play (Meta AI App) | Yapılandırılmamış + Yıldız | `yorumlar_google_play.csv` |
| 3 | App Store (Meta AI App) | Yapılandırılmamış + Yıldız | `yorumlar_appstore.csv` |
| 4 | Reddit / Forum | Yapılandırılmamış | `yorumlar_forumlar.csv` |
| 5 | Google Trends | Yapılandırılmış | `google_trends_rayban_meta.csv` |
| 6 | Hisse Fiyatları | Yapılandırılmış | `meta_hisse_fiyatlari.csv`, `essilorluxottica_hisse_fiyatlari.csv` |
| 7 | Haber Olayları | Yapılandırılmış | `rayban_meta_global_haberler.csv` |
| 8 | Video Performans Meta | Yapılandırılmış | `youtube_video_meta.csv` |

## Scraping Scriptleri

```bash
python scrape_google_play.py   # Google Play yorumları
python scrape_appstore.py      # App Store yorumları (iTunes RSS)
python scrape_amazon.py        # Amazon yorumları (Selenium)
python scrape_forums.py        # Reddit + Technopat
```

## Dosya Yapısı

```
main.py                  — Ana pipeline
build_report.py          — PDF rapor üretici
scrape_*.py              — Veri toplama scriptleri
figures/                 — Görseller + metrics.json
Yonetici_Ozeti_Raporu.pdf — Yönetici özet raporu
*.csv                    — Veri dosyaları
```
