"""
Paylaşımlı hosting için: Cron Job her dakika bu komutu tetikler, komut ise
kendi içinde ~55 saniye boyunca (bir sonraki cron tetiklemesiyle çakışmaması
için 5 saniyelik pay bırakılır) belirli aralıklarla update_all_rates()
çağırıp sonra kendiliğinden sonlanır. Böylece sürekli açık kalan bir process
olmadan (paylaşımlı hosting'ler buna izin vermez), pratikte neredeyse
sürekli/canlı güncelleme elde edilir.

Kullanım (cron job komutu):
    /path/to/venv/bin/python /path/to/manage.py update_rates_burst
    /path/to/venv/bin/python /path/to/manage.py update_rates_burst --interval 3

Cron Job ayarı (cPanel): "Once Per Minute" / "Her Dakika" (* * * * *)
"""
import logging
import time
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from store.services import update_all_rates

MAX_BACKOFF_SECONDS = 60  # tek bir burst içinde hata olursa bekleme en fazla 1 dakika olsun
RUN_BUDGET_SECONDS = 55   # bir sonraki cron tetiklemesiyle çakışmasın diye 5sn pay


def get_logger():
    log_dir = Path(settings.BASE_DIR) / "logs"
    log_dir.mkdir(exist_ok=True)

    logger = logging.getLogger("update_rates_burst")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.FileHandler(log_dir / "update_rates.log", encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(handler)

    return logger


class Command(BaseCommand):
    help = "Cron ile dakikada bir tetiklenip, kendi içinde ~55 saniye boyunca sık sık kur günceller."

    def add_arguments(self, parser):
        parser.add_argument(
            "--interval",
            type=int,
            default=3,
            help="Burst içinde kaç saniyede bir güncellensin (varsayılan: 3 saniye).",
        )

    def handle(self, *args, **options):
        base_interval = max(options["interval"], 1)
        logger = get_logger()

        baslangic = time.monotonic()
        consecutive_failures = 0
        tur = 0

        while (time.monotonic() - baslangic) < RUN_BUDGET_SECONDS:
            tur += 1
            try:
                update_all_rates(log=self.stdout.write)
                if consecutive_failures > 0:
                    logger.info("Toparlandı, %s hatanın ardından güncelleme başarılı.", consecutive_failures)
                consecutive_failures = 0
                sleep_time = base_interval
            except Exception as exc:
                consecutive_failures += 1
                self.stderr.write(self.style.ERROR(f"Güncelleme hatası: {exc}"))
                logger.error("Güncelleme hatası (%s. art arda): %s", consecutive_failures, exc)
                sleep_time = min(base_interval * (2 ** consecutive_failures), MAX_BACKOFF_SECONDS)

            kalan = RUN_BUDGET_SECONDS - (time.monotonic() - baslangic)
            if kalan <= 0:
                break
            time.sleep(min(sleep_time, kalan))

        logger.info("Burst tamamlandı: %s tur çalıştı.", tur)
        self.stdout.write(self.style.SUCCESS(f"Burst tamamlandı: {tur} tur çalıştı."))
