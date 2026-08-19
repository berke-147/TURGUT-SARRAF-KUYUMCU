# Piyasa Durumu ürün detay sayfasındaki grafikler için fiyat geçmişi tablosu.
# Kur robotu bu tabloya en fazla 5 dakikada bir örnek yazar (services.py).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0009_blog'),
    ]

    operations = [
        migrations.CreateModel(
            name='RateSnapshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(db_index=True, max_length=10, verbose_name='Kalem Kodu')),
                ('buy_price', models.DecimalField(decimal_places=4, max_digits=10, verbose_name='Ham Alış')),
                ('sell_price', models.DecimalField(decimal_places=4, max_digits=10, verbose_name='Ham Satış')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Zaman')),
            ],
            options={
                'verbose_name': 'Fiyat Geçmişi',
                'verbose_name_plural': 'Fiyat Geçmişleri',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='ratesnapshot',
            index=models.Index(fields=['code', '-created_at'], name='store_rates_code_cr_idx'),
        ),
    ]
