# Generated manually - alış kar marjı, görünürlük ve sıralama desteği

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0005_product_fixed_price_product_product_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='financialdata',
            name='buy_margin',
            field=models.DecimalField(
                decimal_places=2, default=0, max_digits=5, verbose_name='Alış Kar Marjı (%)'
            ),
        ),
        migrations.AddField(
            model_name='financialdata',
            name='is_visible',
            field=models.BooleanField(default=True, verbose_name='Sitede Göster'),
        ),
        migrations.AddField(
            model_name='financialdata',
            name='display_order',
            field=models.IntegerField(default=100, verbose_name='Sıra (küçük sayı önce gösterilir)'),
        ),
        migrations.AlterModelOptions(
            name='financialdata',
            options={
                'ordering': ['display_order', 'name'],
                'verbose_name': 'Finansal Veri (Otomatik)',
                'verbose_name_plural': 'Finansal Veriler',
            },
        ),
    ]
