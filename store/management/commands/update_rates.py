"""
Canlı altın ve döviz kurlarını TEK SEFERLİK çekip FinancialData tablosunu günceller.

Kullanım:
    python manage.py update_rates

Sürekli, arka planda kendiliğinden çalışması için update_rates_loop komutunu kullan.
"""
from django.core.management.base import BaseCommand

from store.services import update_all_rates


class Command(BaseCommand):
    help = "Canlı altın (24-22-14-8 ayar) ve döviz (USD, EUR, GBP) kurlarını tek seferlik çeker."

    def handle(self, *args, **options):
        try:
            update_all_rates(log=self.stdout.write)
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Kurlar güncellenemedi: {exc}"))
            return

        self.stdout.write(self.style.SUCCESS("Tüm kurlar güncellendi."))
