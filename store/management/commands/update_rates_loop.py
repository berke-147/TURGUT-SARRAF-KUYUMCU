"""
Canlı altın ve döviz kurlarını SÜREKLİ, arka planda belirli aralıklarla çeker.
Ctrl+C ile durdurulana kadar (ya da terminal/pencere kapanana kadar) çalışmaya devam eder.

Kullanım:
    python manage.py update_rates_loop
    python manage.py update_rates_loop --interval 10

Önemli: Bu komut açık bir terminal/komut penceresi gerektirir. Pencereyi
kapatırsan ya da bilgisayar uyku moduna geçerse döngü de durur. Sürekli
çalışması için ya pencereyi açık bırak ya da Windows Görev Zamanlayıcı'da
"oturum açıldığında" tetikleyicisiyle start_rate_updater.bat'ı otomatik
başlat.

Hata takibi: Her denemenin sonucu logs/update_rates.log dosyasına da yazılır.
Fiyatlar donmuş görünüyorsa önce o dosyaya, sonra admin panelindeki
"Son Güncelleme" sütununa bak.
"""
import logging
import time
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from store.services import update_all_rates

MAX_BACKOFF_SECONDS = 300  # art arda hata durumunda bekleme en fazla 5 dakikaya çıksın


def get_logger():
    log_dir = Path(settings.BASE_DIR) / "logs"
    log_dir.mkdir(exist_ok=True)

    logger = logging.getLogger("update_rates_loop")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.FileHandler(log_dir / "update_rates.log", encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(handler)

    return logger


class Command(BaseCommand):
    help = "update_rates'i durmaksızın, belirli aralıklarla arka planda çalıştırır."

    def add_arguments(self, parser):
        parser.add_argument(
            "--interval",
            type=int,
            default=3,
            help="Kaç saniyede bir güncellensin (varsayılan: 3 saniye).",
        )

    def handle(self, *args, **options):
        base_interval = max(options["interval"], 1)
        logger = get_logger()

        self.stdout.write(
            self.style.SUCCESS(
                f"Kur güncelleme döngüsü başladı ({base_interval} saniyede bir). "
                "Durdurmak için Ctrl+C."
            )
        )
        self.stdout.write(
            self.style.WARNING(
                "Not: dovizgrafik.com, gold-api.com ve exchangerate-api.com resmi API "
                "değil / key gerektirmeyen ücretsiz kaynaklardır. 3 saniyede bir tam "
                "sayfa çekmek IP'nin geçici olarak engellenmesine yol açabilir. Art "
                "arda hata alınırsa bekleme süresi otomatik uzatılır (backoff), site "
                "bu sırada son bilinen fiyatları göstermeye devam eder. Detaylar "
                "logs/update_rates.log dosyasında."
            )
        )
        logger.info("Döngü başladı (interval=%ss)", base_interval)

        consecutive_failures = 0

        while True:
            try:
                update_all_rates(log=self.stdout.write)
                if consecutive_failures > 0:
                    logger.info("Toparlandı, %s hatanın ardından güncelleme başarılı.", consecutive_failures)
                consecutive_failures = 0
                logger.info("Güncelleme başarılı.")
                sleep_time = base_interval
            except Exception as exc:
                consecutive_failures += 1
                self.stderr.write(self.style.ERROR(f"Güncelleme hatası: {exc}"))
                logger.error("Güncelleme hatası (%s. art arda): %s", consecutive_failures, exc)

                # Art arda hata alındıkça bekleme süresini kademeli artır (rate-limit'i
                # daha da kötüleştirmemek için). base_interval'den başlayıp katlanarak büyür.
                sleep_time = min(base_interval * (2 ** consecutive_failures), MAX_BACKOFF_SECONDS)
                if consecutive_failures in (1, 3, 6, 10) or consecutive_failures % 20 == 0:
                    self.stdout.write(
                        self.style.WARNING(
                            f"{consecutive_failures} kez art arda hata alındı, "
                            f"bekleme süresi {sleep_time} saniyeye çıkarıldı."
                        )
                    )

            time.sleep(sleep_time)
