from pathlib import Path
from decouple import config, Csv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# GÜVENLİK AYARLARI
# Bu değerler artık kod içinde değil, .env dosyasında tutulur.
# Yerelde çalışman için hazır bir .env dosyası oluşturuldu.
# Canlıya alırken .env.example dosyasındaki talimatları izle.
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='', cast=Csv())

# UYGULAMALAR
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',  # sitemap.xml otomatik üretimi için (SEO)

    # Senin uygulaman
    'store',
]

# ARA KATMANLAR (MIDDLEWARE)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise: statik dosyaları (CSS/JS) Django'nun kendisi üzerinden sunar.
    # Sunucu (Apache/LiteSpeed/.htaccess) ayarından bağımsız çalışır - hosting
    # statik dosyaları doğrudan servis etmese/edemese bile CSS/JS her zaman gelir.
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# URL YÖNLENDİRİCİSİ (Sende eksik olan en kritik kısım burasıydı)
ROOT_URLCONF = 'core.urls'

# ŞABLON AYARLARI (TEMPLATES)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'store.context_processors.seo_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# VERİTABANI AYARLARI (Sende eksik olan diğer kritik kısım)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ŞİFRE DOĞRULAMA (Varsayılan)
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# DİL VE SAAT AYARLARI
LANGUAGE_CODE = 'tr-tr'  # Türkçe yaptık
TIME_ZONE = 'Europe/Istanbul' # Türkiye saati
USE_I18N = True
USE_TZ = True

# STATİK VE MEDYA DOSYALARI
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
# 'python manage.py collectstatic' komutu dosyaları buraya toplar (canlıda kullanılır)
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise'a statik dosyaları sıkıştırarak sunmasını söylüyoruz (manifest/hash
# kullanmıyoruz ki eksik bir dosya referansı hata fırlatmasın - daha güvenli).
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# Kuyumcu ürün resimleri için
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Dükkan sahibi paneli (/panel/) için: giriş yapmamış biri panel
# sayfalarından birine gitmeye çalışırsa buraya yönlendirilir.
LOGIN_URL = 'panel_login'

# ------------------------------------------------------------------
# SEO / PAZARLAMA AYARLARI
# Aşağıdakilerin çoğu boş bırakılabilir - değeri yoksa ilgili özellik
# (GA4 script'i, Search Console doğrulama etiketi, işletme adresi vb.)
# sayfada hiç görünmez, hataya yol açmaz. Bir değeri doldurmak için .env
# dosyasına (yerelde) ya da cPanel Environment Variables'a (canlıda) ekleyip
# SAVE/Restart yapman yeterli - kod değişikliği gerekmez.
# ------------------------------------------------------------------
SITE_DOMAIN = config('SITE_DOMAIN', default='https://turgutsarraf.com')

# Google Analytics 4 ölçüm kimliği (ör. G-XXXXXXXXXX). analytics.google.com'da
# hesap/mülk oluşturup "Veri Akışı" bölümünden alınır.
GA4_MEASUREMENT_ID = config('GA4_MEASUREMENT_ID', default='')

# Google Search Console site sahipliği doğrulama kodu (HTML etiket yöntemi).
# search.google.com/search-console adresinde site eklerken "HTML etiketi"
# seçeneğinde verilen content="..." değerinin İÇİNDEKİ kodu buraya yapıştır.
GOOGLE_SITE_VERIFICATION = config('GOOGLE_SITE_VERIFICATION', default='')

# LocalBusiness (Google'da işletme bilgisi/zengin sonuç) için mağaza bilgileri.
# Varsayılanlar gerçek mağaza bilgileriyle dolduruldu; canlıda farklı bir
# değer gerekirse cPanel Environment Variables üzerinden ezilebilir.
BUSINESS_NAME = config('BUSINESS_NAME', default='Turgut Sarraf Kuyumculuk')
BUSINESS_PHONE = config('BUSINESS_PHONE', default='0533 363 3220')
BUSINESS_STREET_ADDRESS = config('BUSINESS_STREET_ADDRESS', default="Karaayvatlar Mahallesi, Cumhuriyet Caddesi No:15")
BUSINESS_CITY = config('BUSINESS_CITY', default='Bucak/Burdur')
BUSINESS_POSTAL_CODE = config('BUSINESS_POSTAL_CODE', default='')

# Mağaza konumu (Google Haritalar'da "yol tarifi al" bağlantısı ve
# LocalBusiness şemasındaki geo koordinatları için). Koordinatlar
# 37°27'24.8"N, 30°35'41.9"E ondalık dereceye çevrilerek girildi.
BUSINESS_LATITUDE = config('BUSINESS_LATITUDE', default='37.456889')
BUSINESS_LONGITUDE = config('BUSINESS_LONGITUDE', default='30.594972')

# WhatsApp yönlendirme/tıklama takibi için mağaza WhatsApp numarası.
# uluslararası format, boşluksuz/artısız (ör. 905333633220).
WHATSAPP_NUMBER = config('WHATSAPP_NUMBER', default='905333633220')

# ------------------------------------------------------------------
# CANLI ORTAM (PRODUCTION) GÜVENLİK AYARLARI
# DEBUG=False olduğunda (yani .env'de DEBUG=False yazdığında) devreye girer.
# Yerelde (DEBUG=True) hiçbir etkisi yoktur, http ile çalışmaya devam edersin.
# ------------------------------------------------------------------
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'