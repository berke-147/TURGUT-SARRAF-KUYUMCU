from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
import decimal # Hesaplama yaparken kuruş hatası olmaması için gerekli


def benzersiz_slug_uret(model_sinifi, kaynak_metin, mevcut_pk=None):
    """
    Verilen metinden (ör. ürün/haber başlığı) benzersiz bir slug üretir.
    Aynı isimde birden fazla kayıt oluşturulursa (ör. iki haber aynı başlıkla
    kaydedilirse) sonuna -2, -3 gibi bir sayı ekleyerek UNIQUE hatasını önler.
    """
    taban_slug = slugify(kaynak_metin) or "kayit"
    slug = taban_slug
    sayac = 2

    sorgu = model_sinifi.objects.filter(slug=slug)
    if mevcut_pk:
        sorgu = sorgu.exclude(pk=mevcut_pk)

    while sorgu.exists():
        slug = f"{taban_slug}-{sayac}"
        sayac += 1
        sorgu = model_sinifi.objects.filter(slug=slug)
        if mevcut_pk:
            sorgu = sorgu.exclude(pk=mevcut_pk)

    return slug

# 1. FİNANSAL VERİ MODELİ (Canlı Altın/Döviz Kurları)
class FinancialData(models.Model):
    # Kod: USD, EUR, HAS, CEYREK
    code = models.CharField(max_length=10, unique=True, verbose_name="Para/Altın Kodu")
    name = models.CharField(max_length=50, verbose_name="Görünen Ad")
    
    # ROBOTUN DOLDURACAĞI HAM PİYASA FİYATLARI
    buy_price = models.DecimalField(max_digits=10, decimal_places=4, default=0, verbose_name="Piyasa Alış")
    sell_price = models.DecimalField(max_digits=10, decimal_places=4, default=0, verbose_name="Piyasa Satış")

    # Bir önceki GÜNÜN son fiyatı - %değişim (change_percent) buna göre hesaplanır.
    # Borsa panolarındaki "bir önceki kapanışa göre değişim" mantığıyla aynıdır:
    # gün içinde SABİT kalır, sadece günün İLK güncellemesinde yenilenir
    # (bkz. services.py -> upsert()). Son 3 saniyedeki tik'e göre DEĞİL,
    # dünkü son bilinen fiyata göre kıyaslama yapar.
    previous_sell_price = models.DecimalField(max_digits=10, decimal_places=4, default=0, verbose_name="Önceki Gün Kapanış Fiyatı")

    # ÇARPAN (yüzde DEĞİL) - SATIŞ tarafı. Sitede gösterilen satış fiyatı,
    # ham satış fiyatının bu sayıyla DOĞRUDAN çarpımıdır (final = sell_price * sell_multiplier).
    # Örnek: has altını 0,916 ile çarparsan 22 ayar karşılığını bulursun;
    # 1,05 yazarsan ham fiyatın üzerine %5 eklenir; 1 yazarsan hiç değişmez.
    sell_multiplier = models.DecimalField(max_digits=8, decimal_places=4, default=1, verbose_name="Satış Çarpanı")

    # ÇARPAN (yüzde DEĞİL) - ALIŞ tarafı. Dükkanın müşteriden alırken
    # uyguladığı ayarlama. Genelde 1'den küçük girilir (ör. 0,98 yazarsan ham
    # alıştan %2 düşük gösterilir). 1 yazarsan hiç değişiklik yapılmaz.
    buy_multiplier = models.DecimalField(max_digits=8, decimal_places=4, default=1, verbose_name="Alış Çarpanı")

    # Piyasa Durumu sayfasında gösterilsin mi? Kapatırsan kalem sitede
    # (piyasa durumu, çevirici, ana sayfa) hiçbir yerde görünmez ama veri
    # veritabanında kalmaya devam eder.
    is_visible = models.BooleanField(default=True, verbose_name="Sitede Göster")

    # Piyasa Durumu tablosunda sıralama - küçük sayı önce gösterilir.
    display_order = models.IntegerField(default=100, verbose_name="Sıra (küçük sayı önce gösterilir)")

    updated_at = models.DateTimeField(auto_now=True, verbose_name="Son Güncelleme")

    class Meta:
        verbose_name = "Finansal Veri (Otomatik)"
        verbose_name_plural = "Finansal Veriler"
        ordering = ['display_order', 'name']

    def __str__(self):
        return f"{self.name} - x{self.sell_multiplier}"

    # SİTEDE GÖRÜNECEK NİHAİ SATIŞ FİYATI = Ham Satış Fiyatı x Çarpan
    @property
    def final_sell_price(self):
        if self.sell_price is None or self.sell_price == 0:
            return decimal.Decimal('0')
        # Örn: 100 TL * 1,05 = 105 TL ; 100 TL * 0,916 = 91,6 TL
        return round(self.sell_price * decimal.Decimal(str(self.sell_multiplier)), 4)

    # SİTEDE GÖRÜNECEK NİHAİ ALIŞ FİYATI = Ham Alış Fiyatı x Çarpan
    @property
    def final_buy_price(self):
        if self.buy_price is None or self.buy_price == 0:
            return decimal.Decimal('0')
        return round(self.buy_price * decimal.Decimal(str(self.buy_multiplier)), 4)

    # BİR ÖNCEKİ GÜNÜN SON FİYATINA GÖRE YÜZDESEL DEĞİŞİM (borsadaki "önceki kapanışa göre" mantığı)
    @property
    def change_percent(self):
        if not self.previous_sell_price:
            return decimal.Decimal('0')
        try:
            degisim = ((self.sell_price - self.previous_sell_price) / self.previous_sell_price) * 100
            return round(degisim, 2)
        except (ZeroDivisionError, decimal.InvalidOperation):
            return decimal.Decimal('0')

    # BİR ÖNCEKİ GÜNÜN SON FİYATINA GÖRE TL CİNSİNDEN FARK (piyasa panolarındaki "Fark" sütunu)
    # Hem yeni hem eski fiyata AYNI çarpan uygulanarak hesaplanır ki sitede
    # gösterilen (çarpanlı) fiyatla tutarlı olsun.
    @property
    def change_amount(self):
        if not self.previous_sell_price:
            return decimal.Decimal('0')
        try:
            onceki_final = round(self.previous_sell_price * self.sell_multiplier, 4)
            return round(self.final_sell_price - onceki_final, 2)
        except (decimal.InvalidOperation, TypeError):
            return decimal.Decimal('0')


# 1B. ÜRÜN KATEGORİSİ (Yüzük, Kolye, Bilezik, Küpe, Saat vb.)
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Kategori Adı")
    slug = models.SlugField(unique=True, blank=True, verbose_name="URL Yolu (Otomatik)")
    display_order = models.IntegerField(default=100, verbose_name="Sıra (küçük sayı önce gösterilir)")

    class Meta:
        verbose_name = "Kategori"
        verbose_name_plural = "Kategoriler"
        ordering = ['display_order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = benzersiz_slug_uret(Category, self.name, self.pk)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# 2. ÜRÜN MODELİ (Kuyumcu Ürünleri - Dinamik ya da Sabit Fiyatlı)
class Product(models.Model):
    AYAR_SECENEKLERI = [
        (24, '24 Ayar (Has)'),
        (22, '22 Ayar'),
        (14, '14 Ayar'),
        (8, '8 Ayar'),
    ]

    URUN_TIPI_SECENEKLERI = [
        ('iscilikli', 'İşçilikli Ürün (Altın - Gramaj/Ayar ile hesaplanır)'),
        ('sabit', 'Sabit Fiyatlı Ürün (Saat, Aksesuar vb.)'),
    ]

    TAS_TURU_SECENEKLERI = [
        ('tassiz', 'Taşsız'),
        ('pirlanta', 'Pırlanta'),
        ('zirkon', 'Zirkon'),
        ('yakut', 'Yakut'),
        ('zumrut', 'Zümrüt'),
        ('safir', 'Safir'),
        ('inci', 'İnci'),
        ('diger', 'Diğer'),
    ]

    name = models.CharField(max_length=200, verbose_name="Ürün Adı")
    slug = models.SlugField(unique=True, blank=True, verbose_name="URL Yolu (Otomatik)")
    description = models.TextField(blank=True, verbose_name="Ürün Açıklaması")

    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='urunler', verbose_name="Kategori",
    )

    # Stok kodu - panelde takip için, sitede de rozet olarak gösterilebilir.
    sku = models.CharField(max_length=50, blank=True, verbose_name="Stok Kodu (SKU)")

    stone_type = models.CharField(
        max_length=20, choices=TAS_TURU_SECENEKLERI, default='tassiz', blank=True, verbose_name="Taş Türü"
    )

    # Ürün tipi: işçilikli (altın, kura göre canlı hesaplanır) ya da sabit (saat vb., elle girilen fiyat)
    product_type = models.CharField(
        max_length=10, choices=URUN_TIPI_SECENEKLERI, default='iscilikli', verbose_name="Ürün Tipi"
    )

    # Hesaplama Algoritması Verileri (SADECE işçilikli ürünlerde kullanılır)
    weight_gram = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True, verbose_name="Gramaj"
    )
    purity = models.IntegerField(choices=AYAR_SECENEKLERI, null=True, blank=True, verbose_name="Ayar")

    # İşçilik maliyeti - SABİT bir TL tutarıdır (yüzde/çarpan DEĞİL), ham
    # maden maliyetinin üzerine olduğu gibi eklenir. SADECE işçilikli
    # ürünlerde kullanılır.
    labor_cost = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="İşçilik Maliyeti (TL)"
    )

    # Ürün bazlı ÇARPAN (yüzde DEĞİL) - SADECE işçilikli ürünlerde kullanılır.
    # Fiyat = (Has Altın Kuru x Milyem x Gram + İşçilik) x Çarpan. Örn: 1,15
    # yazarsan ham maliyetin üzerine %15 kar eklenir; 1 yazarsan hiç eklenmez.
    price_multiplier = models.DecimalField(max_digits=8, decimal_places=4, default=1, verbose_name="Fiyat Çarpanı")

    # SADECE sabit fiyatlı ürünlerde kullanılır (saat, aksesuar vb.)
    fixed_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Sabit Satış Fiyatı (TL)"
    )

    is_active = models.BooleanField(default=True, verbose_name="Yayında mı?")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ürün"
        verbose_name_plural = "Ürünler"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = benzersiz_slug_uret(Product, self.name, self.pk)
        super().save(*args, **kwargs)

    def __str__(self):
        if self.product_type == 'sabit':
            return f"{self.name} - {self.fixed_price} TL (sabit)"
        return f"{self.name} - x{self.price_multiplier}"

    # Ürün listesinde/kartlarda gösterilecek kapak (ilk sıradaki) görsel.
    @property
    def kapak_gorseli(self):
        ilk = self.images.first()
        return ilk.image if ilk else None

    # Renk/ölçü varyasyonu var mı? Panelde bu ürün için hiç eklenmemişse
    # sitede o seçim alanı hiç gösterilmez (ürün bazlı OPSİYONEL varyasyon).
    @property
    def renk_var_mi(self):
        return self.renk_secenekleri.exists()

    @property
    def olcu_var_mi(self):
        return self.olcu_secenekleri.exists()

    # --- CANLI FİYAT HESAPLAMA MOTORU ---
    # İşçilikli ürün: (Has Altın Kuru * Milyem * Gram + İşçilik) * Çarpan, altın kuru değiştikçe canlı değişir.
    # Sabit fiyatlı ürün (saat vb.): panelden girilen fiyat aynen gösterilir, kurdan etkilenmez.
    @property
    def hesapla_fiyat(self):
        if self.product_type == 'sabit':
            return round(self.fixed_price, 2) if self.fixed_price else 0

        try:
            # 1. 'HAS' kodlu altının HAM piyasa fiyatını çekiyoruz
            # Ürünlerde kendi çarpanımız olduğu için, altının ham halini kullanıyoruz.
            has_altin = FinancialData.objects.get(code='HAS')
            guncel_kur = has_altin.sell_price

            # 2. Milyem Çarpanı
            milyem_oranlari = {
                24: 1.000,
                22: 0.916,
                14: 0.585,
                8: 0.333
            }
            milyem_carpani = milyem_oranlari.get(self.purity, 1)

            # 3. HAM MALİYET: Kur x Milyem x Gram
            ham_maliyet = (guncel_kur * decimal.Decimal(milyem_carpani) * (self.weight_gram or 0))

            # 4. SATIŞ FİYATI: (Ham Maliyet + İşçilik) x Fiyat Çarpanı
            satis_fiyati = (ham_maliyet + (self.labor_cost or 0)) * self.price_multiplier

            return round(satis_fiyati, 2)

        except FinancialData.DoesNotExist:
            return 0
        except Exception:
            return 0


# 2B. ÜRÜN GÖRSEL GALERİSİ (Sürükle-bırak sıralanabilir, çoklu görsel)
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name="Ürün")
    image = models.ImageField(upload_to='products/', verbose_name="Görsel")
    display_order = models.IntegerField(default=0, verbose_name="Sıra")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ürün Görseli"
        verbose_name_plural = "Ürün Görselleri"
        ordering = ['display_order', 'id']

    def __str__(self):
        return f"{self.product.name} - Görsel #{self.display_order}"


# 2C. RENK VARYASYONU (opsiyonel - ürün bazlı, admin hangi renklerin
# mevcut olduğunu işaretler; hiç eklenmezse sitede renk seçimi görünmez)
class ProductColorOption(models.Model):
    RENK_SECENEKLERI = [
        ('sari', 'Sarı Altın'),
        ('beyaz', 'Beyaz Altın'),
        ('rose', 'Rose Gold'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='renk_secenekleri', verbose_name="Ürün")
    renk = models.CharField(max_length=10, choices=RENK_SECENEKLERI, verbose_name="Renk")

    class Meta:
        verbose_name = "Renk Seçeneği"
        verbose_name_plural = "Renk Seçenekleri"
        unique_together = ('product', 'renk')
        ordering = ['renk']

    def __str__(self):
        return self.get_renk_display()


# 2D. ÖLÇÜ VARYASYONU (opsiyonel - ürün bazlı, ör. yüzük ölçüsü)
class ProductSizeOption(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='olcu_secenekleri', verbose_name="Ürün")
    olcu = models.CharField(max_length=10, verbose_name="Ölçü")
    stokta_var = models.BooleanField(default=True, verbose_name="Stokta Var")

    class Meta:
        verbose_name = "Ölçü Seçeneği"
        verbose_name_plural = "Ölçü Seçenekleri"
        unique_together = ('product', 'olcu')
        ordering = ['olcu']

    def __str__(self):
        return self.olcu


# 3. HABER VE MEDYA MODELİ
class News(models.Model):
    CATEGORY_CHOICES = [
        ('news', 'Piyasa Haberi'),
        ('note', 'Piyasa Notu'),
    ]

    title = models.CharField(max_length=200, verbose_name="Başlık")
    slug = models.SlugField(unique=True, blank=True)
    content = models.TextField(verbose_name="İçerik")
    image = models.ImageField(upload_to='news/', blank=True, null=True, verbose_name="Haber Görseli")
    
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Yazar")
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='news', verbose_name="Kategori")
    
    is_published = models.BooleanField(default=True, verbose_name="Yayında")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Tarih")

    class Meta:
        verbose_name = "Haber/Not"
        verbose_name_plural = "Haberler ve Notlar"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = benzersiz_slug_uret(News, self.title, self.pk)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


# 3B. BLOG (Piyasa haberlerinden ayrı - bakım/stil/rehber tarzı yazılar).
# News modelinden bilinçli olarak ayrı tutuldu: News "Piyasa Haberi/Notu"
# eksenli, Blog ise "Altın Takı Bakımı", "Yüzük Ölçüsü Nasıl Ölçülür" gibi
# zamana bağlı olmayan, uzun ömürlü editoryal içerikler için.
class Blog(models.Model):
    title = models.CharField(max_length=200, verbose_name="Başlık")
    slug = models.SlugField(unique=True, blank=True, verbose_name="URL Yolu (Otomatik)")
    excerpt = models.CharField(
        max_length=240, blank=True, verbose_name="Kısa Özet",
        help_text="Kart görünümünde başlığın altında gösterilir. Boş bırakırsan içerikten otomatik kısaltılır."
    )
    content = models.TextField(verbose_name="İçerik")
    cover_image = models.ImageField(upload_to='blog/', blank=True, null=True, verbose_name="Kapak Görseli")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Yazar")
    is_published = models.BooleanField(default=True, verbose_name="Yayında")
    display_order = models.IntegerField(
        default=100, verbose_name="Sıra (küçük sayı önce gösterilir, ana sayfa vitrini için)"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Tarih")

    class Meta:
        verbose_name = "Blog Yazısı"
        verbose_name_plural = "Blog Yazıları"
        ordering = ['display_order', '-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = benzersiz_slug_uret(Blog, self.title, self.pk)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def ozet_goster(self):
        if self.excerpt:
            return self.excerpt
        from django.utils.text import Truncator
        return Truncator(self.content).words(28)


# 4. İLETİŞİM MESAJLARI (İletişim formundan gelen talepler)
class ContactMessage(models.Model):
    name = models.CharField(max_length=100, verbose_name="Ad Soyad")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Telefon")
    email = models.EmailField(blank=True, verbose_name="E-posta")
    message = models.TextField(verbose_name="Mesaj")
    is_read = models.BooleanField(default=False, verbose_name="Okundu mu?")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Tarih")

    class Meta:
        verbose_name = "İletişim Mesajı"
        verbose_name_plural = "İletişim Mesajları"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.created_at:%d.%m.%Y %H:%M}"


# 5. WHATSAPP TIKLAMA KAYDI (istatistik için)
class WhatsAppClick(models.Model):
    KAYNAK_SECENEKLERI = [
        ('urun_detay', 'Ürün Detay'),
        ('iletisim', 'İletişim Sayfası'),
        ('genel', 'Site Geneli (Yüzen Buton)'),
    ]

    source = models.CharField(max_length=20, choices=KAYNAK_SECENEKLERI, default='genel', verbose_name="Kaynak")
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="İlgili Ürün"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Tarih")

    class Meta:
        verbose_name = "WhatsApp Tıklaması"
        verbose_name_plural = "WhatsApp Tıklamaları"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_source_display()} - {self.created_at:%d.%m.%Y %H:%M}"