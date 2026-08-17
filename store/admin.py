from django.contrib import admin
from .models import (
    FinancialData, Product, News, Category,
    ProductImage, ProductColorOption, ProductSizeOption,
    ContactMessage, WhatsAppClick, Blog,
)

# 1. FİNANSAL VERİ YÖNETİMİ (Döviz & Sarrafiye)
@admin.register(FinancialData)
class FinancialDataAdmin(admin.ModelAdmin):
    # Listede görünecek sütunlar
    list_display = (
        'code', 'name', 'buy_price', 'sell_price', 'degisim_goster',
        'buy_multiplier', 'sell_multiplier', 'sitedeki_alis_goster', 'sitedeki_satis_goster',
        'is_visible', 'display_order', 'updated_at',
    )

    search_fields = ('name', 'code')
    list_filter = ('is_visible',)

    # Çarpanlar, görünürlük ve sıra buradan hızlıca düzenlenebilir.
    list_editable = ('buy_multiplier', 'sell_multiplier', 'is_visible', 'display_order')

    # Robotun tanıdığı kodlarda alış/satış fiyatı zaten otomatik güncellenir;
    # yine de gerekirse (özel/manuel kalemlerde) elle değiştirilebilsin diye
    # bu ikisi artık salt-okunur DEĞİL. previous_sell_price ve updated_at
    # sadece bilgi amaçlı olduğu için salt-okunur kalıyor.
    readonly_fields = ('previous_sell_price', 'updated_at')

    def degisim_goster(self, obj):
        yuzde = obj.change_percent
        isaret = "+" if yuzde > 0 else ""
        return f"{isaret}{yuzde}%"

    degisim_goster.short_description = "Değişim"

    def sitedeki_alis_goster(self, obj):
        return f"{obj.final_buy_price} TL"

    sitedeki_alis_goster.short_description = "Sitede Görünecek Alış"

    def sitedeki_satis_goster(self, obj):
        return f"{obj.final_sell_price} TL"

    sitedeki_satis_goster.short_description = "Sitede Görünecek Satış"


# 2. KATEGORİ YÖNETİMİ
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_order')
    list_editable = ('display_order',)
    prepopulated_fields = {'slug': ('name',)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductColorOptionInline(admin.TabularInline):
    model = ProductColorOption
    extra = 0


class ProductSizeOptionInline(admin.TabularInline):
    model = ProductSizeOption
    extra = 0


# 3. ÜRÜN YÖNETİMİ (Bilezik, Kolye, Saat vb.)
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # Listede görünecek sütunlar
    list_display = (
        'name', 'category', 'sku', 'product_type', 'purity', 'weight_gram',
        'labor_cost', 'price_multiplier', 'fixed_price', 'hesaplanan_fiyat_goster', 'is_active',
    )

    # Filtreleme ve Arama
    list_filter = ('product_type', 'purity', 'category', 'stone_type', 'is_active')
    search_fields = ('name', 'sku')

    # Otomatik URL oluşturma
    prepopulated_fields = {'slug': ('name',)}

    # Listeden hızlı düzenleme (Fiyat Çarpanı, Sabit Fiyat ve Yayım Durumu)
    list_editable = ('price_multiplier', 'fixed_price', 'is_active')

    inlines = [ProductImageInline, ProductColorOptionInline, ProductSizeOptionInline]

    # Özel Fonksiyon: (Has Altın x Milyem x Gram + İşçilik) x Çarpan sonucunu gösterir
    def hesaplanan_fiyat_goster(self, obj):
        fiyat = obj.hesapla_fiyat
        if fiyat == 0:
            return "Kur Bekleniyor"
        return f"{fiyat} TL"

    hesaplanan_fiyat_goster.short_description = "Sitedeki Anlık Fiyat"


# 4. İLETİŞİM MESAJLARI
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'is_read', 'created_at')
    list_filter = ('is_read',)
    search_fields = ('name', 'phone', 'email', 'message')
    list_editable = ('is_read',)


# 5. WHATSAPP TIKLAMA İSTATİSTİĞİ (salt-okunur - robot/kullanıcı otomatik oluşturur)
@admin.register(WhatsAppClick)
class WhatsAppClickAdmin(admin.ModelAdmin):
    list_display = ('source', 'product', 'created_at')
    list_filter = ('source',)
    readonly_fields = ('source', 'product', 'created_at')

    def has_add_permission(self, request):
        return False


# 6. HABER YÖNETİMİ
@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'is_published', 'created_at')
    list_filter = ('category', 'is_published')
    search_fields = ('title', 'content')


# 7. BLOG YÖNETİMİ
@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'display_order', 'is_published', 'created_at')
    list_filter = ('is_published',)
    list_editable = ('display_order',)
    search_fields = ('title', 'content', 'excerpt')
    prepopulated_fields = {'slug': ('title',)}