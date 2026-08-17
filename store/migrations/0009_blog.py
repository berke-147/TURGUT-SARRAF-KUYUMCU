# Blog modelini oluşturur ve vitrine hemen içerik görünsün diye 3 örnek
# yazı ekler. Bu yazılar panelden (Blog > Düzenle/Sil) tamamen değiştirilebilir
# ya da silinebilir - sadece boş görünmesin diye başlangıç içeriğidir.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


ORNEK_YAZI_SLUGLARI = [
    'altin-takilarinizi-nasil-parlak-tutarsiniz',
    'yuzuk-olcunuzu-evde-nasil-olcersiniz',
    'ayar-altin-arasindaki-fark-nedir',
]


def ornek_yazilari_ekle(apps, schema_editor):
    Blog = apps.get_model('store', 'Blog')

    if Blog.objects.filter(slug__in=ORNEK_YAZI_SLUGLARI).exists():
        return

    Blog.objects.create(
        title="Altın Takılarınızı Nasıl Parlak Tutarsınız",
        slug='altin-takilarinizi-nasil-parlak-tutarsiniz',
        excerpt="Günlük kullanımda altın takılarınızın parlaklığını korumak için basit ama etkili birkaç öneri.",
        content=(
            "Altın takılar doğru bakıldığında yıllarca ilk günkü parlaklığını korur. "
            "İşte evde uygulayabileceğiniz birkaç pratik öneri:\n\n"
            "Takılarınızı parfüm, losyon ve saç spreyinden sonra takın; bu ürünlerdeki "
            "kimyasallar yüzeydeki parlaklığı zamanla matlaştırabilir. Havuz veya deniz "
            "suyuna girerken altın takılarınızı çıkarmanız da hem takının hem de cildinizin "
            "iyiliği için önerilir.\n\n"
            "Temizlik için ılık su ve birkaç damla sıvı bulaşık deterjanı yeterlidir; yumuşak "
            "bir diş fırçasıyla nazikçe fırçalayıp bol suyla durulayın ve yumuşak bir bezle "
            "kurulayın. Taşlı ürünlerde fırçalarken taşın etrafına dikkat edin.\n\n"
            "Saklarken takılarınızı birbirine sürtünmeyecek şekilde ayrı bölmelerde ya da "
            "yumuşak kumaş keselerde tutmak, çizilmeleri büyük ölçüde önler."
        ),
        is_published=True,
        display_order=10,
    )

    Blog.objects.create(
        title="Yüzük Ölçünüzü Evde Nasıl Ölçersiniz",
        slug='yuzuk-olcunuzu-evde-nasil-olcersiniz',
        excerpt="Mağazaya gelmeden önce yüzük ölçünüzü öğrenmenin evde uygulayabileceğiniz kolay bir yolu.",
        content=(
            "Doğru yüzük ölçüsünü bulmak, hem rahat bir kullanım hem de takının kaybolmaması "
            "için önemlidir. Evde ölçü almanın en kolay yolu şu şekildedir:\n\n"
            "İnce bir kağıt şeridi ya da ip parçasını, ölçüsünü almak istediğiniz parmağın "
            "etrafına sarın. İpin/kağıdın üst üste bindiği noktayı işaretleyin, sonra düz bir "
            "cetvelle bu işarete kadar olan uzunluğu milimetre cinsinden ölçün. Bu, parmağınızın "
            "çevre uzunluğunu verir.\n\n"
            "Ölçüyü günün ilerleyen saatlerinde almanız daha sağlıklı sonuç verir; parmaklar "
            "sabah saatlerinde genellikle biraz daha ince olur. Emin olamadığınız durumlarda "
            "ölçüyü mağazada bizzat kontrol ettirmeniz en sağlıklısıdır."
        ),
        is_published=True,
        display_order=20,
    )

    Blog.objects.create(
        title="8, 14, 22 ve 24 Ayar Altın Arasındaki Fark Nedir?",
        slug='ayar-altin-arasindaki-fark-nedir',
        excerpt="Ayar, altının saflık derecesini gösterir. Hangi ayarın ne için uygun olduğuna kısa bir bakış.",
        content=(
            "\"Ayar\", bir altın alaşımının içindeki saf altın oranını ifade eder. 24 ayar, "
            "%99,9 saflıkla neredeyse tamamen saf altındır; bu haliyle çok yumuşak olduğu için "
            "günlük kullanımda çizilmeye/deforme olmaya daha açıktır, daha çok külçe ve "
            "yatırımlık ürünlerde tercih edilir.\n\n"
            "22 ayar, saf altına gümüş/bakır gibi metaller karıştırılarak biraz daha "
            "dayanıklı hale getirilmiş, geleneksel takılarda sıkça tercih edilen bir orandır. "
            "14 ayar ise saf altın oranı daha düşük olduğu için günlük kullanıma daha "
            "dayanıklıdır ve genellikle daha uygun fiyatlıdır.\n\n"
            "8 ayar, saf altın oranı en düşük olan gruptur; en dayanıklı ve en ekonomik "
            "seçenektir. Hangi ayarın sizin için uygun olduğu; bütçenize, günlük kullanım "
            "sıklığınıza ve tercih ettiğiniz görünüme göre değişir."
        ),
        is_published=True,
        display_order=30,
    )


def ornek_yazilari_geri_al(apps, schema_editor):
    Blog = apps.get_model('store', 'Blog')
    Blog.objects.filter(slug__in=ORNEK_YAZI_SLUGLARI).delete()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('store', '0008_kategori_galeri_varyasyon_iletisim'),
    ]

    operations = [
        migrations.CreateModel(
            name='Blog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Başlık')),
                ('slug', models.SlugField(blank=True, unique=True, verbose_name='URL Yolu (Otomatik)')),
                ('excerpt', models.CharField(
                    blank=True, max_length=240,
                    help_text='Kart görünümünde başlığın altında gösterilir. Boş bırakırsan içerikten otomatik kısaltılır.',
                    verbose_name='Kısa Özet',
                )),
                ('content', models.TextField(verbose_name='İçerik')),
                ('cover_image', models.ImageField(blank=True, null=True, upload_to='blog/', verbose_name='Kapak Görseli')),
                ('is_published', models.BooleanField(default=True, verbose_name='Yayında')),
                ('display_order', models.IntegerField(
                    default=100, verbose_name='Sıra (küçük sayı önce gösterilir, ana sayfa vitrini için)'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Tarih')),
                ('author', models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL, verbose_name='Yazar',
                )),
            ],
            options={
                'verbose_name': 'Blog Yazısı',
                'verbose_name_plural': 'Blog Yazıları',
                'ordering': ['display_order', '-created_at'],
            },
        ),
        migrations.RunPython(ornek_yazilari_ekle, ornek_yazilari_geri_al),
    ]
