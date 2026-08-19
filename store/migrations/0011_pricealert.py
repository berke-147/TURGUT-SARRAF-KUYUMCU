# Fiyat dedektörü: %1'lik değişimlerde panel kullanıcısına bildirim olarak
# sunulan PriceAlert kayıtları (services.py -> _degisimi_denetle üretir).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0010_ratesnapshot'),
    ]

    operations = [
        migrations.CreateModel(
            name='PriceAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(db_index=True, max_length=10, verbose_name='Kalem Kodu')),
                ('name', models.CharField(max_length=50, verbose_name='Kalem Adı')),
                ('old_price', models.DecimalField(decimal_places=4, max_digits=10, verbose_name='Önceki Fiyat (ham)')),
                ('new_price', models.DecimalField(decimal_places=4, max_digits=10, verbose_name='Yeni Fiyat (ham)')),
                ('change_percent', models.DecimalField(decimal_places=2, max_digits=6, verbose_name='Değişim %')),
                ('is_read', models.BooleanField(default=False, verbose_name='Okundu')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Tarih')),
            ],
            options={
                'verbose_name': 'Fiyat Uyarısı',
                'verbose_name_plural': 'Fiyat Uyarıları',
                'ordering': ['-created_at'],
            },
        ),
    ]
