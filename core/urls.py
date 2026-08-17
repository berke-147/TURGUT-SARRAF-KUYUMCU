from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve as static_serve
from store.views import home_page, robots_txt # Az önce yazdığımız fonksiyonları çağırdık
from store.sitemaps import StaticViewSitemap, ProductSitemap, NewsSitemap, BlogSitemap

sitemaps = {
    'static': StaticViewSitemap,
    'urunler': ProductSitemap,
    'haberler': NewsSitemap,
    'blog': BlogSitemap,
}

urlpatterns = [
    # Django'nun kendi admin paneli. Tahmin edilmesi zor olsun diye
    # standart "admin/" yerine bu adrese taşındı. Buraya sadece
    # sell_multiplier gibi ince ayarlar veya kur verisini elle düzeltmek
    # için ihtiyaç duyarsın; günlük ürün/haber girişi için /panel/ kullan.
    path('yonetim-9f3k2/', admin.site.urls),
    path('', home_page, name='home'), # Normal Kullanıcı (Ana Sayfa) girişi
    path('', include('store.urls')), # Ürün, haber, çevirici ve panel sayfaları

    # SEO: arama motorları bu iki adresi otomatik arar.
    path('robots.txt', robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
]

# Ürün/haber resimlerinin (medya dosyaları) görünmesi için.
# NOT: Statik dosyalar (CSS/JS) WhiteNoise middleware tarafından otomatik
# sunuluyor (bkz. settings.py). Medya dosyaları (kullanıcı yüklediği resimler)
# WhiteNoise kapsamında değildir, bu yüzden DEBUG=False olsa bile burada
# Django üzerinden sunuluyor - küçük/orta ölçekli bir site için performans
# sorun teşkil etmez.
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', static_serve, {'document_root': settings.MEDIA_ROOT}),
]