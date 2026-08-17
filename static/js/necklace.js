/*
 * Ana sayfa: kaydırdıkça yakuttan kolyeye dönüşen SVG sahnesi.
 *
 * Mantık: #necklace-scene section'ı ekstra yüksek (bkz. CSS - 380vh).
 * İçindeki .necklace-sticky, position:sticky ile ekranda sabit kalır.
 * Kullanıcı bu bölüm boyunca kaydırdıkça 0-1 arası bir "progress" değeri
 * hesaplanır ve bu değere göre:
 *   1) Yakut (ruby-pendant grubu) ekranın ortasındaki büyük halinden,
 *      zincirin ucundaki küçük kolye ucu haline döner/küçülür.
 *   2) Altın zincir halkaları (chain-links) rehber eğri (chain-guide)
 *      üzerinde tek tek, sırayla belirir - her halkanın kendi eşik
 *      aralığı vardır, geri kaydırınca da tersine kaybolur (tamamen
 *      kaydırma pozisyonuna bağlı, tek seferlik bir "oynatma" değil).
 *   3) Görünür altın çizgi (chain-line) stroke-dashoffset ile "çizilerek"
 *      tamamlanır.
 *   4) Giriş/çıkış metinleri buna paralel solar.
 *
 * prefers-reduced-motion tercih edilmişse hiç scroll-a bağlı hesap
 * yapılmaz; sahne kısa/normal boyda kalır ve kolye baştan tam görünür
 * halde durur (bkz. style.css .necklace-scene.reduced-motion).
 */
(function () {
    var sahne = document.getElementById('necklace-scene');
    if (!sahne) return;

    var svg = sahne.querySelector('.necklace-svg');
    var rehberEgri = sahne.querySelector('#chain-guide');
    var zincirCizgisi = sahne.querySelector('#chain-line');
    var halkaGrubu = sahne.querySelector('#chain-links');
    var yakut = sahne.querySelector('#ruby-pendant');
    var girisMetni = document.getElementById('necklace-text-intro');
    var cikisMetni = document.getElementById('necklace-text-outro');
    var kaydirIpucu = document.getElementById('scroll-hint');

    if (!svg || !rehberEgri || !zincirCizgisi || !halkaGrubu || !yakut) return;

    var azaltilmisHareket = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // ---------- Rehber eğri üzerinde halka pozisyonlarını hesapla ----------
    var TOPLAM_HALKA = 16;
    var uzunluk = rehberEgri.getTotalLength();
    var PENDANT = rehberEgri.getPointAtLength(uzunluk / 2);
    var HALKALAR = [];

    (function halkalariOlustur() {
        for (var i = 0; i < TOPLAM_HALKA; i++) {
            // Ortadaki (kolye ucunun tam üstüne denk gelen) küçük bir aralığı
            // atlıyoruz ki halka yakutun içine gömülmüş gibi durmasın.
            var u = i / (TOPLAM_HALKA - 1);
            if (u > 0.46 && u < 0.54) continue;

            var nokta = rehberEgri.getPointAtLength(u * uzunluk);
            var g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            g.setAttribute('class', 'chain-link');
            g.style.opacity = 0;

            // Dış halka: kalın, koyu-açık altın gradyanlı ana halka gövdesi.
            var disElips = document.createElementNS('http://www.w3.org/2000/svg', 'ellipse');
            disElips.setAttribute('cx', 0);
            disElips.setAttribute('cy', 0);
            disElips.setAttribute('rx', 11);
            disElips.setAttribute('ry', 7.5);
            disElips.setAttribute('fill', 'none');
            disElips.setAttribute('stroke', 'url(#gold-grad)');
            disElips.setAttribute('stroke-width', 3.6);
            g.appendChild(disElips);

            // İç ince parlak vurgu: yuvarlak metal kesitin ışık yakalayan
            // tarafını taklit eder - halkaları düz çizgi yerine "dolgun/
            // parlak metal" gibi gösterir.
            var icElips = document.createElementNS('http://www.w3.org/2000/svg', 'ellipse');
            icElips.setAttribute('cx', -1.4);
            icElips.setAttribute('cy', -1.4);
            icElips.setAttribute('rx', 9.5);
            icElips.setAttribute('ry', 6);
            icElips.setAttribute('fill', 'none');
            icElips.setAttribute('stroke', 'url(#gold-grad-soft)');
            icElips.setAttribute('stroke-width', 1.3);
            g.appendChild(icElips);

            halkaGrubu.appendChild(g);

            HALKALAR.push({
                el: g,
                x: nokta.x,
                y: nokta.y,
                aci: (HALKALAR.length % 2 === 0) ? 0 : 90,
            });
        }

        // Eşik aralıklarını sıraya göre dağıt - hafif üst üste binme, yumuşak geçiş için.
        var n = HALKALAR.length;
        var araBaslangic = 0.28;
        var araBitis = 0.92;
        var adim = (araBitis - araBaslangic) / n;
        HALKALAR.forEach(function (h, i) {
            h.baslangic = araBaslangic + i * adim;
            h.bitis = h.baslangic + adim * 1.6;
        });
    })();

    var HERO = { x: 400, y: 360, scale: 2.5 };
    var PENDANT_STATE = { x: PENDANT.x, y: PENDANT.y, scale: 0.62 };

    if (azaltilmisHareket) {
        // Animasyon yok - kolye baştan tam/son haliyle sabit görünür.
        sahne.classList.add('reduced-motion');
        HALKALAR.forEach(function (h) {
            h.el.setAttribute('transform', 'translate(' + h.x + ',' + h.y + ') scale(1) rotate(' + h.aci + ')');
            h.el.style.opacity = 1;
        });
        yakut.setAttribute('transform', 'translate(' + PENDANT_STATE.x + ',' + PENDANT_STATE.y + ') scale(' + PENDANT_STATE.scale + ')');
        zincirCizgisi.style.strokeDasharray = 'none';
        zincirCizgisi.style.strokeDashoffset = 0;
        if (girisMetni) girisMetni.style.display = 'none';
        if (cikisMetni) { cikisMetni.style.opacity = 1; cikisMetni.style.transform = 'translateX(-50%)'; }
        if (kaydirIpucu) kaydirIpucu.style.display = 'none';
        return;
    }

    // ---------- Normal (animasyonlu) mod ----------
    var YAKUT_BITIS = 0.30; // bu progress değerinden sonra yakut tamamen yerine oturur

    var zincirUzunlugu = zincirCizgisi.getTotalLength();
    zincirCizgisi.style.strokeDasharray = zincirUzunlugu;
    zincirCizgisi.style.strokeDashoffset = zincirUzunlugu;

    function sinirla(deger, min, max) {
        return Math.max(min, Math.min(max, deger));
    }

    function yumusat(t) {
        // ease-in-out (smoothstep) - ani başlangıç/bitişleri yumuşatır
        return t * t * (3 - 2 * t);
    }

    function karistir(a, b, t) {
        return a + (b - a) * t;
    }

    var tikYapiliyor = false;

    function sahneyiGuncelle() {
        tikYapiliyor = false;

        // offsetTop yerine getBoundingClientRect kullanıyoruz - sahne'nin
        // konumlu (position:relative/sticky) bir üst elemanın İÇİNDE olup
        // olmadığından bağımsız, her zaman doğru sonuç verir.
        var sahneUst = sahne.getBoundingClientRect().top + (window.scrollY || window.pageYOffset);
        var sahneYuksekligi = sahne.offsetHeight;
        var viewportYuksekligi = window.innerHeight;
        var kaydirilan = window.scrollY || window.pageYOffset;

        var kullanilabilirAlan = sahneYuksekligi - viewportYuksekligi;
        var progress = kullanilabilirAlan > 0
            ? sinirla((kaydirilan - sahneUst) / kullanilabilirAlan, 0, 1)
            : 0;

        // 1) Yakut: hero -> kolye ucu
        var yakutT = yumusat(sinirla(progress / YAKUT_BITIS, 0, 1));
        var yx = karistir(HERO.x, PENDANT_STATE.x, yakutT);
        var yy = karistir(HERO.y, PENDANT_STATE.y, yakutT);
        var ys = karistir(HERO.scale, PENDANT_STATE.scale, yakutT);
        yakut.setAttribute('transform', 'translate(' + yx.toFixed(1) + ',' + yy.toFixed(1) + ') scale(' + ys.toFixed(3) + ')');

        // 2) Altın çizgi: kaydırdıkça "çizilir"
        var cizgiT = yumusat(sinirla((progress - 0.22) / (0.95 - 0.22), 0, 1));
        zincirCizgisi.style.strokeDashoffset = (zincirUzunlugu * (1 - cizgiT)).toFixed(1);

        // 3) Halkalar: her biri kendi eşik aralığında belirir
        HALKALAR.forEach(function (h) {
            var t = sinirla((progress - h.baslangic) / (h.bitis - h.baslangic), 0, 1);
            t = yumusat(t);
            var olcek = karistir(0.25, 1, t);
            var donme = karistir(h.aci - 55, h.aci, t);
            h.el.style.opacity = t;
            h.el.setAttribute('transform', 'translate(' + h.x.toFixed(1) + ',' + h.y.toFixed(1) + ') scale(' + olcek.toFixed(3) + ') rotate(' + donme.toFixed(1) + ')');
        });

        // 4) Giriş metni: hızlıca solur ve yukarı kayar
        // ÖNEMLİ: .necklace-text CSS sınıfı yatay ortalamayı
        // "transform: translateX(-50%)" ile yapıyor. Burada style.transform'u
        // DOĞRUDAN "translateY(...)" ile değiştirirsek CSS'teki -50%'yi
        // eziyoruz ve metin sağa kayıyor - bu yüzden translateX(-50%)'yi
        // her seferinde translateY ile birlikte yazıyoruz.
        if (girisMetni) {
            var girisT = sinirla(progress / 0.12, 0, 1);
            girisMetni.style.opacity = 1 - girisT;
            girisMetni.style.transform = 'translateX(-50%) translateY(' + (-girisT * 30).toFixed(1) + 'px)';
        }

        // 5) Çıkış metni: sona doğru belirir
        if (cikisMetni) {
            var cikisT = sinirla((progress - 0.85) / 0.15, 0, 1);
            cikisMetni.style.opacity = cikisT;
            cikisMetni.style.transform = 'translateX(-50%) translateY(' + ((1 - cikisT) * 24).toFixed(1) + 'px)';
        }

        // 6) Kaydırma ipucu: sadece en başta görünür
        if (kaydirIpucu) {
            kaydirIpucu.style.opacity = sinirla(1 - progress / 0.06, 0, 1);
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
