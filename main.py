"""
Ray-Ban Meta Smart Glasses — Çoklu Platform Marka Risk Tahmini
YBS Python ile Veri Bilimi | Final Projesi | 132230044 Furkan Akdemir
Tema 1: Yapılandırılmış & Yapılandırılmamış Veri ile Risk Tahmini (Karma Model)

Çalıştır: python main.py
"""
import subprocess, sys, os, json, warnings, time
from pathlib import Path

# ── 0. PAKET KONTROLÜ ─────────────────────────────────────────────
def ensure_packages():
    pkgs = [
        "pandas", "numpy", "matplotlib", "seaborn", "scikit-learn",
        "shap", "wordcloud", "transformers", "torch", "xgboost",
        "reportlab",
    ]
    for p in pkgs:
        try:
            __import__(p.replace("-", "_"))
        except ImportError:
            print(f"  Yukleniyor: {p}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", p, "-q"])

print("Paket kontrolü...")
ensure_packages()

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud, STOPWORDS
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (classification_report, roc_auc_score, confusion_matrix,
                             ConfusionMatrixDisplay, RocCurveDisplay,
                             precision_recall_curve)
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.pipeline import Pipeline
import shap

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False
    print("  XGBoost bulunamadı, Gradient Boosting kullanılacak.")

warnings.filterwarnings("ignore")
pd.set_option("display.max_columns", None)
pd.set_option("display.float_format", "{:.4f}".format)
RANDOM_STATE = 42
os.makedirs("figures", exist_ok=True)
plt.rcParams.update({"figure.dpi": 120, "font.size": 11})
sns.set_theme(style="whitegrid", palette="muted")
print("Importlar OK.\n")

BASE = Path(".")

# ── 1. VERİ YÜKLEME ───────────────────────────────────────────────
print("=" * 60)
print("1. VERİ YÜKLEME")
print("=" * 60)

# YouTube yorumları
df_yt_inc = pd.read_csv(BASE / "youtube_urun_incelemeleri.csv", low_memory=False)
df_yt_den = pd.read_csv(BASE / "youtube_deneyim.csv", low_memory=False)
df_video_meta = pd.read_csv(BASE / "youtube_video_meta.csv", parse_dates=["upload_date"])
print(f"YouTube Ürün İncelemeleri : {len(df_yt_inc):,}")
print(f"YouTube Deneyim          : {len(df_yt_den):,}")
print(f"YouTube Video Meta       : {len(df_video_meta):,}")

# Google Play
df_gplay = pd.read_csv(BASE / "yorumlar_google_play.csv", low_memory=False)
print(f"Google Play Yorumları    : {len(df_gplay):,}")

# App Store
df_appstore = pd.read_csv(BASE / "yorumlar_appstore.csv", low_memory=False)
print(f"App Store Yorumları      : {len(df_appstore):,}")

# Reddit / Forum
df_forum = pd.read_csv(BASE / "yorumlar_forumlar.csv", low_memory=False)
print(f"Reddit/Forum             : {len(df_forum):,}")

# Google Trends
df_trends = pd.read_csv(BASE / "google_trends_rayban_meta.csv", parse_dates=["date"])
print(f"Google Trends (haftalık) : {len(df_trends):,}")

# Hisse fiyatları (yfinance multi-header: ilk 2 satır atlanır)
df_meta_stock = pd.read_csv(BASE / "meta_hisse_fiyatlari.csv", skiprows=[1, 2], parse_dates=["Price"])
df_meta_stock = df_meta_stock.rename(columns={"Price": "date", "Close": "meta_close"})
df_meta_stock = df_meta_stock[["date", "meta_close"]].dropna()
df_meta_stock["meta_close"] = pd.to_numeric(df_meta_stock["meta_close"], errors="coerce")
print(f"META Hisse Fiyatları     : {len(df_meta_stock):,}")

df_el_stock = pd.read_csv(BASE / "essilorluxottica_hisse_fiyatlari.csv", skiprows=[1, 2], parse_dates=["Price"])
df_el_stock = df_el_stock.rename(columns={"Price": "date", "Close": "el_close"})
df_el_stock = df_el_stock[["date", "el_close"]].dropna()
df_el_stock["el_close"] = pd.to_numeric(df_el_stock["el_close"], errors="coerce")
print(f"EssilorLuxottica Hisse   : {len(df_el_stock):,}")

# Haberler
df_news = pd.read_csv(BASE / "rayban_meta_global_haberler.csv")
df_news["tarih"] = pd.to_datetime(df_news["tarih"], errors="coerce")
print(f"Haber Olayları           : {len(df_news):,}")

# ── 2. ÖN İŞLEME ─────────────────────────────────────────────────
print("\n" + "=" * 60)
print("2. ÖN İŞLEME")
print("=" * 60)

# YouTube ön işleme
def preprocess_youtube(df, category_label):
    d = df.rename(columns={
        "video_basligi": "video_title", "yorum_metni": "text",
        "begeni_sayisi": "like_count", "yayin_tarihi": "date",
        "tur": "comment_type", "dil": "lang",
    }).copy()
    d["date"] = pd.to_datetime(d["date"], errors="coerce", utc=True).dt.tz_localize(None)
    d["like_count"] = pd.to_numeric(d["like_count"], errors="coerce").fillna(0)
    d.dropna(subset=["text"], inplace=True)
    d = d[d["text"].astype(str).str.len() > 3]
    d = d[d["lang"] == "en"].copy()
    d["platform"] = "youtube"
    d["video_category"] = category_label
    d["rating"] = np.nan
    return d

df_yt_inc = preprocess_youtube(df_yt_inc, "product_review")
df_yt_den = preprocess_youtube(df_yt_den, "lifestyle_experience")
df_yt = pd.concat([df_yt_inc, df_yt_den], ignore_index=True)
print(f"YouTube (EN, temiz)      : {len(df_yt):,}")

# Google Play ön işleme
df_gplay["text"] = df_gplay["yorum_metni"].astype(str)
df_gplay["date"] = pd.to_datetime(df_gplay["tarih"], errors="coerce")
df_gplay["like_count"] = pd.to_numeric(df_gplay["begeni_sayisi"], errors="coerce").fillna(0)
df_gplay["rating"] = pd.to_numeric(df_gplay["puan"], errors="coerce")
df_gplay["platform"] = "google_play"
df_gplay = df_gplay[df_gplay["text"].str.len() > 3].copy()
print(f"Google Play (temiz)      : {len(df_gplay):,}")

# App Store ön işleme
df_appstore["text"] = df_appstore["yorum_metni"].astype(str)
df_appstore["date"] = pd.to_datetime(df_appstore["tarih"], errors="coerce", utc=True)
df_appstore["date"] = df_appstore["date"].dt.tz_localize(None)
df_appstore["like_count"] = 0
df_appstore["rating"] = pd.to_numeric(df_appstore["puan"], errors="coerce")
df_appstore["platform"] = "appstore"
df_appstore = df_appstore[df_appstore["text"].str.len() > 3].copy()
print(f"App Store (temiz)        : {len(df_appstore):,}")

# Reddit ön işleme
df_forum["text"] = df_forum["yorum_metni"].astype(str)
df_forum["date"] = pd.to_datetime(df_forum["tarih_unix"], unit="s", errors="coerce")
df_forum["like_count"] = pd.to_numeric(df_forum["skor"], errors="coerce").fillna(0)
df_forum["rating"] = np.nan
df_forum["platform"] = "reddit"
df_forum = df_forum[df_forum["text"].str.len() > 3].copy()
print(f"Reddit (temiz)           : {len(df_forum):,}")

# ── 3. SENTIMENT SKORLAMA (RoBERTa) ──────────────────────────────
print("\n" + "=" * 60)
print("3. SENTIMENT SKORLAMA (RoBERTa Transformer)")
print("=" * 60)

CACHE_YT = BASE / "cache_youtube_sentiment.csv"
CACHE_REDDIT = BASE / "cache_reddit_sentiment.csv"

def roberta_sentiment(texts, batch_size=32):
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch

    model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    print(f"  Model yükleniyor: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()
    print(f"  Cihaz: {device}")

    scores = []
    labels = []
    total = len(texts)

    for i in range(0, total, batch_size):
        batch = texts[i:i+batch_size]
        batch = [str(t)[:512] for t in batch]  # max 512 token

        encoded = tokenizer(batch, padding=True, truncation=True,
                            max_length=512, return_tensors="pt").to(device)

        with torch.no_grad():
            output = model(**encoded)

        probs = torch.nn.functional.softmax(output.logits, dim=-1).cpu().numpy()
        # sütunlar: negative(0), neutral(1), positive(2)
        for p in probs:
            score = p[2] - p[0]  # positive - negative → [-1, +1]
            scores.append(round(float(score), 4))
            if p[0] > p[1] and p[0] > p[2]:
                labels.append("negative")
            elif p[2] > p[0] and p[2] > p[1]:
                labels.append("positive")
            else:
                labels.append("neutral")

        if (i // batch_size) % 50 == 0:
            print(f"  İlerleme: {min(i+batch_size, total):,}/{total:,} ({min(i+batch_size, total)/total*100:.1f}%)")

    return scores, labels

# YouTube sentiment
if CACHE_YT.exists():
    print("YouTube sentiment cache'ten yükleniyor...")
    cache = pd.read_csv(CACHE_YT)
    df_yt["sentiment_score"] = cache["sentiment_score"].values[:len(df_yt)]
    df_yt["sentiment_label"] = cache["sentiment_label"].values[:len(df_yt)]
    print(f"  Cache'ten {len(df_yt):,} yorum yüklendi.")
else:
    print(f"YouTube yorumları işleniyor ({len(df_yt):,} yorum, bu 1-3 saat sürebilir)...")
    t0 = time.time()
    scores, labels = roberta_sentiment(df_yt["text"].tolist())
    df_yt["sentiment_score"] = scores
    df_yt["sentiment_label"] = labels
    elapsed = time.time() - t0
    print(f"  Tamamlandı: {elapsed/60:.1f} dakika")
    df_yt[["sentiment_score", "sentiment_label"]].to_csv(CACHE_YT, index=False)
    print(f"  Cache kaydedildi: {CACHE_YT}")

# Reddit sentiment
if CACHE_REDDIT.exists():
    print("Reddit sentiment cache'ten yükleniyor...")
    cache_r = pd.read_csv(CACHE_REDDIT)
    df_forum["sentiment_score"] = cache_r["sentiment_score"].values[:len(df_forum)]
    df_forum["sentiment_label"] = cache_r["sentiment_label"].values[:len(df_forum)]
else:
    print(f"Reddit yorumları işleniyor ({len(df_forum):,} yorum)...")
    scores_r, labels_r = roberta_sentiment(df_forum["text"].tolist())
    df_forum["sentiment_score"] = scores_r
    df_forum["sentiment_label"] = labels_r
    df_forum[["sentiment_score", "sentiment_label"]].to_csv(CACHE_REDDIT, index=False)
    print(f"  Cache kaydedildi: {CACHE_REDDIT}")

# Google Play + App Store: yıldız puanından sentiment türet
for df_temp in [df_gplay, df_appstore]:
    df_temp["sentiment_label"] = df_temp["rating"].map(
        lambda r: "negative" if r <= 2 else ("positive" if r >= 4 else "neutral"))
    df_temp["sentiment_score"] = df_temp["rating"].map(
        lambda r: -0.8 if r == 1 else (-0.4 if r == 2 else (0.0 if r == 3 else (0.4 if r == 4 else 0.8))))

print("\nSentiment dağılımı:")
for name, df_tmp in [("YouTube", df_yt), ("Google Play", df_gplay),
                     ("App Store", df_appstore), ("Reddit", df_forum)]:
    counts = df_tmp["sentiment_label"].value_counts()
    print(f"  {name:<12}: pos={counts.get('positive',0):,}  neu={counts.get('neutral',0):,}  neg={counts.get('negative',0):,}")

# ── 4. VERİ HARMANLAMA (5 KATMANLI DATA FUSION) ──────────────────
print("\n" + "=" * 60)
print("4. VERİ HARMANLAMA (5 Katmanlı Data Fusion)")
print("=" * 60)

# Katman 1: Dikey birleştirme — ortak şema
COLS = ["text", "date", "platform", "like_count", "rating",
        "sentiment_score", "sentiment_label"]

yt_cols = df_yt[COLS + ["video_id", "comment_type", "video_category"]].copy()
gp_cols = df_gplay[COLS].copy()
as_cols = df_appstore[COLS].copy()
rd_cols = df_forum[COLS].copy()

for dc in [gp_cols, as_cols, rd_cols]:
    dc["video_id"] = np.nan
    dc["comment_type"] = "ana_yorum"
    dc["video_category"] = np.nan

df = pd.concat([yt_cols, gp_cols, as_cols, rd_cols], ignore_index=True)
df["text"] = df["text"].astype(str).str.strip()
df = df[df["text"].str.len() > 3].copy()
print(f"Katman 1 — Birleşik korpüs: {len(df):,} yorum, {df['platform'].nunique()} platform")
print(f"  Platform dağılımı: {df['platform'].value_counts().to_dict()}")

# Katman 2: Google Trends merge
df_trends = df_trends.sort_values("date")
df_trends.rename(columns={"Ray-Ban Meta": "google_trends_score"}, inplace=True)
df_trends["google_trends_momentum"] = df_trends["google_trends_score"].pct_change().replace([np.inf, -np.inf], 0).fillna(0)

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"])
df = df.sort_values("date")

df = pd.merge_asof(df, df_trends[["date", "google_trends_score", "google_trends_momentum"]],
                   on="date", direction="backward")
print(f"Katman 2 — Google Trends merge: {df['google_trends_score'].notna().sum():,} eşleşme")

# Katman 3: Hisse fiyatı merge
df_meta_stock = df_meta_stock.sort_values("date")
df_meta_stock["meta_stock_change_7d"] = df_meta_stock["meta_close"].pct_change(periods=5).fillna(0) * 100

df = pd.merge_asof(df, df_meta_stock[["date", "meta_close", "meta_stock_change_7d"]],
                   on="date", direction="backward")
print(f"Katman 3 — META hisse merge: {df['meta_close'].notna().sum():,} eşleşme")

df_el_stock = df_el_stock.sort_values("date")
df = pd.merge_asof(df, df_el_stock[["date", "el_close"]],
                   on="date", direction="backward")
print(f"           EssilorLuxottica merge: {df['el_close'].notna().sum():,} eşleşme")

# Katman 4: Haber proximity
news_dates = df_news["tarih"].dropna().values
def nearest_news_days(dt):
    if pd.isna(dt):
        return np.nan
    diffs = np.abs((news_dates - np.datetime64(dt)) / np.timedelta64(1, "D"))
    return float(np.min(diffs))

df["news_event_proximity_days"] = df["date"].apply(nearest_news_days)
print(f"Katman 4 — Haber proximity: medyan {df['news_event_proximity_days'].median():.0f} gün")

# Katman 5: Video meta merge (YouTube kısmı)
meta_cols = df_video_meta[["video_id", "view_count", "like_count", "duration_min",
                            "engagement_rate", "category"]].rename(
    columns={"like_count": "video_like_count", "category": "yt_category"})

df = df.merge(meta_cols, on="video_id", how="left")
yt_matched = df[df["platform"] == "youtube"]["view_count"].notna().sum()
print(f"Katman 5 — Video meta merge: {yt_matched:,} YouTube yorumu eşleşti")

print(f"\nFüzyon sonrası tablo: {df.shape}")

# ── 5. HEDEF DEĞİŞKEN + ÖZELLİK MÜHENDİSLİĞİ ──────────────────
print("\n" + "=" * 60)
print("5. HEDEF DEĞİŞKEN + ÖZELLİK MÜHENDİSLİĞİ")
print("=" * 60)

# Hedef değişken
df["is_negative_risk"] = 0
# Google Play / App Store: yıldız ≤ 2
mask_rated = df["platform"].isin(["google_play", "appstore"])
df.loc[mask_rated, "is_negative_risk"] = (df.loc[mask_rated, "rating"] <= 2).astype(int)
# YouTube / Reddit: RoBERTa negative
mask_unrated = df["platform"].isin(["youtube", "reddit"])
df.loc[mask_unrated, "is_negative_risk"] = (df.loc[mask_unrated, "sentiment_label"] == "negative").astype(int)

print(f"Negatif risk oranı: {df['is_negative_risk'].mean():.2%} ({df['is_negative_risk'].sum():,} yorum)")
print(f"Platform bazlı:")
print(df.groupby("platform")["is_negative_risk"].agg(["mean", "sum", "count"]).round(4))

# Özellik mühendisliği
df["word_count"] = df["text"].str.split().str.len()
df["engagement_score"] = np.log1p(df["like_count"])
df["is_reply"] = (df["comment_type"] == "yanit").astype(int)
df["comment_engagement_ratio"] = df["like_count"] / df["view_count"].replace(0, np.nan)
df["comment_engagement_ratio"] = df["comment_engagement_ratio"].fillna(0)

# Haftalık platform bazlı negatif oran (1 hafta lag)
df["week"] = df["date"].dt.to_period("W")
weekly_neg = (df.groupby(["week", "platform"])["is_negative_risk"]
              .mean().reset_index(name="weekly_platform_neg_rate"))
weekly_neg = weekly_neg.sort_values("week")
weekly_neg["weekly_platform_neg_rate"] = (weekly_neg.groupby("platform")["weekly_platform_neg_rate"]
                                          .shift(1).fillna(0))
df = df.merge(weekly_neg, on=["week", "platform"], how="left")
df["weekly_platform_neg_rate"] = df["weekly_platform_neg_rate"].fillna(0)

# Platform encoding
df["platform_enc"] = LabelEncoder().fit_transform(df["platform"])

# YouTube kategorisi encoding
df["yt_cat_enc"] = LabelEncoder().fit_transform(df["yt_category"].fillna("unknown"))

print("\nTüretilen özellikler:")
feat_desc = [
    ("word_count", "Kelime sayısı"),
    ("engagement_score", "log(1 + beğeni)"),
    ("weekly_platform_neg_rate", "Haftalık platform negatif oran (1 hafta lag)"),
    ("google_trends_score", "Google Trends arama ilgisi"),
    ("google_trends_momentum", "Trends değişim hızı"),
    ("meta_stock_change_7d", "META hisse 5-gün değişim (%)"),
    ("news_event_proximity_days", "En yakın habere uzaklık (gün)"),
    ("platform_enc", "Platform türü"),
    ("is_reply", "Yanıt mı (YouTube)"),
    ("comment_engagement_ratio", "Beğeni / video izlenme (füzyon)"),
    ("yt_cat_enc", "YouTube kategorisi"),
]
for feat, desc in feat_desc:
    print(f"  {feat:<30}: {desc}")

# ── 6. EDA GÖRSELLERİ ────────────────────────────────────────────
print("\n" + "=" * 60)
print("6. EDA GÖRSELLERİ")
print("=" * 60)

# Fig 01 — Platform dağılımı
fig, axes = plt.subplots(1, 2, figsize=(13, 4))
colors_plat = ["#4C72B0", "#DD8452", "#55A868", "#C44E52"]
df["platform"].value_counts().plot(kind="bar", ax=axes[0], color=colors_plat, edgecolor="white")
axes[0].set_title("Platform Başına Yorum Sayısı")
axes[0].set_ylabel("Yorum Sayısı"); axes[0].tick_params(axis="x", rotation=15)

df.groupby("platform")["is_negative_risk"].mean().plot(
    kind="bar", ax=axes[1], color=colors_plat, edgecolor="white")
axes[1].set_title("Platform Başına Negatif Risk Oranı")
axes[1].set_ylabel("Oran"); axes[1].tick_params(axis="x", rotation=15)
plt.tight_layout()
plt.savefig("figures/fig_01_platform_dist.png", bbox_inches="tight"); plt.close()
print("  fig_01 OK")

# Fig 02 — Aylık yorum hacmi
df["month"] = df["date"].dt.to_period("M")
monthly = df.groupby(["month", "platform"]).size().unstack(fill_value=0).reset_index()
monthly["month_str"] = monthly["month"].astype(str)
fig, ax = plt.subplots(figsize=(14, 4))
for col, color in zip(["youtube", "google_play", "appstore", "reddit"], colors_plat):
    if col in monthly.columns:
        ax.plot(monthly["month_str"], monthly[col], marker="o", label=col, color=color, markersize=3)
ax.set_title("Aylık Yorum Hacmi — Platform Bazlı")
ax.set_xlabel("Ay"); ax.set_ylabel("Yorum Sayısı"); ax.legend()
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig("figures/fig_02_monthly_volume.png", bbox_inches="tight"); plt.close()
print("  fig_02 OK")

# Fig 03 — Duygu dağılımı
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
for plat, color in zip(["youtube", "google_play", "appstore"], colors_plat[:3]):
    sub = df[df["platform"] == plat]["sentiment_score"].dropna()
    if len(sub) > 0:
        axes[0].hist(sub, bins=50, alpha=0.5, label=plat, color=color)
axes[0].axvline(0, color="red", ls="--", lw=1.2)
axes[0].set_title("Sentiment Skor Dağılımı (Platform Bazlı)")
axes[0].set_xlabel("Sentiment Skoru"); axes[0].legend()

sent_counts = df.groupby(["platform", "sentiment_label"]).size().unstack(fill_value=0)
sent_counts.plot(kind="bar", ax=axes[1], edgecolor="white")
axes[1].set_title("Sentiment Etiket Dağılımı")
axes[1].tick_params(axis="x", rotation=15)
plt.tight_layout()
plt.savefig("figures/fig_03_sentiment_dist.png", bbox_inches="tight"); plt.close()
print("  fig_03 OK")

# Fig 04 — Kelime bulutu
stops = STOPWORDS | {"See", "more", "see", "http", "https", "com", "www",
                     "Ray", "Ban", "Meta", "glasses", "app", "one", "will", "just", "like"}
all_text = " ".join(df["text"].dropna().sample(min(20000, len(df)), random_state=42))
wc = WordCloud(width=1100, height=420, background_color="white",
               stopwords=stops, colormap="Blues", max_words=160).generate(all_text)
fig, ax = plt.subplots(figsize=(13, 5))
ax.imshow(wc, interpolation="bilinear"); ax.axis("off")
ax.set_title("Kelime Bulutu — Tüm Platformlar")
plt.tight_layout()
plt.savefig("figures/fig_04_wordcloud.png", bbox_inches="tight"); plt.close()
print("  fig_04 OK")

# Fig 05 — Google Trends + haftalık sentiment overlay
weekly_sent = (df.groupby(df["date"].dt.to_period("W"))
               .agg(neg_rate=("is_negative_risk", "mean"),
                    trends=("google_trends_score", "mean"),
                    count=("text", "count"))
               .reset_index())
weekly_sent["date_str"] = weekly_sent["date"].astype(str)

fig, ax1 = plt.subplots(figsize=(14, 5))
ax1.bar(range(len(weekly_sent)), weekly_sent["neg_rate"], color="#C44E52", alpha=0.4, label="Negatif Risk Oranı")
ax1.set_ylabel("Negatif Risk Oranı", color="#C44E52")
ax2 = ax1.twinx()
ax2.plot(range(len(weekly_sent)), weekly_sent["trends"], color="#4C72B0", lw=2, label="Google Trends")
ax2.set_ylabel("Google Trends Skoru", color="#4C72B0")
ax1.set_title("Haftalık Negatif Risk vs Google Trends Arama İlgisi")
ax1.set_xticks(range(0, len(weekly_sent), max(1, len(weekly_sent)//10)))
ax1.set_xticklabels(weekly_sent["date_str"].iloc[::max(1, len(weekly_sent)//10)], rotation=45, ha="right")
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
plt.tight_layout()
plt.savefig("figures/fig_05_trends_sentiment.png", bbox_inches="tight"); plt.close()
print("  fig_05 OK")

# Fig 06 — Korelasyon matrisi
feature_cols = [
    "word_count", "engagement_score", "weekly_platform_neg_rate",
    "google_trends_score", "google_trends_momentum", "meta_stock_change_7d",
    "news_event_proximity_days", "platform_enc", "is_reply",
    "comment_engagement_ratio", "yt_cat_enc", "is_negative_risk",
]
fig, ax = plt.subplots(figsize=(10, 8))
corr = df[feature_cols].corr()
sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, linewidths=0.4, ax=ax)
ax.set_title("Özellik Korelasyon Matrisi")
plt.tight_layout()
plt.savefig("figures/fig_06_correlation.png", bbox_inches="tight"); plt.close()
print("  fig_06 OK")

# ── 7. MODELLEMEs ─────────────────────────────────────────────────
print("\n" + "=" * 60)
print("7. TAHMİNSEL MODELLEME")
print("=" * 60)

FEATURES = [
    "word_count", "engagement_score", "weekly_platform_neg_rate",
    "google_trends_score", "google_trends_momentum", "meta_stock_change_7d",
    "news_event_proximity_days", "platform_enc", "is_reply",
    "comment_engagement_ratio", "yt_cat_enc",
]

X = df[FEATURES].fillna(0).replace([np.inf, -np.inf], 0)
y = df["is_negative_risk"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y)

print(f"Özellikler  : {FEATURES}")
print(f"Eğitim seti : {X_train.shape[0]:,} | Test seti: {X_test.shape[0]:,}")
print(f"Negatif oran: eğitim {y_train.mean():.2%} | test {y_test.mean():.2%}")

models = {
    "Logistic Regression": Pipeline([
        ("sc", StandardScaler()),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE))
    ]),
    "Random Forest": RandomForestClassifier(
        n_estimators=200, max_depth=10, min_samples_leaf=10,
        class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1),
    "Gradient Boosting": GradientBoostingClassifier(
        n_estimators=200, max_depth=5, learning_rate=0.1, random_state=RANDOM_STATE),
}
if HAS_XGB:
    neg_count = y_train.sum()
    pos_count = len(y_train) - neg_count
    models["XGBoost"] = XGBClassifier(
        n_estimators=200, max_depth=5, learning_rate=0.1,
        scale_pos_weight=pos_count / max(neg_count, 1),
        random_state=RANDOM_STATE, n_jobs=-1, eval_metric="logloss", verbosity=0)

results = {}
print("\nModel eğitimi:")
for name, model in models.items():
    cv_auc = cross_val_score(model, X_train, y_train, cv=5, scoring="roc_auc", n_jobs=-1)
    model.fit(X_train, y_train)
    y_prob = model.predict_proba(X_test)[:, 1]
    test_auc = roc_auc_score(y_test, y_prob)
    results[name] = {
        "model": model, "cv_auc": cv_auc.mean(), "test_auc": test_auc,
        "y_pred": model.predict(X_test), "y_prob": y_prob
    }
    print(f"  {name:<25} CV AUC={cv_auc.mean():.4f} (±{cv_auc.std():.4f}) | Test AUC={test_auc:.4f}")

best_name = max(results, key=lambda n: results[n]["test_auc"])
best = results[best_name]
print(f"\nEn iyi model: {best_name} (Test AUC = {best['test_auc']:.4f})")
print(classification_report(y_test, best["y_pred"], target_names=["normal", "negatif_risk"]))

# Eşik optimizasyonu
precisions, recalls, thresholds = precision_recall_curve(y_test, best["y_prob"])
f1s = 2 * precisions * recalls / (precisions + recalls + 1e-9)
bi = np.argmax(f1s[:-1])
best_thresh = thresholds[bi]
print(f"Optimal eşik: {best_thresh:.3f}  P={precisions[bi]:.3f}  R={recalls[bi]:.3f}  F1={f1s[bi]:.3f}")

# Fig 07 — ROC + Confusion Matrix
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
for name, res in results.items():
    RocCurveDisplay.from_predictions(y_test, res["y_prob"], name=name, ax=axes[0])
axes[0].plot([0, 1], [0, 1], "--", color="gray")
axes[0].set_title("ROC Eğrileri — Tüm Modeller")

y_pred_opt = (best["y_prob"] >= best_thresh).astype(int)
ConfusionMatrixDisplay(
    confusion_matrix(y_test, y_pred_opt),
    display_labels=["Normal", "Negatif Risk"]
).plot(ax=axes[1], colorbar=False)
axes[1].set_title(f"Karmaşıklık Matrisi — {best_name}")
plt.tight_layout()
plt.savefig("figures/fig_07_model_eval.png", bbox_inches="tight"); plt.close()
print("  fig_07 OK")

# Fig 08 — Threshold analizi
fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(thresholds, precisions[:-1], label="Precision", color="#2196F3")
ax.plot(thresholds, recalls[:-1], label="Recall", color="#FF5722")
ax.plot(thresholds, f1s[:-1], label="F1 Skoru", color="#4CAF50", ls="--")
ax.axvline(best_thresh, color="red", ls=":", label=f"Optimal = {best_thresh:.2f}")
ax.set_title("Precision / Recall / F1 — Karar Eşiğine Göre")
ax.set_xlabel("Eşik Değeri"); ax.legend()
plt.tight_layout()
plt.savefig("figures/fig_08_threshold.png", bbox_inches="tight"); plt.close()
print("  fig_08 OK")

# ── 8. SHAP AÇIKLANABILIRLIK ──────────────────────────────────────
print("\n" + "=" * 60)
print("8. SHAP AÇIKLANABILIRLIK (XAI)")
print("=" * 60)

_m = best["model"]
if hasattr(_m, "named_steps"):
    clf_s = _m.named_steps["clf"]
    Xt = _m[:-1].transform(X_test)
else:
    clf_s = _m
    Xt = X_test.values

if hasattr(clf_s, "estimators_") or hasattr(clf_s, "get_booster", None):
    explainer = shap.TreeExplainer(clf_s)
else:
    explainer = shap.LinearExplainer(clf_s, Xt)

shap_values = explainer.shap_values(Xt)

if isinstance(shap_values, list):
    sv = np.array(shap_values[1])
elif hasattr(shap_values, "ndim") and shap_values.ndim == 3:
    sv = shap_values[:, :, 1]
else:
    sv = np.array(shap_values)

# Fig 09 — SHAP
fig, axes = plt.subplots(1, 2, figsize=(16, 5))

plt.sca(axes[0])
shap.summary_plot(sv, Xt, feature_names=FEATURES, show=False, plot_size=None)
axes[0].set_title("SHAP Özet — Negatif Risk Tahminine Etki")

plt.sca(axes[1])
shap.summary_plot(sv, Xt, feature_names=FEATURES, plot_type="bar", show=False, plot_size=None)
axes[1].set_title("SHAP Özellik Önem Sıralaması")

plt.tight_layout()
plt.savefig("figures/fig_09_shap.png", bbox_inches="tight"); plt.close()
print("  fig_09 OK")

mean_shap = np.abs(sv).mean(axis=0)
if mean_shap.ndim > 1:
    mean_shap = mean_shap.mean(axis=-1)
print("\nSHAP önem sırası:")
for feat, imp in sorted(zip(FEATURES, mean_shap.tolist()), key=lambda x: -x[1]):
    print(f"  {feat:<30}: {imp:.4f}")

# ── 9. FİNANSAL SİMÜLASYON ──────────────────────────────────────
print("\n" + "=" * 60)
print("9. MALİYET / FAYDA FİNANSAL SİMÜLASYON")
print("=" * 60)

URUN_FIYATI_CLV = 379
MUDAHALE_MALIYET = 20
KURTARMA_ORANI = 0.30
MODEL_PRECISION = float(precisions[bi])

date_range_months = max(1, (df["date"].max() - df["date"].min()).days / 30)
AYLIK_YORUM = int(len(df) / date_range_months)
NEG_RISK_ORANI = df["is_negative_risk"].mean()
AYLIK_NEG = int(AYLIK_YORUM * NEG_RISK_ORANI)

print(f"Aylık yorum hacmi   : {AYLIK_YORUM:,}")
print(f"Negatif risk oranı  : {NEG_RISK_ORANI:.2%}")
print(f"Model precision     : {MODEL_PRECISION:.3f}")

senaryolar = []
for carpan, etiket in [(0.5, "Kötümser"), (1.0, "Temel Senaryo"), (2.0, "İyimser")]:
    n_neg = int(AYLIK_NEG * carpan)
    n_flag = int(n_neg / max(MODEL_PRECISION, 0.01))
    n_tp = int(n_flag * MODEL_PRECISION)
    n_kur = int(n_tp * KURTARMA_ORANI)
    gelir = n_kur * URUN_FIYATI_CLV
    maliyet = n_flag * MUDAHALE_MALIYET
    net = gelir - maliyet
    roi = round(net / max(maliyet, 1) * 100, 1)
    senaryolar.append({
        "Senaryo": etiket, "Negatif Riskli": n_neg, "Müdahale Edilen": n_flag,
        "Kurtarılan": n_kur, "Gelir ($)": gelir, "Maliyet ($)": maliyet,
        "Net Kazanç ($)": net, "ROI (%)": roi,
    })

sim = pd.DataFrame(senaryolar)
print(sim.to_string(index=False))

# Fig 10 — Finansal simülasyon
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
renkler = ["#e74c3c", "#3498db", "#2ecc71"]

bars0 = axes[0].bar(sim["Senaryo"], sim["Net Kazanç ($)"] / 1000, color=renkler, edgecolor="white")
axes[0].set_title("Aylık Net Kazanç ($K)"); axes[0].set_ylabel("$K")
for bar, v in zip(bars0, sim["Net Kazanç ($)"]):
    axes[0].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                 f"${v/1000:.0f}K", ha="center", fontsize=10)

bars1 = axes[1].bar(sim["Senaryo"], sim["ROI (%)"], color=renkler, edgecolor="white")
axes[1].axhline(0, color="black", lw=0.8)
axes[1].set_title("Yatırım Getirisi — ROI (%)"); axes[1].set_ylabel("ROI %")
for bar, v in zip(bars1, sim["ROI (%)"]):
    axes[1].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 3,
                 f"{v:.0f}%", ha="center", fontsize=10)

plt.suptitle("Finansal Simülasyon — ML ile Proaktif Marka Risk Yönetimi", fontweight="bold")
plt.tight_layout()
plt.savefig("figures/fig_10_financial.png", bbox_inches="tight"); plt.close()
print("  fig_10 OK")

# ── 10. METRİKLERİ KAYDET ────────────────────────────────────────
base_scenario = sim[sim["Senaryo"] == "Temel Senaryo"].iloc[0]

metrics = {
    "toplam_satir": int(len(df)),
    "youtube_satir": int((df["platform"] == "youtube").sum()),
    "google_play_satir": int((df["platform"] == "google_play").sum()),
    "appstore_satir": int((df["platform"] == "appstore").sum()),
    "reddit_satir": int((df["platform"] == "reddit").sum()),
    "platform_sayisi": int(df["platform"].nunique()),
    "negatif_risk_orani": round(float(df["is_negative_risk"].mean()), 4),
    "en_iyi_model": best_name,
    "en_iyi_auc": round(float(best["test_auc"]), 4),
    "cv_auc": round(float(best["cv_auc"]), 4),
    "precision_opt": round(float(precisions[bi]), 4),
    "recall_opt": round(float(recalls[bi]), 4),
    "f1_opt": round(float(f1s[bi]), 4),
    "optimal_esik": round(float(best_thresh), 3),
    "feature_sayisi": len(FEATURES),
    "sim_temel_net": int(base_scenario["Net Kazanç ($)"]),
    "sim_temel_roi": float(base_scenario["ROI (%)"]),
    "sentiment_model": "cardiffnlp/twitter-roberta-base-sentiment-latest",
    "veri_kaynaklari": ["YouTube", "Google Play", "App Store", "Reddit",
                        "Google Trends", "META Hisse", "EssilorLuxottica Hisse", "Haber Olayları"],
}

with open("figures/metrics.json", "w", encoding="utf-8") as f:
    json.dump(metrics, f, ensure_ascii=False, indent=2)

print("\nmetrics.json kaydedildi:")
for k, v in metrics.items():
    if isinstance(v, list):
        print(f"  {k:<22}: {', '.join(v)}")
    else:
        print(f"  {k:<22}: {v}")

print("\n" + "=" * 60)
print("TAMAMLANDI")
print(f"Görseller: figures/ ({len(list(Path('figures').glob('fig_*.png')))} adet)")
print(f"Metrikler: figures/metrics.json")
print(f"PDF için : python build_report.py")
print("=" * 60)
