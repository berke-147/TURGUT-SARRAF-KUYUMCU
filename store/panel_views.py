"""
Dükkan sahibi paneli.

Ana sitenin menüsünde bu sayfalara hiçbir link verilmez; sadece URL'yi
bilen (staff yetkili) kullanıcı /panel/giris/ adresinden giriş yapıp
ürün ve haber ekleyip düzenleyebilir.
"""
import json

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.views import LoginView, LogoutView
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    PanelLoginForm, ProductForm, NewsForm, FinancialCreateForm, FinancialEditForm,
    CategoryForm, BlogForm,
)
from .models import (
    Product, News, FinancialData, Category, ProductImage,
    ProductColorOption, ProductSizeOption, ContactMessage, WhatsAppClick, Blog,
)
from .services import AVAILABLE_SOURCE_ITEMS

# Sadece aktif + staff (personel) kullanıcılar panele girebilir.
# Giriş yapmamış/izni olmayan biri panel sayfalarından birine gitmeye
# çalışırsa otomatik olarak panel giriş sayfasına yönlendirilir.
panel_required = user_passes_test(lambda u: u.is_active and u.is_staff, login_url='panel_login')


class PanelLoginView(LoginView):
    template_name = 'panel/login.html'
    form_class = PanelLoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse('panel_dashboard')


class PanelLogoutView(LogoutView):
    next_page = 'panel_login'


@panel_required
def dashboard(request):
    bugun = timezone.localtime(timezone.now()).date()
    context = {
        'urun_sayisi': Product.objects.count(),
        'aktif_urun_sayisi': Product.objects.filter(is_active=True).count(),
        'haber_sayisi': News.objects.count(),
        'blog_sayisi': Blog.objects.count(),
        'kategori_sayisi': Category.objects.count(),
        'okunmamis_mesaj_sayisi': ContactMessage.objects.filter(is_read=False).count(),
        'whatsapp_bugun': WhatsAppClick.objects.filter(created_at__date=bugun).count(),
        'whatsapp_toplam': WhatsAppClick.objects.count(),
        'son_mesajlar': ContactMessage.objects.all()[:5],
        'son_urunler': Product.objects.all().order_by('-created_at')[:5],
    }
    return render(request, 'panel/dashboard.html', context)


# ---------------------------------------------------------------- FİNANSAL VERİLER / KAR MARJI

@panel_required
def finance_list(request):
    """
    Veritabanındaki TÜM piyasa kalemlerini (görünür/gizli fark etmeksizin)
    sıra numarasına göre listeler. Buradan yeni kalem eklenebilir, mevcut
    kalem düzenlenebilir/silinebilir, sitede gösterilip gösterilmeyeceği
    (is_visible) ve sırası (display_order) ayarlanabilir.
    """
    kalemler = FinancialData.objects.all().order_by('display_order', 'name')
    return render(request, 'panel/finance_list.html', {'kalemler': kalemler})


@panel_required
def finance_create(request):
    """
    Yeni bir piyasa kalemi ekler. Kod, services.py'deki robotun tanıdığı
    kodlardan biri değilse (ör. HAS, CEYREK, USD...), fiyat robot tarafından
    hiç dokunulmaz - burada girilen alış/satış fiyatı elle güncellenene kadar
    sabit kalır. Bu, saf altın dışı / özel kalemler eklemek için kullanışlıdır.
    """
    if request.method == 'POST':
        form = FinancialCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Yeni piyasa kalemi eklendi.')
            return redirect('panel_finance_list')
    else:
        form = FinancialCreateForm(initial={'display_order': 100, 'is_visible': True})
    return render(
        request,
        'panel/finance_form.html',
        {'form': form, 'baslik': 'Yeni Piyasa Kalemi Ekle', 'yeni_kayit': True},
    )


@panel_required
def finance_edit(request, code):
    kalem = get_object_or_404(FinancialData, code=code)
    if request.method == 'POST':
        form = FinancialEditForm(request.POST, instance=kalem)
        if form.is_valid():
            form.save()
            messages.success(request, f'{kalem.name} güncellendi.')
            return redirect('panel_finance_list')
    else:
        form = FinancialEditForm(instance=kalem)
    return render(
        request,
        'panel/finance_form.html',
        {'form': form, 'kalem': kalem, 'baslik': f'{kalem.name} - Düzenle'},
    )


@panel_required
def finance_delete(request, code):
    kalem = get_object_or_404(FinancialData, code=code)
    if request.method == 'POST':
        kalem.delete()
        messages.success(request, 'Kalem silindi.')
        return redirect('panel_finance_list')
    return render(
        request,
        'panel/confirm_delete.html',
        {'nesne': kalem, 'iptal_url': 'panel_finance_list'},
    )


@panel_required
def finance_source_picker(request):
    """
    dovizgrafik.com/altin'den (ya da has altın üzerinden hesaplanarak) çekilebilecek
    TÜM kalemleri listeler. Admin işaretlediği kalemler kaydedildiği anda
    FinancialData satırı olarak oluşturulur; bir sonraki otomatik güncelleme
    turunda (birkaç saniye içinde) robot o kalemi çekmeye başlar. İşareti
    kaldırılan bir kalem ise veritabanından tamamen silinir - takip durur.
    HAS (Gram Altın) listede YOK çünkü sistemin çalışması için zorunlu,
    her zaman otomatik takip edilir.
    """
    tum_kodlar = [code for code, _, _ in AVAILABLE_SOURCE_ITEMS]
    mevcut_kodlar = set(
        FinancialData.objects.filter(code__in=tum_kodlar).values_list('code', flat=True)
    )

    if request.method == 'POST':
        secilen_kodlar = set(request.POST.getlist('kodlar'))
        eklenen, silinen = 0, 0
        for code, name, _kaynak in AVAILABLE_SOURCE_ITEMS:
            var_mi = code in mevcut_kodlar
            secili_mi = code in secilen_kodlar
            if secili_mi and not var_mi:
                FinancialData.objects.create(code=code, name=name, is_visible=True)
                eklenen += 1
            elif not secili_mi and var_mi:
                FinancialData.objects.filter(code=code).delete()
                silinen += 1
        messages.success(
            request,
            f'Kaynak seçimleri güncellendi ({eklenen} eklendi, {silinen} kaldırıldı). '
            'Değişiklikler birkaç saniye içinde sitede yansır.',
        )
        return redirect('panel_finance_source_picker')

    kalemler = [
        {
            'code': code,
            'name': name,
            'kaynak': kaynak,
            'secili': code in mevcut_kodlar,
        }
        for code, name, kaynak in AVAILABLE_SOURCE_ITEMS
    ]
    return render(request, 'panel/finance_source_picker.html', {'kalemler': kalemler})


# ---------------------------------------------------------------- ÜRÜNLER

def _urun_varyasyonlarini_kaydet(urun, form):
    """
    ProductForm'daki 'renkler' (checkbox, çoklu seçim) ve 'olculer' (virgülle
    ayrılmış metin) alanlarını okuyup ProductColorOption/ProductSizeOption
    satırlarına çevirir. Ürün bazlı OPSİYONEL: hiç seçim yapılmazsa o
    varyasyon türü tamamen boş kalır ve sitede hiç gösterilmez.
    Mevcut seçim listesiyle senkronize eder (eklenmeyenler silinir).
    """
    secilen_renkler = set(form.cleaned_data.get('renkler') or [])
    mevcut_renkler = set(urun.renk_secenekleri.values_list('renk', flat=True))
    for renk in secilen_renkler - mevcut_renkler:
        ProductColorOption.objects.create(product=urun, renk=renk)
    ProductColorOption.objects.filter(product=urun, renk__in=(mevcut_renkler - secilen_renkler)).delete()

    secilen_olculer = list(form.cleaned_data.get('olculer') or [])
    mevcut_olculer = set(urun.olcu_secenekleri.values_list('olcu', flat=True))
    for olcu in secilen_olculer:
        if olcu not in mevcut_olculer:
            ProductSizeOption.objects.create(product=urun, olcu=olcu)
    ProductSizeOption.objects.filter(product=urun, olcu__in=(mevcut_olculer - set(secilen_olculer))).delete()


def _yeni_gorselleri_kaydet(urun, request):
    """Sürükle-bırak yükleme alanından gelen yeni görselleri galeriye ekler (en sona)."""
    yeni_dosyalar = request.FILES.getlist('images')
    if not yeni_dosyalar:
        return
    mevcut_max = urun.images.order_by('-display_order').first()
    baslangic_sira = (mevcut_max.display_order + 1) if mevcut_max else 0
    for i, dosya in enumerate(yeni_dosyalar):
        ProductImage.objects.create(product=urun, image=dosya, display_order=baslangic_sira + i)


@panel_required
def product_list(request):
    urunler = Product.objects.all().order_by('-created_at')
    return render(request, 'panel/product_list.html', {'urunler': urunler})


@panel_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            urun = form.save()
            _urun_varyasyonlarini_kaydet(urun, form)
            _yeni_gorselleri_kaydet(urun, request)
            if not urun.images.exists():
                messages.warning(request, 'Ürün eklendi ama hiç görsel yüklenmedi - ürün sitede görselsiz görünecek.')
            else:
                messages.success(request, 'Ürün eklendi.')
            return redirect('panel_product_edit', pk=urun.pk)
    else:
        form = ProductForm()
    return render(request, 'panel/product_form.html', {'form': form, 'baslik': 'Yeni Ürün Ekle', 'yeni_urun': True})


@panel_required
def product_edit(request, pk):
    urun = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=urun)
        if form.is_valid():
            form.save()
            _urun_varyasyonlarini_kaydet(urun, form)
            _yeni_gorselleri_kaydet(urun, request)
            messages.success(request, 'Ürün güncellendi.')
            return redirect('panel_product_edit', pk=urun.pk)
    else:
        form = ProductForm(instance=urun)
    return render(
        request,
        'panel/product_form.html',
        {'form': form, 'baslik': f'{urun.name} - Düzenle', 'urun': urun, 'gorseller': urun.images.all()},
    )


@panel_required
def product_delete(request, pk):
    urun = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        urun.delete()
        messages.success(request, 'Ürün silindi.')
        return redirect('panel_product_list')
    return render(
        request,
        'panel/confirm_delete.html',
        {'nesne': urun, 'iptal_url': 'panel_product_list'},
    )


@panel_required
@require_POST
def product_image_delete(request, pk):
    """Tek bir galeri görselini siler. Ürün düzenleme sayfasından AJAX ile çağrılır."""
    gorsel = get_object_or_404(ProductImage, pk=pk)
    urun_pk = gorsel.product_id
    gorsel.delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True})
    messages.success(request, 'Görsel silindi.')
    return redirect('panel_product_edit', pk=urun_pk)


@panel_required
@require_POST
def product_image_reorder(request, pk):
    """
    Sürükle-bırak ile yeni görsel sırasını kaydeder. JS tarafından
    fetch() ile şu gövde gönderilir: {"sira": [gorsel_id1, gorsel_id2, ...]}
    """
    urun = get_object_or_404(Product, pk=pk)
    try:
        veri = json.loads(request.body.decode('utf-8'))
        sira_listesi = veri.get('sira', [])
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({'ok': False, 'hata': 'Geçersiz veri'}, status=400)

    for yeni_sira, gorsel_id in enumerate(sira_listesi):
        ProductImage.objects.filter(pk=gorsel_id, product=urun).update(display_order=yeni_sira)

    return JsonResponse({'ok': True})


# ---------------------------------------------------------------- KATEGORİLER

@panel_required
def category_list(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Kategori eklendi.')
            return redirect('panel_category_list')
    else:
        form = CategoryForm(initial={'display_order': 100})
    kategoriler = Category.objects.all().order_by('display_order', 'name')
    return render(request, 'panel/category_list.html', {'kategoriler': kategoriler, 'form': form})


@panel_required
def category_delete(request, pk):
    kategori = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        kategori.delete()
        messages.success(request, 'Kategori silindi. (Bu kategorideki ürünler kategorisiz kalır, silinmez.)')
        return redirect('panel_category_list')
    return render(
        request,
        'panel/confirm_delete.html',
        {'nesne': kategori, 'iptal_url': 'panel_category_list'},
    )


# ---------------------------------------------------------------- İLETİŞİM TALEPLERİ

@panel_required
def contact_message_list(request):
    mesajlar = ContactMessage.objects.all()
    return render(request, 'panel/contact_message_list.html', {'mesajlar': mesajlar})


@panel_required
@require_POST
def contact_message_mark_read(request, pk):
    mesaj = get_object_or_404(ContactMessage, pk=pk)
    mesaj.is_read = True
    mesaj.save(update_fields=['is_read'])
    return redirect('panel_contact_message_list')


@panel_required
def contact_message_delete(request, pk):
    mesaj = get_object_or_404(ContactMessage, pk=pk)
    if request.method == 'POST':
        mesaj.delete()
        messages.success(request, 'Mesaj silindi.')
        return redirect('panel_contact_message_list')
    return render(
        request,
        'panel/confirm_delete.html',
        {'nesne': mesaj, 'iptal_url': 'panel_contact_message_list'},
    )


@panel_required
def whatsapp_stats(request):
    from django.db.models import Count

    tiklamalar = WhatsAppClick.objects.select_related('product').all()[:200]
    kaynak_dagilimi = WhatsAppClick.objects.values('source').annotate(adet=Count('id')).order_by('-adet')
    context = {
        'tiklamalar': tiklamalar,
        'kaynak_dagilimi': kaynak_dagilimi,
        'toplam': WhatsAppClick.objects.count(),
    }
    return render(request, 'panel/whatsapp_stats.html', context)


# ---------------------------------------------------------------- BLOG

@panel_required
def blog_list(request):
    yazilar = Blog.objects.all().order_by('display_order', '-created_at')
    return render(request, 'panel/blog_list.html', {'yazilar': yazilar})


@panel_required
def blog_create(request):
    if request.method == 'POST':
        form = BlogForm(request.POST, request.FILES)
        if form.is_valid():
            yazi = form.save(commit=False)
            yazi.author = request.user
            yazi.save()
            messages.success(request, 'Blog yazısı eklendi.')
            return redirect('panel_blog_list')
    else:
        form = BlogForm(initial={'display_order': 100})
    return render(request, 'panel/blog_form.html', {'form': form, 'baslik': 'Yeni Blog Yazısı'})


@panel_required
def blog_edit(request, pk):
    yazi = get_object_or_404(Blog, pk=pk)
    if request.method == 'POST':
        form = BlogForm(request.POST, request.FILES, instance=yazi)
        if form.is_valid():
            form.save()
            messages.success(request, 'Blog yazısı güncellendi.')
            return redirect('panel_blog_list')
    else:
        form = BlogForm(instance=yazi)
    return render(request, 'panel/blog_form.html', {'form': form, 'baslik': f'{yazi.title} - Düzenle'})


@panel_required
def blog_delete(request, pk):
    yazi = get_object_or_404(Blog, pk=pk)
    if request.method == 'POST':
        yazi.delete()
        messages.success(request, 'Blog yazısı silindi.')
        return redirect('panel_blog_list')
    return render(
        request,
        'panel/confirm_delete.html',
        {'nesne': yazi, 'iptal_url': 'panel_blog_list'},
    )


# ---------------------------------------------------------------- HABERLER

@panel_required
def news_list(request):
    haberler = News.objects.all().order_by('-created_at')
    return render(request, 'panel/news_list.html', {'haberler': haberler})


@panel_required
def news_create(request):
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES)
        if form.is_valid():
            haber = form.save(commit=False)
            haber.author = request.user
            haber.save()
            messages.success(request, 'Haber eklendi.')
            return redirect('panel_news_list')
    else:
        form = NewsForm()
    return render(request, 'panel/news_form.html', {'form': form, 'baslik': 'Yeni Haber Ekle'})


@panel_required
def news_edit(request, pk):
    haber = get_object_or_404(News, pk=pk)
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES, instance=haber)
        if form.is_valid():
            form.save()
            messages.success(request, 'Haber güncellendi.')
            return redirect('panel_news_list')
    else:
        form = NewsForm(instance=haber)
    return render(request, 'panel/news_form.html', {'form': form, 'baslik': f'{haber.title} - Düzenle'})


@panel_required
def news_delete(request, pk):
    haber = get_object_or_404(News, pk=pk)
    if request.method == 'POST':
        haber.delete()
        messages.success(request, 'Haber silindi.')
        return redirect('panel_news_list')
    return render(
        request,
        'panel/confirm_delete.html',
        {'nesne': haber, 'iptal_url': 'panel_news_list'},
    )
