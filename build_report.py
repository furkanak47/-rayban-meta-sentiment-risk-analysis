"""
Yönetici Özeti Raporu (PDF) — Ray-Ban Meta Çoklu Platform Marka Risk Tahmini
Çalıştır: python build_report.py  (main.py çalıştırıldıktan sonra)
"""
import json
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, Image, PageBreak, HRFlowable)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT_DIR = r"C:\Windows\Fonts"
pdfmetrics.registerFont(TTFont("Arial", f"{FONT_DIR}\\arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", f"{FONT_DIR}\\arialbd.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Italic", f"{FONT_DIR}\\ariali.ttf"))
pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-Bold", italic="Arial-Italic")

M = json.load(open("figures/metrics.json", encoding="utf-8"))

ss = getSampleStyleSheet()
for name in ss.byName:
    ss[name].fontName = "Arial"

ss.add(ParagraphStyle("RTitle", parent=ss["Title"], fontName="Arial-Bold", fontSize=16,
                       spaceAfter=4, textColor=colors.HexColor("#1a1a2e")))
ss.add(ParagraphStyle("RSub", parent=ss["Normal"], fontName="Arial", fontSize=9.5,
                       alignment=TA_CENTER, textColor=colors.HexColor("#555")))
ss.add(ParagraphStyle("H1", parent=ss["Heading1"], fontName="Arial-Bold", fontSize=12.5,
                       spaceBefore=10, spaceAfter=5, textColor=colors.HexColor("#1a1a2e")))
ss.add(ParagraphStyle("H2", parent=ss["Heading2"], fontName="Arial-Bold", fontSize=10.5,
                       spaceBefore=6, spaceAfter=3, textColor=colors.HexColor("#16213e")))
ss.add(ParagraphStyle("Body", parent=ss["Normal"], fontName="Arial", fontSize=9,
                       leading=13, alignment=TA_JUSTIFY, spaceAfter=4))
ss.add(ParagraphStyle("RBullet", parent=ss["Normal"], fontName="Arial", fontSize=9,
                       leading=12.5, leftIndent=12, spaceAfter=2))
ss.add(ParagraphStyle("Caption", parent=ss["Normal"], fontName="Arial-Italic", fontSize=8,
                       alignment=TA_CENTER, textColor=colors.HexColor("#777"),
                       spaceBefore=2, spaceAfter=6))

TBL_HEAD = colors.HexColor("#1a1a2e")
TBL_ALT = colors.HexColor("#f2f2f7")

def styled_table(data, col_widths=None, font_size=8):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), TBL_HEAD),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Arial"),
        ("FONTNAME", (0, 0), (-1, 0), "Arial-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, TBL_ALT]),
    ]
    t.setStyle(TableStyle(style))
    return t

def hr():
    return HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc"),
                      spaceBefore=3, spaceAfter=6)

doc = SimpleDocTemplate("Yonetici_Ozeti_Raporu.pdf", pagesize=A4,
                        topMargin=1.5*cm, bottomMargin=1.5*cm,
                        leftMargin=1.7*cm, rightMargin=1.7*cm,
                        title="Ray-Ban Meta — Çoklu Platform Marka Risk Tahmini")

S = []

# ═══════════════════════ SAYFA 1 ═══════════════════════
S.append(Paragraph("Ray-Ban Meta Smart Glasses — Çoklu Platform Marka Risk Tahmini", ss["RTitle"]))
S.append(Paragraph("Yönetici Özeti Raporu &nbsp;|&nbsp; YBS Python ile Veri Bilimi Final Projesi", ss["RSub"]))
S.append(Paragraph("132230044 — Furkan Akdemir &nbsp;|&nbsp; Tema 1: Yapılandırılmış &amp; Yapılandırılmamış Veri ile Risk Tahmini", ss["RSub"]))
S.append(Spacer(1, 6))
S.append(hr())

S.append(Paragraph("1. Problem ve İş Sorusu", ss["H1"]))
S.append(Paragraph(
    "Ray-Ban Meta Smart Glasses, 2023 lansmanından bu yana YouTube, uygulama mağazaları ve "
    "sosyal medyada yoğun tartışma üretti. 2025 sonunda 7 milyon+ adet satışa ulaşırken, "
    "gizlilik skandalları, okulda yasaklanma ve toplu davalar gibi olumsuz gelişmeler de "
    "marka itibarını tehdit ediyor. PR/CX ekiplerinin farklı platformlardaki binlerce yorumu "
    "manuel taraması hem yavaş hem maliyetlidir.", ss["Body"]))
S.append(Paragraph(
    "<b>İş sorusu:</b> YouTube, Google Play, App Store ve Reddit verilerini yapılandırılmış "
    "pazar verileriyle (Google Trends, hisse fiyatı, haber olayları) birleştirerek, negatif "
    "duygu riskini <i>yapısal sinyallerden</i> önceden tahmin edebilir miyiz? Bu sayede CX "
    "ekibi sınırlı kapasitesini en riskli içeriklere yönlendirebilir.", ss["Body"]))

S.append(Paragraph("2. Veri Kaynakları ve Harmanlama", ss["H1"]))
S.append(Paragraph(
    "Proje, <b>8 farklı veri kaynağını 5 katmanlı füzyon</b> stratejisiyle birleştirir — "
    "Tema 1'in gerektirdiği yapılandırılmış↔yapılandırılmamış karma modeli uygular:", ss["Body"]))

src_data = [
    ["#", "Kaynak", "Tür", "Hacim"],
    ["1", "YouTube — Ürün İncelemeleri + Deneyim", "Yapılandırılmamış (metin)", f"{M.get('youtube_satir', 0):,} yorum"],
    ["2", "Google Play — Meta AI App", "Yapılandırılmamış + yıldız puanı", f"{M.get('google_play_satir', 0):,} yorum"],
    ["3", "App Store — Meta AI App (22 ülke)", "Yapılandırılmamış + yıldız puanı", f"{M.get('appstore_satir', 0):,} yorum"],
    ["4", "Reddit / Forum", "Yapılandırılmamış (metin)", f"{M.get('reddit_satir', 0):,} gönderi"],
    ["5", "Google Trends", "Yapılandırılmış (zaman serisi)", "182 hafta"],
    ["6", "META + EssilorLuxottica Hisse", "Yapılandırılmış (günlük)", "~1.750 gün"],
    ["7", "Global Haber Olayları", "Yapılandırılmış (olay)", "40 haber"],
    ["8", "YouTube Video Performans Meta", "Yapılandırılmış (tablo)", "7 video × 9 sütun"],
]
S.append(styled_table(src_data, col_widths=[0.7*cm, 4.2*cm, 3.8*cm, 3.7*cm]))
S.append(Paragraph(
    f"<b>Toplam:</b> {M.get('toplam_satir', 0):,} yorum/gönderi, "
    f"{M.get('platform_sayisi', 4)} platform, 8 veri kaynağı. "
    "Sentiment analizi için <b>RoBERTa transformer</b> modeli kullanıldı "
    f"(<font face='Courier' size='7.5'>{M.get('sentiment_model', '')}</font>).", ss["Body"]))

S.append(PageBreak())

# ═══════════════════════ SAYFA 2 ═══════════════════════
S.append(Paragraph("3. Özellik Mühendisliği ve Data Fusion", ss["H1"]))
S.append(Paragraph(
    "Ham sütunlar dışında <b>11 yeni değişken</b> türetildi. Bunlardan dördü doğrudan "
    "füzyonun ürünüdür — yalnızca tek kaynak kullansaydık hesaplanamazdı:", ss["Body"]))

feat_data = [
    ["Özellik", "Türetim", "İş Gerekçesi"],
    ["word_count", "len(text.split())", "Uzun yorum → güçlü görüş"],
    ["engagement_score", "log(1 + beğeni)", "Viral ağırlık"],
    ["weekly_platform_neg_rate", "Haftalık neg. oran (1-hafta lag)", "Erken uyarı KPI"],
    ["google_trends_score •", "Haftalık arama ilgisi", "[Füzyon] Talep sinyali"],
    ["google_trends_momentum •", "Trends değişim hızı", "[Füzyon] Trend ivmesi"],
    ["meta_stock_change_7d •", "META hisse 5-gün değişimi", "[Füzyon] Şirket momentumu"],
    ["news_event_proximity •", "En yakın habere uzaklık (gün)", "[Füzyon] Haber etkisi"],
    ["platform_enc", "Platform türü (4 kategori)", "Risk profili farkı"],
    ["is_reply", "Yanıt mı ana yorum mu", "Reaktif/duygusal eğilim"],
    ["comment_engagement_ratio", "Beğeni ÷ video izlenme", "[Füzyon] Normalize etki"],
    ["yt_cat_enc", "YouTube kategorisi", "[Füzyon] Video bağlamı"],
]
S.append(styled_table(feat_data, col_widths=[4.2*cm, 4.0*cm, 5.5*cm]))
S.append(Paragraph(
    "• Yapılandırılmış↔yapılandırılmamış füzyonun doğrudan ürünü.<br/>"
    "<b>Hedef değişken:</b> Google Play/App Store: yıldız ≤ 2 → negatif risk; "
    "YouTube/Reddit: RoBERTa sentiment = negative → negatif risk. "
    f"Oran: <b>%{M.get('negatif_risk_orani', 0)*100:.1f}</b>. "
    "<b>Sızıntı önlemi:</b> sentiment_score özellik setine dahil edilmez.", ss["Body"]))

S.append(Spacer(1, 6))
try:
    S.append(Image("figures/fig_05_trends_sentiment.png", width=14.5*cm, height=14.5*cm*4.5/14))
    S.append(Paragraph("Şekil 1 — Haftalık Negatif Risk Oranı vs Google Trends Arama İlgisi", ss["Caption"]))
except:
    pass

S.append(PageBreak())

# ═══════════════════════ SAYFA 3 ═══════════════════════
S.append(Paragraph("4. Model Performansı ve Açıklanabilirlik (XAI)", ss["H1"]))
S.append(Paragraph(
    "Logistic Regression, Random Forest, Gradient Boosting ve XGBoost modelleri "
    "5-katlı çapraz doğrulama ile karşılaştırıldı. En iyi sonucu "
    f"<b>{M.get('en_iyi_model', '')}</b> verdi:", ss["Body"]))

mdl_data = [
    ["Metrik", "Değer", "Yorum"],
    ["Test AUC", f"{M.get('en_iyi_auc', 0):.3f}", "Platformlar arası ayrım gücü"],
    ["CV AUC", f"{M.get('cv_auc', 0):.3f}", "5-katlı çapraz doğrulama ortalaması"],
    ["Optimal Eşik", f"{M.get('optimal_esik', 0):.3f}", "F1-maksimize edici karar sınırı"],
    ["Precision", f"{M.get('precision_opt', 0):.3f}", "İşaretlenenlerin gerçek negatif oranı"],
    ["Recall", f"{M.get('recall_opt', 0):.3f}", "Yakalanan negatif yorum oranı"],
    ["F1-Skoru", f"{M.get('f1_opt', 0):.3f}", "Precision/Recall dengesi"],
]
S.append(styled_table(mdl_data, col_widths=[3.5*cm, 2.5*cm, 7.7*cm]))

S.append(Paragraph("SHAP Bulguları", ss["H2"]))
S.append(Paragraph(
    "SHAP analizi, modelin kararlarını şeffaflaştırır. Füzyon-türevi özellikler "
    "(Google Trends, hisse fiyatı, haber proximity) modelde ölçülebilir katkı sağladı — "
    "bu, çoklu kaynak birleştirmenin yalnızca teorik değil, <b>kanıtlanmış</b> bir değer "
    "yarattığını gösterir.", ss["Body"]))

try:
    S.append(Image("figures/fig_09_shap.png", width=15.5*cm, height=15.5*cm*5/16))
    S.append(Paragraph("Şekil 2 — SHAP Özellik Önem Sıralaması ve Etki Yönü", ss["Caption"]))
except:
    pass

S.append(PageBreak())

# ═══════════════════════ SAYFA 4 ═══════════════════════
S.append(Paragraph("5. Maliyet / Fayda Finansal Simülasyonu", ss["H1"]))
S.append(Paragraph(
    "<b>İş sorusu:</b> \"Meta'nın CX ekibi, modeli kullanarak çoklu platformdaki negatif-riskli "
    "yorumları otomatik önceliklendirip 24 saat içinde proaktif yanıt verirse, aylık net "
    "finansal kazanç ne olur?\"", ss["Body"]))
S.append(Paragraph(
    f"<b>Varsayımlar:</b> Ürün fiyatı + CLV = 379 $; müdahale maliyeti = 20 $/yorum; "
    f"kurtarma oranı = %30; model precision = {M.get('precision_opt', 0):.2f}.", ss["Body"]))
sim_data = [
    ["Senaryo", "Negatif Riskli\nYorum/Ay", "Müdahale\nEdilen", "Kurtarılan\nMüşteri",
     "Korunan\nGelir ($)", "Müdahale\nMaliyeti ($)", "Net\nKazanç ($)", "ROI\n(%)"],
    ["Kötümser (0.5×)", "206", "317", "61", "23,119", "6,340", "16,779", "265"],
    ["Temel Senaryo", "412", "635", "123", "46,617", "12,700",
     f"{M.get('sim_temel_net', 0):,}", f"{M.get('sim_temel_roi', 0):.0f}"],
    ["İyimser (2×)", "824", "1,270", "246", "93,234", "25,400", "67,834", "267"],
]
S.append(styled_table(sim_data, col_widths=[2.3*cm, 1.8*cm, 1.6*cm, 1.6*cm, 1.8*cm, 1.8*cm, 1.7*cm, 1.1*cm], font_size=7.5))
S.append(Spacer(1, 4))
S.append(Paragraph(
    f"<b>Temel senaryo özeti:</b> Ayda <b>{M.get('sim_temel_net', 0):,} $ net kazanç</b>, "
    f"<b>%{M.get('sim_temel_roi', 0):.0f} ROI</b> — harcanan her 1 $'a karşılık "
    f"{1 + M.get('sim_temel_roi', 0)/100:.1f} $ değerinde gelir korunuyor. Kötümser "
    "senaryoda dahi yatırım kendini fazlasıyla amorti ediyor.", ss["Body"]))

try:
    S.append(Image("figures/fig_10_financial.png", width=15.5*cm, height=15.5*cm*5/13))
    S.append(Paragraph("Şekil 3 — 3 Senaryolu Finansal Simülasyon: Net Kazanç ve ROI", ss["Caption"]))
except:
    pass

S.append(PageBreak())

# ═══════════════════════ SAYFA 5 ═══════════════════════
S.append(Paragraph("6. Sonuç ve Stratejik Öneriler", ss["H1"]))

S.append(Paragraph("Temel Bulgular", ss["H2"]))
for b in [
    f"<b>Çoklu platform füzyonu kanıtlandı:</b> 8 farklı kaynak 5 katmanlı birleştirme ile "
    f"tek bir risk tahmin modeline dönüştürüldü. Toplam <b>{M.get('toplam_satir', 0):,}</b> "
    "gerçek veri noktası — sentetik veri kullanılmadı.",
    f"<b>Transformer-tabanlı sentiment:</b> YouTube ve Reddit yorumları için RoBERTa modeli, "
    "Google Play ve App Store için gerçek yıldız puanları kullanıldı — hibrit etiketleme "
    "stratejisi ile güçlü ground truth elde edildi.",
    f"<b>Model performansı:</b> {M.get('en_iyi_model', '')} modeli, "
    f"<b>AUC = {M.get('en_iyi_auc', 0):.2f}</b> ile platformlar arası negatif riski "
    "başarıyla ayırt ediyor.",
    f"<b>Finansal etki:</b> Temel senaryoda proaktif ML-destekli müdahale "
    f"<b>{M.get('sim_temel_net', 0):,} $ aylık net kazanç</b> "
    f"(<b>%{M.get('sim_temel_roi', 0):.0f} ROI</b>) sağlıyor.",
]:
    S.append(Paragraph(f"• {b}", ss["RBullet"]))

S.append(Paragraph("Stratejik Öneriler", ss["H2"]))
for b in [
    "<b>Acil:</b> Modeli çoklu platform gerçek-zamanlı izleme hattına entegre edin — "
    "YouTube, Google Play ve App Store'dan gelen negatif sinyalleri 24 saat içinde "
    "önceliklendirin.",
    "<b>Kısa vadeli:</b> Google Trends momentum ve haber proximity sinyallerini "
    "yönetici KPI panosuna ekleyin — arama ilgisi zirveleri ile negatif dalgalar "
    "arasındaki korelasyonu izleyin.",
    "<b>Orta vadeli:</b> Platform bazlı farklılaştırılmış müdahale stratejisi kurun — "
    "uygulama mağazası yorumları (düşük yıldız) ile YouTube yorumları farklı risk "
    "dinamikleri sergiliyor.",
    "<b>Uzun vadeli:</b> Modeli yeni ürün lansmanlarına (Gen 3, Oakley Meta) genelleyin "
    "ve hisse fiyatı + Google Trends verilerini canlı besleyerek füzyon hattını "
    "güncel tutun.",
]:
    S.append(Paragraph(f"• {b}", ss["RBullet"]))

S.append(Spacer(1, 8))
S.append(hr())
S.append(Paragraph(
    "Bu rapor, <i>main.py</i> pipeline'ında belgelenen tam analiz hattının "
    "(veri harmanlama → RoBERTa sentiment → özellik mühendisliği → modelleme → "
    "SHAP → finansal simülasyon) yönetici düzeyinde özetidir.", ss["Caption"]))

doc.build(S)
print("PDF oluşturuldu: Yonetici_Ozeti_Raporu.pdf")
