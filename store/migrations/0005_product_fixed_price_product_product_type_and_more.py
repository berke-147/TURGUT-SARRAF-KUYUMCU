# Generated manually - ürün tipi (işçilikli / sabit fiyatlı) desteği

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0004_financialdata_previous_sell_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='product_type',
            field=models.CharField(
                choices=[
                    ('iscilikli', 'İşçilikli Ürün (Altın - Gramaj/Ayar ile hesaplanır)'),
                    ('sabit', 'Sabit Fiyatlı Ürün (Saat, Aksesuar vb.)'),
                ],
                default='iscilikli',
                max_length=10,
                verbose_name='Ürün Tipi',
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='fixed_price',
            field=models.DecimalField(
                decimal_places=2, max_digits=10, null=True, blank=True, verbose_name='Sabit Satış Fiyatı (TL)'
            ),
        ),
        migrations.AlterField(
            model_name='product',
            name='weight_gram',
            field=models.DecimalField(
                decimal_places=2, max_digits=6, null=True, blank=True, verbose_name='Gramaj'
            ),
        ),
        migrations.AlterField(
            model_name='product',
            name='purity',
            field=models.IntegerField(
                choices=[(24, '24 Ayar (Has)'), (22, '22 Ayar'), (14, '14 Ayar'), (8, '8 Ayar')],
                null=True,
                blank=True,
                verbose_name='Ayar',
            ),
        ),
    ]
