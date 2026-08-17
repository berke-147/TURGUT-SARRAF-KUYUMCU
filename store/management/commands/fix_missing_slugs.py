"""
Boş (slug='') kalmış Ürün/Haber kayıtlarına otomatik, benzersiz bir slug atar.

NEDEN GEREKLİ: News modelinde daha önce otomatik slug üretimi yoktu, bu yüzden
panelden/admin'den eklenen ilk haber(ler) boş slug ile kaydedilmiş olabilir.
Boş slug'lı bir kayıt, ana sayfadaki haber linkini oluştururken hataya (ve
sayfanın tamamen açılamamasına) yol açar. Bu komut TEK SEFERLİK çalıştırılıp
mevcut bozuk kayıtları düzeltir. Bundan sonra yeni eklenen ürün/haberler zaten
otomatik doğru slug alır (models.py'deki save() metodu sayesinde).

Kullanım:
    python manage.py fix_missing_slugs
"""
from django.core.management.base import BaseCommand

from store.models import News, Product


class Command(BaseCommand):
    help = "slug alanı boş kalmış Ürün/Haber kayıtlarını düzeltir."

    def handle(self, *args, **options):
        toplam = 0
        for model_sinifi, etiket in ((News, "haber"), (Product, "ürün")):
            bozuk_kayitlar = model_sinifi.objects.filter(slug="")
            for kayit in bozuk_kayitlar:
                kayit.save()  # save() içindeki mantık otomatik slug üretir
                toplam += 1
                self.stdout.write(f"  - {etiket} düzeltildi: {kayit}")

        if toplam == 0:
            self.stdout.write(self.style.SUCCESS("Düzeltilecek bozuk kayıt bulunamadı, her şey yolunda."))
        else:
            self.stdout.write(self.style.SUCCESS(f"{toplam} kayıt düzeltildi."))
