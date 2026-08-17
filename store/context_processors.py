"""
Her sayfada (base.html içinde) kullanılabilecek SEO/pazarlama ayarlarını
şablonlara taşır. Bu sayede her view fonksiyonuna tek tek context eklemek
gerekmez - settings.py'deki değerler otomatik olarak her template'te
{{ ga4_measurement_id }}, {{ business_name }} gibi hazır gelir.
"""
from django.conf import settings


def seo_settings(request):
    return {
        'site_domain': getattr(settings, 'SITE_DOMAIN', ''),
        'ga4_measurement_id': getattr(settings, 'GA4_MEASUREMENT_ID', ''),
        'google_site_verification': getattr(settings, 'GOOGLE_SITE_VERIFICATION', ''),
        'business_name': getattr(settings, 'BUSINESS_NAME', ''),
        'business_phone': getattr(settings, 'BUSINESS_PHONE', ''),
        'business_street_address': getattr(settings, 'BUSINESS_STREET_ADDRESS', ''),
        'business_city': getattr(settings, 'BUSINESS_CITY', ''),
        'business_postal_code': getattr(settings, 'BUSINESS_POSTAL_CODE', ''),
        'business_latitude': getattr(settings, 'BUSINESS_LATITUDE', ''),
        'business_longitude': getattr(settings, 'BUSINESS_LONGITUDE', ''),
        'business_maps_url': (
            f"https://www.google.com/maps/search/?api=1&query="
            f"{getattr(settings, 'BUSINESS_LATITUDE', '')},{getattr(settings, 'BUSINESS_LONGITUDE', '')}"
        ),
        'whatsapp_number': getattr(settings, 'WHATSAPP_NUMBER', ''),
    }
