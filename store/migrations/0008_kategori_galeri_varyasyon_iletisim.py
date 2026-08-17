# Generated manually - kategori, çoklu görsel galerisi, SKU/işçilik/taş türü,
# opsiyonel renk/ölçü varyasyonu, iletişim mesajları ve WhatsApp tıklama kaydı.
#
# NOT: Eskiden Product'ta tek bir "image" alanı vardı. Bu migration önce yeni
# ProductImage galerisini oluşturur, sonra mevcut tüm ürünlerin eski tekil
# görselini otomatik olarak galeriye (0. sıraya) taşır, en son eski "image"
# alanını kaldırır. Yani hiçbir ürün görseli kaybolmaz.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def eski_gorselleri_galeriye_tasi(apps, schema_editor):
    Product = apps.get_model('store', 'Product')
    ProductImage = apps.get_model('store', 'ProductImage')

    for urun in Product.objects.exclude(image='').exclude(image__isnull=True):
        ProductImage.objects.create(product=urun, image=urun.image, display_order=0)


def galeriden_eski_alana_geri_tasi(apps, schema_editor):
    # Migration geri alınırsa: her ürünün galerideki İLK görselini eski
    # tekil "image" alanına geri yazar.
    Product = apps.get_model('store', 'Product')

    for urun in Product.objects.all():
        ilk = urun.images.order_by('display_order', 'id').first()
        if ilk:
            urun.image = ilk.image
            urun.save(update_fields=['image'])


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0007_replace_percent_margins_with_multipliers'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Kategori Adı')),
                ('slug', models.SlugField(blank=True, unique=True, verbose_name='URL Yolu (Otomatik)')),
                ('display_order', models.IntegerField(default=100, verbose_name='Sıra (küçük sayı önce gösterilir)')),
            ],
            options={
                'verbose_name': 'Kategori',
                'verbose_name_plural': 'Kategoriler',
                'ordering': ['display_order', 'name'],
            },
        ),
        migrations.AddField(
            model_name='product',
            name='category',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='urunler', to='store.category', verbose_name='Kategori',
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='sku',
            field=models.CharField(blank=True, max_length=50, verbose_name='Stok Kodu (SKU)'),
        ),
        migrations.AddField(
            model_name='product',
            name='stone_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('tassiz', 'Taşsız'), ('pirlanta', 'Pırlanta'), ('zirkon', 'Zirkon'),
                    ('yakut', 'Yakut'), ('zumrut', 'Zümrüt'), ('safir', 'Safir'),
                    ('inci', 'İnci'), ('diger', 'Diğer'),
                ],
                default='tassiz', max_length=20, verbose_name='Taş Türü',
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='labor_cost',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='İşçilik Maliyeti (TL)'),
        ),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='products/', verbose_name='Görsel')),
                ('display_order', models.IntegerField(default=0, verbose_name='Sıra')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name='images',
                    to='store.product', verbose_name='Ürün',
                )),
            ],
            options={
                'verbose_name': 'Ürün Görseli',
                'verbose_name_plural': 'Ürün Görselleri',
                'ordering': ['display_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='ProductColorOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('renk', models.CharField(
                    choices=[('sari', 'Sarı Altın'), ('beyaz', 'Beyaz Altın'), ('rose', 'Rose Gold')],
                    max_length=10, verbose_name='Renk',
                )),
                ('product', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name='renk_secenekleri',
                    to='store.product', verbose_name='Ürün',
                )),
            ],
            options={
                'verbose_name': 'Renk Seçeneği',
                'verbose_name_plural': 'Renk Seçenekleri',
                'ordering': ['renk'],
                'unique_together': {('product', 'renk')},
            },
        ),
        migrations.CreateModel(
            name='ProductSizeOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('olcu', models.CharField(max_length=10, verbose_name='Ölçü')),
                ('stokta_var', models.BooleanField(default=True, verbose_name='Stokta Var')),
                ('product', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name='olcu_secenekleri',
                    to='store.product', verbose_name='Ürün',
                )),
            ],
            options={
                'verbose_name': 'Ölçü Seçeneği',
                'verbose_name_plural': 'Ölçü Seçenekleri',
                'ordering': ['olcu'],
                'unique_together': {('product', 'olcu')},
            },
        ),
        migrations.RunPython(eski_gorselleri_galeriye_tasi, galeriden_eski_alana_geri_tasi),
        migrations.RemoveField(
            model_name='product',
            name='image',
        ),
        migrations.CreateModel(
            name='ContactMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Ad Soyad')),
                ('phone', models.CharField(blank=True, max_length=20, verbose_name='Telefon')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='E-posta')),
                ('message', models.TextField(verbose_name='Mesaj')),
                ('is_read', models.BooleanField(default=False, verbose_name='Okundu mu?')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Tarih')),
            ],
            options={
                'verbose_name': 'İletişim Mesajı',
                'verbose_name_plural': 'İletişim Mesajları',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='WhatsAppClick',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.CharField(
                    choices=[
                        ('urun_detay', 'Ürün Detay'), ('iletisim', 'İletişim Sayfası'),
                        ('genel', 'Site Geneli (Yüzen Buton)'),
                    ],
                    default='genel', max_length=20, verbose_name='Kaynak',
                )),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Tarih')),
                ('product', models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    to='store.product', verbose_name='İlgili Ürün',
                )),
            ],
            options={
                'verbose_name': 'WhatsApp Tıklaması',
                'verbose_name_plural': 'WhatsApp Tıklamaları',
                'ordering': ['-created_at'],
            },
        ),
    ]
