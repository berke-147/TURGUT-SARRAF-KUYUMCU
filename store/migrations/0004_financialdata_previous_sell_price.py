# Generated manually - previous_sell_price alanı (yüzdesel değişim hesabı için)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0003_alter_financialdata_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='financialdata',
            name='previous_sell_price',
            field=models.DecimalField(decimal_places=4, default=0, max_digits=10, verbose_name='Önceki Satış Fiyatı'),
        ),
    ]
