import urllib.parse

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .forms import ContactMessageForm
from .models import FinancialData, Product, News, Category, WhatsAppClick, Blog

# Ana sayfadaki kısaltılmış "öne çıkanlar" bandı — tam liste /piyasa-durumu/ sayfasında.
# Not: Panelden bu kodlardan biri silinirse get_ordered_rates otomatik atlar, hata vermez.
HOME_HIGHLIGHTS = ['HAS', 'CEYREK', 'TAM', 'ONS']

# /piyasa-durumu/ başlığındaki hızlı özet (HAS: TL, ONS/$: USD) — ONSUSD, TL
# değil USD cinsinden olduğu için ana listeye (get_visible_rates) dahil edilmez,
# çeviricide karışıklık olmasın diye ayrı tutulur.
QUICKSTAT_ORDER = ['HAS', 'ONSUSD']


def get_ordered_rates(codes):
    """Verilen kod listesi sırasına göre FinancialData kayıtlarını döndürür."""
    kayitlar = {f.code: f for f in FinancialData.objects.filter(code__in=codes)}
    return [kayitlar[code] for code in codes if code in kayitlar]


def get_visible_rates():
    """
    Panelden 'Sitede Göster' işaretli tüm kalemleri, panelden ayarlanan
    sıraya göre döndürür. Piyasa Durumu, Çevirici ve API bu tek listeyi
    kullanır - panelden eklenen/silinen/gizlenen her değişiklik otomatik
    yansır. ONSUSD, TL cinsinden olmadığı (USD) için hariç tutulur; sadece
    Piyasa Durumu başlığındaki hızlı özette ayrıca gösterilir.
    """
    return (
        FinancialData.objects.filter(is_visible=True)
        .exclude(code='ONSUSD')
        .order_by('display_order', 'name')
    )


def try_unit():
    """
    Çeviricide 'Türk Lirası'nı da seçilebilir kılmak için kullanılan sentetik
    birim (1 TL = 1 TL). Veritabanında karşılığı yok, sadece görüntü/hesap içindir.
    """
    return {
        'code': 'TRY',
        'name': 'Türk Lirası',
        'buy_price': '1.0000',
        'sell_price': '1.0000',
        'final_sell_price': '1.0000',
        'change_percent': '0',
        'change_amount': '0',
        'updated_at': timezone.now().isoformat(),
    }


def home_page(request):
    # 1. Ana sayfa: sadece öne çıkan birkaç kalem. Tamamı /piyasa-durumu/ sayfasında.
    altin_verileri = get_ordered_rates(HOME_HIGHLIGHTS)

    # Vitrine koyulacak ürünleri çekelim (Yayında olanlar)
    vitrin_urunleri = Product.objects.filter(is_active=True).order_by('-created_at')[:4]

    # Son dakika haberlerini çekelim
    haberler = News.objects.filter(is_published=True).order_by('-created_at')[:3]

    # Ana sayfa vitrinindeki blog yazıları
    blog_yazilari = Blog.objects.filter(is_published=True).order_by('display_order', '-created_at')[:3]

    context = {
        'altin_verileri': altin_verileri,
        'vitrin_urunleri': vitrin_urunleri,
        'haberler': haberler,
        'blog_yazilari': blog_yazilari,
    }

    # 2. Bu verileri HTML dosyasına gönderiyoruz
    return render(request, 'index.html', context)


def market_page(request):
    """Panelden 'Sitede Göster' işaretli tüm kalemlerin listelendiği Piyasa Durumu sayfası."""
    kalemler = get_visible_rates()
    hizli_ozet = {veri.code: veri for veri in get_ordered_rates(QUICKSTAT_ORDER)}

    # Cumartesi/Pazar günleri Kapalı Çarşı fiilen kapalıdır, bu yüzden fiyatlar
    # hafta sonu boyunca değişmez (bu normaldir, hata değildir). Ziyaretçiye
    # bunu açıkça belirtmek için bir uyarı gösteriyoruz.
    yerel_saat = timezone.localtime(timezone.now())
    piyasa_kapali = yerel_saat.weekday() >= 5  # 5=Cumartesi, 6=Pazar

    context = {
        'kalemler': kalemler,
        'has_veri': hizli_ozet.get('HAS'),
        'ons_usd_veri': hizli_ozet.get('ONSUSD'),
        'piyasa_kapali': piyasa_kapali,
    }
    return render(request, 'market.html', context)


def product_list(request):
    """
    Yayında olan ürünleri listeler. Ayar, gramaj aralığı, taş türü, fiyat
    aralığı ve kategoriye göre filtrelenebilir - hepsi opsiyonel GET
    parametreleridir, hiçbiri seçilmezse tüm ürünler listelenir.
    """
    urunler = Product.objects.filter(is_active=True).select_related('category').prefetch_related('images')

    secili_kategori = request.GET.get('kategori', '').strip()
    if secili_kategori:
        urunler = urunler.filter(category__slug=secili_kategori)

    secili_ayar = request.GET.get('ayar', '').strip()
    if secili_ayar:
        try:
            urunler = urunler.filter(purity=int(secili_ayar))
        except ValueError:
            pass

    secili_tas = request.GET.get('tas', '').strip()
    if secili_tas:
        urunler = urunler.filter(stone_type=secili_tas)

    gram_min = request.GET.get('gram_min', '').strip()
    gram_max = request.GET.get('gram_max', '').strip()
    if gram_min:
        try:
            urunler = urunler.filter(weight_gram__gte=float(gram_min))
        except ValueError:
            pass
    if gram_max:
        try:
            urunler = urunler.filter(weight_gram__lte=float(gram_max))
        except ValueError:
            pass

    siralama = request.GET.get('sirala', '-created_at')
    gecerli_siralamalar = {'-created_at', 'created_at', 'name', '-name'}
    if siralama not in gecerli_siralamalar:
        siralama = '-created_at'
    urunler = urunler.order_by(siralama)

    # Fiyat aralığı filtresi canlı hesaplandığı için Python tarafında uygulanır
    # (veritabanı sorgusuyla değil - hesapla_fiyat bir property).
    fiyat_min = request.GET.get('fiyat_min', '').strip()
    fiyat_max = request.GET.get('fiyat_max', '').strip()
    urunler = list(urunler)
    if fiyat_min:
        try:
            fmin = float(fiyat_min)
            urunler = [u for u in urunler if u.hesapla_fiyat >= fmin]
        except ValueError:
            pass
    if fiyat_max:
        try:
            fmax = float(fiyat_max)
            urunler = [u for u in urunler if u.hesapla_fiyat <= fmax]
        except ValueError:
            pass

    context = {
        'urunler': urunler,
        'kategoriler': Category.objects.all(),
        'ayar_secenekleri': Product.AYAR_SECENEKLERI,
        'tas_secenekleri': Product.TAS_TURU_SECENEKLERI,
        'secili_kategori': secili_kategori,
        'secili_ayar': secili_ayar,
        'secili_tas': secili_tas,
        'gram_min': gram_min,
        'gram_max': gram_max,
        'fiyat_min': fiyat_min,
        'fiyat_max': fiyat_max,
        'secili_sirala': siralama,
    }
    return render(request, 'product_list.html', context)


def product_detail(request, slug):
    urun = get_object_or_404(Product, slug=slug, is_active=True)

    context = {
        'urun': urun,
    }
    return render(request, 'product_detail.html', context)


def blog_list(request):
    yazilar = Blog.objects.filter(is_published=True).order_by('display_order', '-created_at')
    return render(request, 'blog_list.html', {'yazilar': yazilar})


def blog_detail(request, slug):
    yazi = get_object_or_404(Blog, slug=slug, is_published=True)
    diger_yazilar = Blog.objects.filter(is_published=True).exclude(pk=yazi.pk).order_by('display_order', '-created_at')[:3]
    return render(request, 'blog_detail.html', {'yazi': yazi, 'diger_yazilar': diger_yazilar})


def contact_page(request):
    """İletişim & Mağaza sayfası: adres/harita/çalışma saatleri + iletişim formu."""
    if request.method == 'POST':
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(f"{request.path}?gonderildi=1")
    else:
        form = ContactMessageForm()

    context = {
        'form': form,
        'gonderildi': request.GET.get('gonderildi') == '1',
    }
    return render(request, 'contact.html', context)


def whatsapp_redirect(request):
    """
    Sitedeki her WhatsApp butonu buraya yönlenir - önce tıklamayı
    WhatsAppClick olarak kaydeder, sonra gerçek wa.me bağlantısına 302 ile
    yönlendirir. GET parametreleri: kaynak (urun_detay/iletisim/genel),
    urun (opsiyonel ürün pk'sı, mesaj metnine ürün adını eklemek için).
    """
    kaynak = request.GET.get('kaynak', 'genel')
    gecerli_kaynaklar = {k for k, _ in WhatsAppClick.KAYNAK_SECENEKLERI}
    if kaynak not in gecerli_kaynaklar:
        kaynak = 'genel'

    urun = None
    urun_pk = request.GET.get('urun')
    if urun_pk:
        urun = Product.objects.filter(pk=urun_pk).first()

    WhatsAppClick.objects.create(source=kaynak, product=urun)

    numara = getattr(settings, 'WHATSAPP_NUMBER', '').replace(' ', '').replace('+', '')
    if not numara:
        return HttpResponse("WhatsApp numarası ayarlanmamış.", status=503)

    if urun:
        mesaj = f"Merhaba, {urun.name} ürünü hakkında bilgi almak istiyorum."
    else:
        mesaj = "Merhaba, bilgi almak istiyorum."

    wa_url = f"https://wa.me/{numara}?text={urllib.parse.quote(mesaj)}"
    return HttpResponseRedirect(wa_url)


def news_detail(request, slug):
    haber = get_object_or_404(News, slug=slug, is_published=True)

    context = {
        'haber': haber,
    }
    return render(request, 'news_detail.html', context)


def converter_page(request):
    kalemler = get_visible_rates()

    context = {
        'kalemler': kalemler,
    }
    return render(request, 'converter.html', context)


def rates_api(request):
    """
    Piyasa Durumu kartlarını sayfa yenilenmeden güncellemek için kullanılan
    hafif JSON uç noktası. static/js/rates.js ve board.js tarafından periyodik olarak çağrılır.
    """
    data = [
        {
            'code': veri.code,
            'name': veri.name,
            'raw_buy_price': str(veri.buy_price),
            'raw_sell_price': str(veri.sell_price),
            'buy_price': str(veri.final_buy_price),
            'sell_price': str(veri.sell_price),
            'final_sell_price': str(veri.final_sell_price),
            'change_percent': str(veri.change_percent),
            'change_amount': str(veri.change_amount),
            'updated_at': veri.updated_at.isoformat(),
        }
        for veri in get_visible_rates()
    ]
    # ONSUSD, get_visible_rates() dışında tutuluyor (TL değil) ama Piyasa
    # Durumu başlığındaki hızlı özeti canlı tutabilmek için ayrıca ekleniyor.
    for veri in get_ordered_rates(QUICKSTAT_ORDER):
        if veri.code == 'ONSUSD':
            data.append({
                'code': veri.code,
                'name': veri.name,
                'raw_buy_price': str(veri.buy_price),
                'raw_sell_price': str(veri.sell_price),
                'buy_price': str(veri.final_buy_price),
                'sell_price': str(veri.sell_price),
                'final_sell_price': str(veri.final_sell_price),
                'change_percent': str(veri.change_percent),
                'change_amount': str(veri.change_amount),
                'updated_at': veri.updated_at.isoformat(),
            })
    data.append(try_unit())
    return JsonResponse(data, safe=False)


def robots_txt(request):
    """
    Arama motoru botlarına hangi sayfaları taramaları/taramamaları gerektiğini
    söyler. Panel ve admin girişleri arama sonuçlarında ASLA görünmemeli.
    """
    site_domain = getattr(settings, 'SITE_DOMAIN', '').rstrip('/')
    satirlar = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /panel/",
        "Disallow: /yonetim-9f3k2/",
        "",
        f"Sitemap: {site_domain}/sitemap.xml",
    ]
    return HttpResponse("\n".join(satirlar), content_type="text/plain")
