# Generated manually - % kar marjı sistemini çarpan (x) sistemine çevirir.
#
# NEDEN: Yüzdelik hesap (final = ham_fiyat * (1 + %/100)) hassas altın/gümüş
# rakamlarında kafa karıştırıcı olabiliyor. Bunun yerine admin artık DOĞRUDAN
# bir çarpan giriyor (final = ham_fiyat * çarpan) - tıpkı milyem hesabındaki
# "has altın x 0,916" mantığı gibi. 1 = değişiklik yok, 1.05 = %5 zam,
# 0.98 = %2 iskonto gibi düşünülebilir ama artık gerçek işlem çarpmadır.
#
# Mevcut kayıtlardaki eski % değerleri (profit_margin/buy_margin) KAYBOLMAZ -
# aşağıdaki veri taşıma adımı her birini otomatik olarak eşdeğer çarpana
# çevirir (ör. %5 -> 1.05), yani admin panelden girilmiş ayarlar bu
# güncellemeden sonra da AYNI fiyatı üretmeye devam eder.

import decimal

from django.db import migrations, models


def yuzdeyi_carpana_cevir(apps, schema_editor):
    FinancialData = apps.get_model('store', 'FinancialData')
    Product = apps.get_model('store', 'Product')

    for kalem in FinancialData.objects.all():
        kalem.sell_multiplier = decimal.Decimal('1') + (kalem.profit_margin / decimal.Decimal('100'))
        kalem.buy_multiplier = decimal.Decimal('1') + (kalem.buy_margin / decimal.Decimal('100'))
        kalem.save(update_fields=['sell_multiplier', 'buy_multiplier'])

    for urun in Product.objects.all():
        urun.price_multiplier = decimal.Decimal('1') + (urun.profit_margin / decimal.Decimal('100'))
        urun.save(update_fields=['price_multiplier'])


def carpani_yuzdeye_geri_cevir(apps, schema_editor):
    # Migration geri alınırsa (rollback) eşdeğer % değerine geri döner.
    FinancialData = apps.get_model('store', 'FinancialData')
    Product = apps.get_model('store', 'Product')

    for kalem in FinancialData.objects.all():
        kalem.profit_margin = (kalem.sell_multiplier - decimal.Decimal('1')) * decimal.Decimal('100')
        kalem.buy_margin = (kalem.buy_multiplier - decimal.Decimal('1')) * decimal.Decimal('100')
        kalem.save(update_fields=['profit_margin', 'buy_margin'])

    for urun in Product.objects.all():
        urun.profit_margin = (urun.price_multiplier - decimal.Decimal('1')) * decimal.Decimal('100')
        urun.save(update_fields=['profit_margin'])


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0006_financialdata_buy_margin_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='financialdata',
            name='sell_multiplier',
            field=models.DecimalField(decimal_places=4, default=1, max_digits=8, verbose_name='Satış Çarpanı'),
        ),
        migrations.AddField(
            model_name='financialdata',
            name='buy_multiplier',
            field=models.DecimalField(decimal_places=4, default=1, max_digits=8, verbose_name='Alış Çarpanı'),
        ),
        migrations.AddField(
            model_name='product',
            name='price_multiplier',
            field=models.DecimalField(decimal_places=4, default=1, max_digits=8, verbose_name='Fiyat Çarpanı'),
        ),
        migrations.RunPython(yuzdeyi_carpana_cevir, carpani_yuzdeye_geri_cevir),
        migrations.RemoveField(
            model_name='financialdata',
            name='profit_margin',
        ),
        migrations.RemoveField(
            model_name='financialdata',
            name='buy_margin',
        ),
        migrations.RemoveField(
            model_name='product',
            name='profit_margin',
        ),
    ]
