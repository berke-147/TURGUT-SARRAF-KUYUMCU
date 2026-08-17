"""
Alış/satış çarpanlarını 1'e (yani "değişiklik yok" durumuna) sıfırlar.

NEDEN GEREKLİ: gerçek zamanlı kaynak (dovizgrafik.com/altin) entegrasyonundan
ÖNCE, çeyrek/yarım/tam/ata/gremse gibi sikkeler "yaklaşık hesap" modundaydı ve
robot her seferinde tipik bir piyasa priminin eşdeğerini otomatik olarak
çarpan alanına yazıyordu. Artık bu kalemlerin çoğu dovizgrafik.com/altin'den
GERÇEK fiyatla çekiliyor ve o gerçek fiyatın üzerine eski otomatik çarpan hâlâ
duruyorsa, sitedeki fiyat gerçek piyasa fiyatından daha yüksek görünür (prim
iki kere uygulanmış olur). Bu komutu BİR KEZ çalıştırmak tüm kalemlerin
çarpanını 1'e (etkisiz) çeker, böylece sitedeki fiyat tekrar kaynakla birebir
eşleşir.

Bundan sonra istersen /panel/finansal/ üzerinden istediğin kalemlere kendi
çarpanını elle girebilirsin (ör. 1,05 = %5 zam, 0,916 = 22 ayar karşılığı) —
bu değer artık robot tarafından bir daha otomatik değiştirilmez/sıfırlanmaz.

Kullanım:
    python manage.py reset_margins
"""
from django.core.management.base import BaseCommand

from store.models import FinancialData


class Command(BaseCommand):
    help = "Tüm FinancialData kayıtlarının alış/satış çarpanını 1'e (etkisiz) sıfırlar."

    def handle(self, *args, **options):
        guncellenen = (
            FinancialData.objects.exclude(sell_multiplier=1, buy_multiplier=1)
            .update(sell_multiplier=1, buy_multiplier=1)
        )
        self.stdout.write(
            self.style.SUCCESS(f"{guncellenen} kalemin çarpanı 1'e sıfırlandı. Fiyatlar artık ham/çekilen değerle birebir aynı.")
        )
