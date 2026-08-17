"""
Döviz kalemlerini (USD/EUR/GBP/SAR) veritabanından tamamen siler.

NEDEN GEREKLİ: Site artık döviz göstermiyor - services.py'deki robot bu
kodlar için artık kayıt oluşturmuyor/güncellemiyor (bkz. update_all_rates).
Ancak siteye önceden eklenmiş eski USD/EUR/GBP/SAR kayıtları veritabanında
duruyorsa, panelin "Finansal Veriler" listesinde görünmeye devam eder. Bu
komutu BİR KEZ çalıştırmak o eski kayıtları temizler.

Kullanım:
    python manage.py remove_currency_items
"""
from django.core.management.base import BaseCommand

from store.models import FinancialData

DOVIZ_KODLARI = ["USD", "EUR", "GBP", "SAR"]


class Command(BaseCommand):
    help = "USD/EUR/GBP/SAR döviz kayıtlarını veritabanından siler."

    def handle(self, *args, **options):
        silinen, _ = FinancialData.objects.filter(code__in=DOVIZ_KODLARI).delete()
        self.stdout.write(self.style.SUCCESS(f"{silinen} döviz kaydı silindi."))
