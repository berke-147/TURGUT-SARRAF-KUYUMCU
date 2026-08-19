"""
Canlı altın, gümüş kuru çekme mantığı.

Hem "python manage.py update_rates" (tek seferlik) hem de
"python manage.py update_rates_loop" (sürekli arka plan döngüsü)
komutları bu modüldeki update_all_rates() fonksiyonunu kullanır.

VERİ KAYNAKLARI (öncelik sırasıyla):

1. dovizgrafik.com/altin (ÖNCELİKLİ, Kapalı Çarşı'nın önerdiği kapalıçarşı
   fiyatları). Bu RESMİ BİR API DEĞİL — genel/ücretsiz görüntülenen sayfa
   üzerinden okunuyor (scrape). Sayfa yapısı değişirse veya erişilemezse
   otomatik olarak aşağıdaki yedek yönteme düşer, site ASLA çökmez.

2. Yedek (fallback) - API key gerektirmeyen ücretsiz kaynaklar:
   - https://api.gold-api.com/price/XAU              -> 1 ons altının USD fiyatı
   - https://api.gold-api.com/price/XAG              -> 1 ons gümüşün USD fiyatı
   - https://api.exchangerate-api.com/v4/latest/USD  -> USD bazlı kur (sadece
     dolar bazlı hesaplarda TL karşılığı bulmak için, döviz kalemi olarak
     sitede gösterilmez)
   Bu yöntemde çeyrek/yarım/tam/ata/cumhuriyet/gremse gibi sikkelerin fiyatı,
   içerdiği has altına TİPİK bir piyasa primi eklenerek YAKLAŞIK hesaplanır
   (gerçek günlük prim değildir).

ÇARPAN (yüzde DEĞİL):
   Her kalemin "Satış Çarpanı" alanı (admin veya panelden girilir) HER ZAMAN
   korunur ve ham/çekilen fiyatla DOĞRUDAN çarpılır (final_sell_price =
   sell_price * sell_multiplier). Bu fonksiyonlar kur güncellerken bu alana
   ASLA dokunmaz (yalnızca ilk kayıt oluşturulurken sikkeler için tipik bir
   başlangıç çarpanı önerilir). Yani panelden bir çarpan girdiğinde, sonraki
   otomatik güncellemelerde sıfırlanmaz. Aynı mantıkla, robot bir kaydın
   "name" (görünen ad) alanına da SADECE kayıt ilk kez oluşturulurken
   dokunur - panelden verdiğin isim asla otomatik geri değişmez.

SEÇİME BAĞLI TAKİP (is_tracked):
   AVAILABLE_SOURCE_ITEMS listesindeki HAS dışındaki hiçbir kalem, panelden
   ("Kaynak Kalemleri Seç" ekranı) açıkça seçilmeden veritabanında kayıt
   OLUŞTURULMAZ. update_all_rates() her kalem için önce is_tracked(code) ile
   veritabanında zaten bir kayıt olup olmadığını kontrol eder; kayıt yoksa o
   kalemi hiç çekmez/oluşturmaz. Panelden bir kalem seçildiğinde satır hemen
   oluşturulur ve BİR SONRAKİ otomatik güncelleme turunda (birkaç saniye
   içinde) fiyatı çekilmeye başlar. Seçim kaldırılırsa (panelden silinirse)
   robot bir daha o kalemi hiç güncellemez.
"""
import datetime
import decimal
import re

import requests
from django.utils import timezone

from .models import FinancialData, RateSnapshot

# Fiyat geçmişi örnekleme aralığı: bir kalem için EN FAZLA bu sıklıkta
# geçmiş satırı yazılır (robot 3 sn'de bir dönse bile). Grafik için 5 dk
# çözünürlük fazlasıyla yeterli, veritabanı da şişmez.
GECMIS_ARALIGI = datetime.timedelta(minutes=5)

# Bu süreden eski geçmiş kayıtları otomatik silinir.
GECMIS_SAKLAMA = datetime.timedelta(days=90)


def _gecmisi_kaydet(code, buy_price, sell_price):
    """
    Kalemin fiyat geçmişine (grafik verisi) örnek yazar - ama son örnekten
    bu yana GECMIS_ARALIGI geçmediyse hiçbir şey yapmaz. Arada bir de eski
    kayıtları temizler. Hata olursa sessizce geçer: geçmiş kaydı, kur
    güncellemesinin kendisini ASLA aksatmamalı.
    """
    try:
        simdi = timezone.now()
        son = (
            RateSnapshot.objects.filter(code=code)
            .values_list('created_at', flat=True)
            .first()  # ordering = ['-created_at'] -> en yenisi
        )
        if son is not None and (simdi - son) < GECMIS_ARALIGI:
            return

        RateSnapshot.objects.create(code=code, buy_price=buy_price, sell_price=sell_price)

        # Temizlik: eski kayıtları sil (her örnek yazımında çalışsa da
        # 5 dakikada bir küçük bir delete sorgusudur, yük oluşturmaz).
        RateSnapshot.objects.filter(created_at__lt=simdi - GECMIS_SAKLAMA).delete()
    except Exception:
        pass

METAL_API_URL = "https://api.gold-api.com/price/{symbol}"
FX_API_URL = "https://api.exchangerate-api.com/v4/latest/USD"
SOURCE_URL = "https://dovizgrafik.com/altin"

GRAM_PER_OUNCE = decimal.Decimal("31.1034768")

# Piyasa alış/satış arasında gerçek bankalardaki gibi küçük bir makas
# bırakmak için kullanılan yaklaşık oran (sadece scrape başarısız olursa kullanılır).
BUY_SPREAD = decimal.Decimal("0.995")

# Ayar -> milyem (saflık) oranı. Product modelindeki milyem_oranlari ile aynı.
MILYEM_ORANLARI = {
    24: decimal.Decimal("1.000"),
    22: decimal.Decimal("0.916"),
    14: decimal.Decimal("0.585"),
    8: decimal.Decimal("0.333"),
}

# Gram bazlı altın kalemleri: kod -> (görünen ad, ayar)
GRAM_GOLD_ITEMS = {
    "HAS": ("Has Altın (24 Ayar Gram)", 24),
    "GRAM22": ("22 Ayar Gram Altın", 22),
    "GRAM14": ("14 Ayar Gram Altın", 14),
    "GRAM8": ("8 Ayar Gram Altın", 8),
}

# Sikke/ölçü bazlı altın kalemleri: kod -> (görünen ad, brüt gramaj, ayar, varsayılan çarpan)
# Bu varsayılan ÇARPANLAR (yüzde DEĞİL) SADECE kaynak siteden gerçek veri
# çekilemediğinde (yedek moda düşüldüğünde) kullanılır. Örn: 1.06 = ham
# hesaba %6 tipik piyasa primi eklenir.
COIN_GOLD_ITEMS = {
    "CEYREK": ("Çeyrek Altın", decimal.Decimal("1.75"), 22, decimal.Decimal("1.06")),
    "YARIM": ("Yarım Altın", decimal.Decimal("3.50"), 22, decimal.Decimal("1.05")),
    "TAM": ("Tam Altın", decimal.Decimal("7.00"), 22, decimal.Decimal("1.04")),
    "ATA": ("Ata Altın (Ata Lira)", decimal.Decimal("7.216"), 22, decimal.Decimal("1.07")),
    "CUMHURIYET": ("Cumhuriyet Altını", decimal.Decimal("7.00"), 22, decimal.Decimal("1.05")),
    "GREMSE": ("Gremse Altın", decimal.Decimal("3.60"), 22, decimal.Decimal("1.05")),
}

# Sadece kaynak siteden canlı çekilebilen, fallback formülü OLMAYAN kalemler.
# Kaynağa erişilemezse bu turda GÜNCELLENMEZ, son bilinen fiyat sitede
# kalmaya devam eder.
EXTRA_SOURCE_ONLY_ITEMS = {
    "ESKICEYREK": "Eski Çeyrek Altın",
    "ATA5": "5'li Ata",
}

# Panelde "Kaynak Kalemleri Seç" ekranında admin'e sunulan TÜM seçenekler.
# kaynak='dovizgrafik' -> dovizgrafik.com/altin sayfasından CANLI çekilir.
# kaynak='hesap'       -> Has altının (HAS) üzerinden ORANLA hesaplanır,
#                         kaynak sitede doğrudan ayrı bir satırı yoktur.
# HAS listenin dışında tutulur çünkü zorunludur (bkz. CORE_CODES) - panelde
# seçim dışı, her zaman otomatik takip edilir.
AVAILABLE_SOURCE_ITEMS = [
    ("GRAM22", "22 Ayar Altın", "dovizgrafik"),
    ("GRAM14", "14 Ayar Altın", "dovizgrafik"),
    ("GRAM8", "8 Ayar Gram Altın", "hesap"),
    ("CEYREK", "Çeyrek Altın", "dovizgrafik"),
    ("ESKICEYREK", "Eski Çeyrek Altın", "dovizgrafik"),
    ("YARIM", "Yarım Altın", "dovizgrafik"),
    ("TAM", "Tam Altın", "dovizgrafik"),
    ("ATA", "Ata Altın (Ata Lira)", "dovizgrafik"),
    ("ATA5", "5'li Ata", "dovizgrafik"),
    ("CUMHURIYET", "Cumhuriyet Altını", "dovizgrafik"),
    ("GREMSE", "Gremse Altın", "dovizgrafik"),
    ("ONS", "Ons Altın (TL)", "hesap"),
    ("ONSUSD", "Ons Altın (USD)", "dovizgrafik"),
    ("GUMUS", "Gram Gümüş", "dovizgrafik"),
]

# HAS (Gram Altın), diğer tüm hesaplamaların temeli olduğu için panelde
# seçim dışıdır - her zaman otomatik takip edilir/oluşturulur.
CORE_CODES = {"HAS"}

# dovizgrafik.com/altin tablosundaki satır başlıklarını bizim kodlarımıza
# eşler. Sırayla denenir, İLK eşleşen anahtar kazanır - bu yüzden "Eski"
# gibi daha ÖZEL etiketler kendi temel karşılığından (ör. "Çeyrek Altın
# Eski" -> "Çeyrek Altın") önce gelmelidir, yoksa "Çeyrek Altın" anahtarı
# "Çeyrek Altın Eski" satırına da (yanlışlıkla) eşleşir çünkü o metin
# içinde geçer.
#
# ÖZEL DURUM: kaynak sitede "Ata" ve "Cumhuriyet" TEK bir satırda
# ("Ata Cumhuriyet") birlikte veriliyor - bu satır önce ATA_CUM adlı geçici
# bir anahtara toplanır, fetch_source_prices() sonunda hem ATA hem
# CUMHURIYET koduna aynı fiyat kopyalanır (bkz. fonksiyonun sonu).
#
# NOT: Kaynak sitede "HAS Altın" adında ayrı, doğrudan bir satır var - bizim
# HAS (24 ayar has altın) kodumuzun temeli budur.
SOURCE_LABEL_MAP = [
    ("HAS Altın", "HAS"),
    ("22 Ayar Altın", "GRAM22"),
    ("14 Ayar Altın", "GRAM14"),
    ("Çeyrek Altın Eski", "ESKICEYREK"),
    ("Çeyrek Altın", "CEYREK"),
    ("Yarım Altın", "YARIM"),
    ("Tam Altın", "TAM"),
    ("5'li Ata", "ATA5"),
    ("Ata Cumhuriyet", "ATA_CUM"),
    ("Gremse", "GREMSE"),
    ("ONS $", "ONSUSD"),
    ("Gümüş/TL", "GUMUS"),
]

_ROW_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.IGNORECASE | re.DOTALL)
_CELL_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_NUM_RE = re.compile(r"[\d.,]+")


def _strip_tags(html_fragment):
    text = _TAG_RE.sub(" ", html_fragment)
    return re.sub(r"\s+", " ", text).strip()


def _parse_price_text(text):
    """'6.216,27' -> Decimal('6216.27') ; '6216.27' -> Decimal('6216.27')"""
    if not text:
        return None
    text = text.strip()
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        value = decimal.Decimal(text)
        return value if value > 0 else None
    except decimal.InvalidOperation:
        return None


def fetch_source_prices():
    """
    dovizgrafik.com/altin sayfasındaki Kapalı Çarşı önerilen fiyatlar
    tablosundan gerçek alış/satış fiyatlarını okumaya çalışır. RESMİ BİR API
    DEĞİLDİR — sayfa görünümü değişirse boş sözlük döndürebilir, bu normaldir
    ve çağıran taraf (update_all_rates) bunu otomatik olarak yedek
    hesaplamayla telafi eder.

    Satış hücresinde fiyatın yanında değişim yüzdesi de yazıyor
    (ör. "6094.93 -0.82%") - _NUM_RE ilk sayıyı (fiyatı) yakalayıp yüzdeyi
    otomatik göz ardı eder.

    Dönüş: {'HAS': (alis, satis), 'CEYREK': (alis, satis), ...}
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )
    }
    response = requests.get(SOURCE_URL, headers=headers, timeout=10)
    response.raise_for_status()
    html_text = response.text

    sonuc = {}
    kullanilan = set()

    for row_html in _ROW_RE.findall(html_text):
        cells_html = _CELL_RE.findall(row_html)
        if len(cells_html) < 3:
            continue

        cells = [_strip_tags(c) for c in cells_html]
        baslik = cells[0]
        if not baslik:
            continue

        for anahtar, kod in SOURCE_LABEL_MAP:
            if kod in kullanilan or anahtar not in baslik:
                continue

            alis_match = _NUM_RE.search(cells[1])
            alis = _parse_price_text(alis_match.group(0)) if alis_match else None

            satis_match = _NUM_RE.search(cells[2])
            satis = _parse_price_text(satis_match.group(0)) if satis_match else None

            if alis and satis:
                sonuc[kod] = (alis, satis)
                kullanilan.add(kod)
            break

    # ÖZEL DURUM: "Ata Cumhuriyet" tek satırı hem ATA hem CUMHURIYET koduna kopyalanır.
    if "ATA_CUM" in sonuc:
        sonuc["ATA"] = sonuc["ATA_CUM"]
        sonuc["CUMHURIYET"] = sonuc["ATA_CUM"]
        del sonuc["ATA_CUM"]

    return sonuc


def fetch_fx_rates():
    """USD için TL karşılığını döndürür (sadece HAS/gümüş fallback hesabında kullanılır)."""
    response = requests.get(FX_API_URL, timeout=10)
    response.raise_for_status()
    data = response.json()
    rates = data["rates"]
    return {"USD": decimal.Decimal(str(rates["TRY"]))}


def fetch_metal_ounce_usd(symbol):
    """Verilen değerli metalin (XAU/XAG) 1 ons'unun HAM USD fiyatını döndürür."""
    response = requests.get(METAL_API_URL.format(symbol=symbol), timeout=10)
    response.raise_for_status()
    data = response.json()
    return decimal.Decimal(str(data["price"]))


def ounce_usd_to_gram_try(ons_usd, usd_try):
    """Ons başına USD fiyatından, gram başına TL fiyatına çevirir."""
    gram_usd = ons_usd / GRAM_PER_OUNCE
    return gram_usd * usd_try


def is_tracked(code):
    """
    Bu kod için veritabanında zaten bir FinancialData kaydı var mı?
    Panelden ("Kaynak Kalemleri Seç") açıkça seçilmemiş/oluşturulmamış
    kalemler için robot HİÇBİR ZAMAN otomatik kayıt oluşturmaz - sadece
    zaten var olan kayıtları günceller.
    """
    return FinancialData.objects.filter(code=code).exists()


def upsert(code, name, sell_price, log, buy_price=None, default_multiplier=None):
    """
    ÖNEMLİ: Bu fonksiyon kayıt oluşturulurken (created=True) hariç ASLA
    sell_multiplier, name (görünen ad), is_visible veya display_order
    alanlarına dokunmaz. Panelden/admin'den girilen bu değerler kalıcıdır —
    her kur güncellemesinde (scrape ya da yedek hesap fark etmeksizin)
    korunur. default_multiplier sadece kayıt ilk kez oluşturuluyorsa ya da
    çarpan hâlâ dokunulmamış varsayılan 1 ise, başlangıç için tipik bir
    değer önerir.

    % DEĞİŞİM REFERANSI (previous_sell_price): Borsa panolarındaki "Fark"
    sütunu gibi, bir ÖNCEKİ GÜNÜN SON FİYATINA göre hesaplanır — son 3
    saniyedeki tik'e göre DEĞİL. Yani previous_sell_price gün içinde SADECE
    günün ilk güncellemesinde değişir (dünkü son fiyat = bugünün referansı)
    ve o günün geri kalanında sabit kalır. Böylece %değişim, gün boyunca
    tutarlı ve anlamlı kalır (kaynağın "kapanış fiyatı" kavramı olmadığı
    için, önceki günün son bilinen fiyatı en yakın karşılığıdır).
    """
    sell_price = round(sell_price, 4)
    buy_price = round(buy_price, 4) if buy_price is not None else round(sell_price * BUY_SPREAD, 4)

    mevcut = (
        FinancialData.objects.filter(code=code)
        .values("sell_price", "updated_at")
        .first()
    )

    # NOT: "name" burada BİLEREK defaults'a eklenmiyor - sadece aşağıda
    # created=True olduğunda bir kere yazılıyor. Böylece panelden bir
    # kaleme verdiğin isim, robotun bir sonraki turunda geri değişmez.
    defaults = {
        "sell_price": sell_price,
        "buy_price": buy_price,
    }

    bugun = timezone.localtime(timezone.now()).date()

    if mevcut is None:
        # İlk kayıt: referans fiyat kendisi olsun, değişim %0 gösterilsin.
        defaults["previous_sell_price"] = sell_price
    else:
        kayit_gunu = timezone.localtime(mevcut["updated_at"]).date()
        if kayit_gunu < bugun:
            # Bugünün İLK güncellemesi: dünkü SON fiyat, bugünün sabit
            # referansı (kapanış fiyatı yerine) olarak kaydediliyor.
            defaults["previous_sell_price"] = mevcut["sell_price"]
        # else: aynı gün içindeyiz — previous_sell_price'a HİÇ dokunma,
        # gün başında ayarlanan referans günün sonuna kadar sabit kalsın.

    obj, created = FinancialData.objects.update_or_create(
        code=code,
        defaults=defaults,
    )

    if created:
        obj.name = name
        obj.save(update_fields=["name"])

    if default_multiplier is not None and (created or obj.sell_multiplier == 1):
        # Kayıt ilk kez oluşturuluyorsa YA DA çarpan hâlâ dokunulmamış
        # varsayılan 1 ise, tipik piyasa çarpanını başlangıç değeri olarak
        # yaz. Panelden bir değer girildikten sonra bir daha buradan değiştirilmez.
        obj.sell_multiplier = default_multiplier
        obj.save(update_fields=["sell_multiplier"])

    # Grafik için fiyat geçmişi örneği (en fazla 5 dk'da bir yazılır).
    _gecmisi_kaydet(code, buy_price, sell_price)

    durum = "oluşturuldu" if created else "güncellendi"
    log(f"  - {code} {durum}: {sell_price} TL")


def update_all_rates(log=print):
    """
    Tüm altın ve gümüş kurlarını çekip veritabanını günceller. Önce
    dovizgrafik.com/altin'den gerçek Kapalı Çarşı verisini dener; bulamadığı
    kalemler için gold-api.com + exchangerate-api.com'dan hesaplanan yaklaşık
    değere otomatik olarak döner. Ağ hatası olursa exception fırlatır (çağıran
    taraf yakalamalı).
    """
    scraped = {}
    try:
        scraped = fetch_source_prices()
        log(f"dovizgrafik.com/altin verisi: {len(scraped)} kalem bulundu.")
    except Exception as exc:
        log(f"dovizgrafik.com/altin'den veri çekilemedi ({exc}), yedek hesaplamaya geçiliyor.")

    fx_rates = fetch_fx_rates()
    usd_try = fx_rates["USD"]

    # Has altın gram fiyatı (diğer tüm gram hesaplarının temeli) - HER ZAMAN
    # takip edilir, panelden seçilmesi gerekmez (bkz. CORE_CODES).
    if "HAS" in scraped:
        alis, satis = scraped["HAS"]
        gram_has_try = satis
        upsert("HAS", GRAM_GOLD_ITEMS["HAS"][0], satis, log, buy_price=alis)
    else:
        xau_ons_usd = fetch_metal_ounce_usd("XAU")
        gram_has_try = ounce_usd_to_gram_try(xau_ons_usd, usd_try)
        upsert("HAS", GRAM_GOLD_ITEMS["HAS"][0], gram_has_try, log)

    # --- AŞAĞIDAKİLERİN HEPSİ SEÇİME BAĞLI ---
    # Her biri SADECE panelden ("Kaynak Kalemleri Seç") daha önce seçilmiş,
    # yani veritabanında zaten bir kaydı varsa güncellenir (bkz. is_tracked).
    # Seçilmemiş bir kalem için robot hiçbir zaman otomatik kayıt oluşturmaz.

    # Diğer gram bazlı altınlar (22-14 kaynak siteden, 8 ayar hesaplanan)
    for code, (name, ayar) in GRAM_GOLD_ITEMS.items():
        if code == "HAS" or not is_tracked(code):
            continue
        if code in scraped:
            alis, satis = scraped[code]
            upsert(code, name, satis, log, buy_price=alis)
        else:
            carpan = MILYEM_ORANLARI[ayar]
            upsert(code, name, gram_has_try * carpan, log)

    # Sikke/ölçü bazlı altınlar (kaynak siteden çekilebilenler + fallback formülü olanlar)
    for code, (name, gramaj, ayar, default_multiplier) in COIN_GOLD_ITEMS.items():
        if not is_tracked(code):
            continue
        if code in scraped:
            alis, satis = scraped[code]
            upsert(code, name, satis, log, buy_price=alis)
        else:
            carpan = MILYEM_ORANLARI[ayar]
            upsert(code, name, gram_has_try * carpan * gramaj, log, default_multiplier=default_multiplier)

    # "Eski Çeyrek" ve "5'li Ata" gibi kalemler - SADECE kaynak siteden canlı
    # çekilebilir, fallback formülü yok. Kaynağa erişilemezse bu turda
    # güncellenmezler (son bilinen fiyat sitede kalmaya devam eder).
    for code, name in EXTRA_SOURCE_ONLY_ITEMS.items():
        if not is_tracked(code):
            continue
        if code in scraped:
            alis, satis = scraped[code]
            upsert(code, name, satis, log, buy_price=alis)
        else:
            log(f"  - {code}: kaynak siteden veri gelmedi, bu turda güncellenmedi.")

    # Ons altın (TL) - kendi hesabımız, has altından türetilir. Kaynak sitede
    # ayrı bir "Ons Altın (TL)" satırı olmadığı için HER ZAMAN hesaplanarak yazılır.
    if is_tracked("ONS"):
        ons_try = gram_has_try * GRAM_PER_OUNCE
        upsert("ONS", "Ons Altın (TL)", ons_try, log)

    # Ons altın (USD) - Piyasa Durumu başlığındaki hızlı özet için
    if is_tracked("ONSUSD"):
        if "ONSUSD" in scraped:
            alis, satis = scraped["ONSUSD"]
            upsert("ONSUSD", "Ons Altın (USD)", satis, log, buy_price=alis)
        else:
            xau_ons_usd = fetch_metal_ounce_usd("XAU")
            upsert("ONSUSD", "Ons Altın (USD)", xau_ons_usd, log)

    # Gram gümüş
    if is_tracked("GUMUS"):
        if "GUMUS" in scraped:
            alis, satis = scraped["GUMUS"]
            upsert("GUMUS", "Gram Gümüş", satis, log, buy_price=alis)
        else:
            xag_ons_usd = fetch_metal_ounce_usd("XAG")
            gram_gumus_try = ounce_usd_to_gram_try(xag_ons_usd, usd_try)
            upsert("GUMUS", "Gram Gümüş", gram_gumus_try, log)
