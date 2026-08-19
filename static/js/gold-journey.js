/*
 * Ana sayfa: "Altınla Dolan Monogram" - markanın gerçek logosuyla, üç
 * aşamalı hikaye.
 *
 * #gold-journey section'ı. İçindeki .gold-journey-sticky ekranda sabit
 * kalır. Ortada markanın TS monogramı (PNG logo) durur ve scroll
 * progress'e bağlı şu sırayla oynar:
 *   1) Başta sadece silik bir hayalet logo görünür
 *   2) Kaydırdıkça altın sarısı versiyonu AŞAĞIDAN YUKARI dolar
 *      (clip-path inset azaltılarak)
 *   3) Dolum bitince logo altın bir parlamayla ışır (drop-shadow glow) ve
 *      üzerinden soldan sağa bir ışıltı süpürmesi geçer (logo maskeli bant).
 *
 * Hikaye 3 karttan oluşur (#gold-journey-rail > .gj-card): "Turgut Sarraf",
 * "Yılların Emeği", "Güvenin Işıltısı". Her kart SADECE kendi 1 birimlik
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

    // Logo sahnesinin katmanları.
    var logoDolu = sahne.querySelector('.gd-logo-dolu');
    var logoParilti = sahne.querySelector('.gd-logo-parilti');

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

        // 1) Logo sahnesi zaman çizelgesi (progress 0 -> 1):
        //    %4-64   altın logo aşağıdan yukarı dolar
        //    %66-88  dolan logo giderek parlar (altın glow)
        //    %78-96  ışıltı bandı logonun üzerinden soldan sağa süpürülür
        var dolumT = yumusat(evreT(progress, 0.04, 0.60));
        var parlamaT = yumusat(evreT(progress, 0.66, 0.22));

        if (logoDolu) {
            logoDolu.style.clipPath = 'inset(' + (100 - 100 * dolumT).toFixed(1) + '% 0 0 0)';
            // Parlama: sarılık/parlaklık artar + altın renkli dış ışıma büyür.
            logoDolu.style.filter =
                'sepia(1) saturate(' + (2.6 + 1.2 * parlamaT).toFixed(2) + ')' +
                ' hue-rotate(-8deg)' +
                ' brightness(' + (1.1 + 0.3 * parlamaT).toFixed(2) + ')' +
                ' drop-shadow(0 0 ' + (36 * parlamaT).toFixed(0) + 'px rgba(255, 210, 110, ' + (0.8 * parlamaT).toFixed(2) + '))';
        }

        if (logoParilti) {
            var suprulmeT = yumusat(evreT(progress, 0.78, 0.18));
            logoParilti.style.transform = 'translateX(' + (-160 + 480 * suprulmeT).toFixed(1) + '%)';
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
