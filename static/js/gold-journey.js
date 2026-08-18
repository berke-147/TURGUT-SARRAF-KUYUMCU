/*
 * Ana sayfa: "Erimiş Altın Dökümü" - basit SVG zeminli, üç aşamalı hikaye.
 *
 * #gold-journey section'ı. İçindeki .gold-journey-sticky ekranda sabit
 * kalır. Arka planda TEK bir vektörel (SVG) sahne var ve scroll progress'e
 * bağlı şu sırayla oynar:
 *   1) Pota hafifçe eğilir, erimiş altın akmaya başlar (akış scale-y ile uzar)
 *   2) Kalıp içindeki dolum (clip-path'li rect) yükselerek külçeyi doldurur,
 *      kalıbın etrafında sıcak kor parıltısı belirir
 *   3) Akış kesilir, dolum soğumuş altın rengine döner (crossfade), üzerinden
 *      bir ışıltı süpürmesi geçer ve TS damgası belirir.
 * Foto/video değil - saf SVG attribute/transform animasyonu.
 *
 * Hikaye 3 karttan oluşur (#gold-journey-rail > .gj-card): "Saf Altın",
 * "Ustanın Eli", "Güvenin Mührü". Her kart SADECE kendi 1 birimlik
 * penceresinde yaşar; komşu kartla kısa bir geçiş payı paylaşır:
 *
 *   rel = globalX - kartIndex
 *   rel < -GIRIS_PAYI      : görünmez, ekranın solunda bekliyor
 *   -GIRIS_PAYI..0         : soldan içeri kayıyor (giriş)
 *   0..(1-CIKIS_PAYI)      : ortada sabit, OKUNUYOR (tek kart bu aralıkta hakim)
 *   (1-CIKIS_PAYI)..1      : sağa doğru çıkıyor (çıkış)
 *   rel > 1                : görünmez, ekranın sağında
 *
 * "Yazılarda oynasın" isteği için: kart girerken başlık/adım/metin
 * kademeli (staggered) olarak, hafifçe aşağıdan yukarı süzülerek belirir.
 *
 * Not: Bu mantık kart sayısından bağımsızdır (TOPLAM_ASAMA = kartlar.length),
 * yarın 2 yerine 3-4 kart eklenirse kod değişmeden çalışmaya devam eder.
 */
(function () {
    var sahne = document.getElementById('gold-journey');
    if (!sahne) return;

    var sticky = sahne.querySelector('.gold-journey-sticky');
    var kartlar = Array.prototype.slice.call(sahne.querySelectorAll('.gj-card'));
    var izFill = document.getElementById('gj-track-fill');
    var izNoktalari = Array.prototype.slice.call(sahne.querySelectorAll('.gj-track-dot'));
    var ipucu = document.getElementById('gold-journey-hint');

    // SVG sahnesinin parçaları - döküm hikayesinin oyuncuları.
    var pota = sahne.querySelector('.gd-pota');
    var akis = sahne.querySelector('.gd-akis');
    var dolum = sahne.querySelector('.gd-dolum');
    var sogumus = sahne.querySelector('.gd-sogumus');
    var parilti = sahne.querySelector('.gd-parilti');
    var damga = sahne.querySelector('.gd-damga');
    var kor = sahne.querySelector('.gd-kor');

    if (!sticky || !kartlar.length) return;

    var azaltilmisHareket = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (azaltilmisHareket) {
        // Animasyon yok - kartlar alt alta, sade akışta, hepsi görünür.
        sahne.classList.add('reduced-motion');
        return;
    }

    var TOPLAM_ASAMA = kartlar.length;
    var GIRIS_PAYI = 0.18;
    var CIKIS_PAYI = 0.18;
    var tikYapiliyor = false;

    function sinirla(deger, min, max) {
        return Math.max(min, Math.min(max, deger));
    }

    function karistir(a, b, t) {
        return a + (b - a) * t;
    }

    function evreT(t, baslangic, aralik) {
        return sinirla((t - baslangic) / aralik, 0, 1);
    }

    function yumusat(t) {
        return t * t * (3 - 2 * t); // smoothstep - daha zarif bir açılma hissi için
    }

    // Her kartın alt elemanlarını (adım etiketi, başlık, paragraf/buton)
    // önceden bul - her karede yeniden sorgulamamak için.
    var kartElemanlari = kartlar.map(function (kart) {
        return {
            kart: kart,
            adim: kart.querySelector('.gj-step'),
            baslik: kart.querySelector('h2'),
            metin: kart.querySelector('p:not(.gj-slogan)'),
            slogan: kart.querySelector('.gj-slogan')
        };
    });

    function metniYerlestir(el, t) {
        if (!el) return;
        el.style.opacity = t.toFixed(2);
        el.style.transform = 'translateY(' + ((1 - t) * 16).toFixed(1) + 'px)';
    }

    function sahneyiGuncelle() {
        tikYapiliyor = false;

        var sahneUst = sahne.getBoundingClientRect().top + (window.scrollY || window.pageYOffset);
        var sahneYuksekligi = sahne.offsetHeight;
        var viewportYuksekligi = window.innerHeight;
        var kaydirilan = window.scrollY || window.pageYOffset;

        var kullanilabilirAlan = sahneYuksekligi - viewportYuksekligi;
        var progress = kullanilabilirAlan > 0
            ? sinirla((kaydirilan - sahneUst) / kullanilabilirAlan, 0, 1)
            : 0;

        var globalX = progress * TOPLAM_ASAMA; // 0 .. TOPLAM_ASAMA arası "sahne birimi"

        // 1) Döküm sahnesi zaman çizelgesi (progress 0 -> 1):
        //    %0-10   pota eğilir
        //    %8-16   akış uzayarak kalıba ulaşır
        //    %16-64  kalıp dolar (kor parıltısı dolumla birlikte artar)
        //    %62-72  akış kesilir, pota doğrulur
        //    %70-84  altın soğur (sıcak turuncudan eskitilmiş altına crossfade)
        //    %84-94  ışıltı süpürmesi külçenin üzerinden geçer
        //    %90-100 TS damgası belirir
        var potaT = yumusat(evreT(progress, 0, 0.10)) - yumusat(evreT(progress, 0.64, 0.08));
        if (pota) {
            var aci = (-9 * sinirla(potaT, 0, 1)).toFixed(2);
            pota.setAttribute('transform', 'rotate(' + aci + ' 200 92)');
        }

        var akisT = yumusat(evreT(progress, 0.08, 0.08)) - yumusat(evreT(progress, 0.62, 0.08));
        akisT = sinirla(akisT, 0, 1);
        if (akis) {
            akis.setAttribute('transform', 'scale(1 ' + akisT.toFixed(3) + ')');
            akis.setAttribute('opacity', akisT.toFixed(2));
        }

        var dolumT = yumusat(evreT(progress, 0.16, 0.48));
        if (dolum) {
            // Kalıp içi y=302..366 arası (64 birim) - dolum alttan yükselir.
            var yukseklik = 64 * dolumT;
            dolum.setAttribute('y', (366 - yukseklik).toFixed(1));
            dolum.setAttribute('height', yukseklik.toFixed(1));
        }

        var sogumaT = yumusat(evreT(progress, 0.70, 0.14));
        if (sogumus) {
            sogumus.setAttribute('opacity', sogumaT.toFixed(2));
        }

        if (kor) {
            // Kor, dolum sürerken parlar; altın soğudukça söner.
            var korOpaklik = sinirla(dolumT * (1 - sogumaT), 0, 1) * 0.9;
            kor.setAttribute('opacity', korOpaklik.toFixed(2));
        }

        if (parilti) {
            // Işıltı bandı külçenin solundan girip sağından çıkar (clip
            // sayesinde sadece külçe yüzeyinde görünür).
            var suprulmeT = evreT(progress, 0.84, 0.10);
            var x = -80 + 360 * yumusat(suprulmeT);
            parilti.setAttribute('transform', 'translate(' + x.toFixed(1) + ' 0)');
        }

        if (damga) {
            var damgaT = yumusat(evreT(progress, 0.90, 0.10));
            damga.setAttribute('opacity', damgaT.toFixed(2));
            var olcek = (0.7 + 0.3 * damgaT).toFixed(3);
            damga.setAttribute('transform',
                'translate(200 334) scale(' + olcek + ') translate(-200 -334)');
        }

        // 2) Kartlar: her biri SADECE kendi 1 birimlik penceresinde yaşar.
        kartElemanlari.forEach(function (ke, i) {
            var rel = globalX - i;
            var ofset, kartOpaklik;
            var girisT = null;

            if (rel <= -GIRIS_PAYI) {
                ofset = -140; kartOpaklik = 0;
            } else if (rel < 0) {
                girisT = (rel + GIRIS_PAYI) / GIRIS_PAYI; // 0 -> 1
                ofset = karistir(-140, 0, girisT);
                kartOpaklik = 1;
            } else if (rel <= (1 - CIKIS_PAYI)) {
                ofset = 0; kartOpaklik = 1; girisT = 1;
            } else if (rel < 1) {
                var cikisT = (rel - (1 - CIKIS_PAYI)) / CIKIS_PAYI; // 0 -> 1
                ofset = karistir(0, 140, cikisT);
                kartOpaklik = 1 - cikisT;
                girisT = 1;
            } else {
                ofset = 140; kartOpaklik = 0;
            }

            ke.kart.style.transform = 'translate(-50%, -50%) translateX(' + ofset.toFixed(1) + '%)';
            ke.kart.style.opacity = kartOpaklik.toFixed(2);
            ke.kart.style.pointerEvents = kartOpaklik > 0.5 ? 'auto' : 'none';

            // Metinler kademeli (staggered) süzülerek belirir - adım
            // etiketi önce, başlık sonra, paragraf/buton en son yerine oturur.
            // Son karttaki slogan (varsa) en son, ayrı bir vurgu gibi belirir.
            if (girisT !== null) {
                metniYerlestir(ke.adim, evreT(girisT, 0, 0.6));
                metniYerlestir(ke.baslik, evreT(girisT, 0.15, 0.6));
                metniYerlestir(ke.metin, evreT(girisT, 0.3, 0.6));
                if (ke.slogan) metniYerlestir(ke.slogan, evreT(girisT, 0.45, 0.55));
            }
        });

        // 3) Yolculuk çizgisi: soldan sağa dolan ilerleme çubuğu + noktalar.
        if (izFill) {
            izFill.style.width = (progress * 100).toFixed(1) + '%';
        }
        izNoktalari.forEach(function (nokta, i) {
            nokta.classList.toggle('is-passed', globalX >= i);
        });

        // 4) Kaydırma ipucu: sadece en başta görünür
        if (ipucu) {
            ipucu.style.opacity = sinirla(1 - progress / 0.03, 0, 1);
        }
    }

    function scrollDinleyici() {
        if (!tikYapiliyor) {
            tikYapiliyor = true;
            window.requestAnimationFrame(sahneyiGuncelle);
        }
    }

    window.addEventListener('scroll', scrollDinleyici, { passive: true });
    window.addEventListener('resize', scrollDinleyici);
    sahneyiGuncelle();
})();
