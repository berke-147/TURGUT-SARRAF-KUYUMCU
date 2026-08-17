/*
 * Ana sayfa: "Yakuttan Broşa" - basit SVG zeminli, iki aşamalı hikaye.
 *
 * #gold-journey section'ı (280vh). İçindeki .gold-journey-sticky ekranda
 * sabit kalır. Arka planda TEK bir vektörel (SVG) sahne var: ortada yakut
 * SABİT duruyor (sadece en başta belirir), kaydırdıkça etrafındaki 16
 * papatya yaprağı (8 dış + 8 iç) TEKER TEKER, sırayla açılıyor, en son
 * tepede asma halkası (bail) belirip parçayı bir kolye pandantifine
 * dönüştürüyor. Foto/video değil - saf CSS/SVG transform animasyonu.
 *
 * Hikaye 2 karttan oluşur (#gold-journey-rail > .gj-card): "Bir Yakut" ve
 * "Altın Bir Kolye". Her kart SADECE kendi 1 birimlik penceresinde yaşar;
 * komşu kartla sadece kısa bir geçiş payı (giriş/çıkış) paylaşır:
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

    // SVG sahnesinin parçaları - ortadaki sabit yakut, teker teker açılan
    // 16 yaprak (dış + iç sıra) ve en son beliren asma halkası (bail).
    var gemGrubu = sahne.querySelector('.gj-gem-group');
    var yapraklar = Array.prototype.slice.call(sahne.querySelectorAll('.gj-petal'));
    var bail = sahne.querySelector('.gj-bail');

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

    // Yaprakların açılma sırası ve zamanlaması, DOM sırasına göre (HTML'de
    // önce 8 dış yaprak, sonra 8 iç yaprak yazılmış durumda) önceden
    // hesaplanır - her karede yeniden hesaplamamak için. Yakut ilk %6'da,
    // dış yapraklar %6-%62 arası sırayla, iç yapraklar %62-%94 arası
    // sırayla, asma halkası en son %94-%100 arası belirir.
    var YAPRAK_PENCERESI = (function () {
        var pencereler = [];
        yapraklar.forEach(function (yaprak, i) {
            var baslangic, aralik;
            if (i < 8) {
                baslangic = 0.06 + i * 0.07;
                aralik = 0.10;
            } else {
                var k = i - 8;
                baslangic = 0.62 + k * 0.04;
                aralik = 0.06;
            }
            pencereler.push({
                aci: parseFloat(yaprak.dataset.angle) || 0,
                olcek: parseFloat(yaprak.dataset.scale) || 1,
                baslangic: baslangic,
                aralik: aralik
            });
        });
        return pencereler;
    })();

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

        // 1) Yakut -> Broş SVG sahnesi. Yakut ortada sabit duruyor, sadece
        // en başta hafifçe belirip yerine oturuyor. Ardından 16 yaprak
        // teker teker (önce dış sıra, sonra iç sıra) açılıyor, en son
        // asma halkası beliriyor.
        if (gemGrubu) {
            var gt = yumusat(evreT(progress, 0, 0.06));
            gemGrubu.style.opacity = gt.toFixed(2);
            gemGrubu.style.transform = 'scale(' + (0.4 + gt * 0.6).toFixed(3) + ')';
        }

        yapraklar.forEach(function (yaprak, i) {
            var p = YAPRAK_PENCERESI[i];
            var t = yumusat(evreT(progress, p.baslangic, p.aralik));
            var girisAcisi = p.aci - (1 - t) * 18; // hafifçe dönerek yerine oturur
            var olcek = p.olcek * (0.35 + t * 0.65);
            yaprak.style.opacity = t.toFixed(2);
            yaprak.style.transform = 'rotate(' + girisAcisi.toFixed(1) + 'deg) scale(' + olcek.toFixed(3) + ')';
        });

        if (bail) {
            var bt = yumusat(evreT(progress, 0.94, 0.06));
            bail.style.opacity = bt.toFixed(2);
            bail.style.transform = 'scale(' + (0.5 + bt * 0.5).toFixed(3) + ')';
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
