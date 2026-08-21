/*
 * Piyasa Durumu ürün detay sayfası:
 *  - Anlık alış/satış/fark/% değerlerini rates_api'den 3 sn'de bir tazeler
 *    (pano sayfasıyla aynı uç nokta).
 *  - Fiyat geçmişi grafiğini rate_history_api'den çekip Chart.js ile çizer.
 *    Aralık düğmeleri (1 gün / 1 hafta / 2 hafta / 1 ay) grafiği yeniden yükler.
 */
(function () {
  var REFRESH_MS = 3000;

  document.addEventListener('DOMContentLoaded', function () {
    var kok = document.getElementById('market-detail');
    if (!kok) return;

    var kod = kok.getAttribute('data-code');
    var ratesUrl = kok.getAttribute('data-rates-url');
    var historyUrl = kok.getAttribute('data-history-url');

    var buyEl = document.getElementById('detail-buy');
    var sellEl = document.getElementById('detail-sell');
    var farkEl = document.getElementById('detail-fark');
    var pctEl = document.getElementById('detail-pct');
    var updatedEl = document.getElementById('detail-updated');

    function formatNum(value, decimals) {
      var num = parseFloat(value);
      if (isNaN(num)) return value;
      return num.toLocaleString('tr-TR', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      });
    }

    function yonUygula(el, deger) {
      if (!el) return;
      el.classList.remove('up', 'down');
      if (deger > 0) el.classList.add('up');
      else if (deger < 0) el.classList.add('down');
    }

    // --- Anlık değerler ---
    function canliTazele() {
      fetch(ratesUrl, { cache: 'no-store' })
        .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
        .then(function (items) {
          var item = null;
          for (var i = 0; i < items.length; i++) {
            if (items[i].code === kod) { item = items[i]; break; }
          }
          if (!item) return;

          if (buyEl) buyEl.textContent = formatNum(item.buy_price, 2);
          if (sellEl) sellEl.textContent = formatNum(item.final_sell_price, 2);

          var pct = parseFloat(item.change_percent) || 0;
          var fark = parseFloat(item.change_amount) || 0;
          if (pctEl) {
            pctEl.textContent = (pct > 0 ? '+' : '') + pct.toFixed(2) + '%';
            yonUygula(pctEl, pct);
          }
          if (farkEl) {
            farkEl.textContent = (fark > 0 ? '+' : '') + formatNum(fark, 0);
            yonUygula(farkEl, fark);
          }
          if (updatedEl) updatedEl.textContent = new Date().toLocaleTimeString('tr-TR');
        })
        .catch(function (err) { console.error('Canlı veri alınamadı:', err); });
    }

    canliTazele();
    setInterval(canliTazele, REFRESH_MS);

    // --- Grafik ---
    var tuval = document.getElementById('detail-chart');
    var bosMesaj = document.getElementById('detail-chart-empty');
    var grafik = null;

    function etiketFormatla(isoStr, gun) {
      var d = new Date(isoStr);
      if (gun <= 1) {
        return d.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });
      }
      return d.toLocaleDateString('tr-TR', { day: '2-digit', month: '2-digit' }) +
             ' ' + d.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });
    }

    function mesajGoster(metin) {
      if (bosMesaj) {
        bosMesaj.textContent = metin;
        bosMesaj.hidden = false;
      }
      if (tuval) tuval.style.display = 'none';
    }

    // Chart.js CDN'den asenkron gelebilir (ya da ilk CDN başarısız olup
    // yedeğe düşülebilir). Kütüphane hazır olana kadar 250ms arayla bekler,
    // ~5 saniyede hâlâ yoksa kullanıcıya açıklayıcı bir mesaj gösterir -
    // ASLA sessizce boş bir grafik alanı bırakmaz.
    function chartIleCalis(isKalani, denemeSayisi) {
      if (typeof Chart !== 'undefined') { isKalani(); return; }
      if ((denemeSayisi || 0) >= 20) {
        mesajGoster('Grafik bileşeni yüklenemedi. Sayfayı yenilemeyi deneyin; sorun sürerse internet bağlantınız grafik kütüphanesinin indirilmesini engelliyor olabilir.');
        return;
      }
      setTimeout(function () { chartIleCalis(isKalani, (denemeSayisi || 0) + 1); }, 250);
    }

    function grafigiYukle(gun) {
      fetch(historyUrl + '?gun=' + gun, { cache: 'no-store' })
        .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
        .then(function (veri) {
          var noktalar = veri.points || [];
          var yeterli = noktalar.length >= 2;

          if (!yeterli) {
            mesajGoster('Bu aralık için henüz yeterli geçmiş verisi birikmedi. Sistem fiyatları düzenli aralıklarla kaydediyor; grafik kısa süre içinde burada dolmaya başlayacak.');
            return;
          }

          if (bosMesaj) bosMesaj.hidden = true;
          if (tuval) tuval.style.display = '';

          chartIleCalis(function () { grafigiCiz(noktalar, gun); }, 0);
        })
        .catch(function (err) {
          console.error('Grafik verisi alınamadı:', err);
          mesajGoster('Grafik verisi alınamadı. Sayfayı yenilemeyi deneyin.');
        });
    }

    function grafigiCiz(noktalar, gun) {
          var etiketler = noktalar.map(function (n) { return etiketFormatla(n.t, gun); });
          var satislar = noktalar.map(function (n) { return parseFloat(n.s); });

          if (grafik) grafik.destroy();
          grafik = new Chart(tuval.getContext('2d'), {
            type: 'line',
            data: {
              labels: etiketler,
              datasets: [{
                label: 'Satış (TL)',
                data: satislar,
                borderColor: '#d6ba85',
                backgroundColor: 'rgba(214, 186, 133, .12)',
                borderWidth: 2,
                pointRadius: 0,
                pointHitRadius: 12,
                fill: true,
                tension: 0.25,
              }],
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              interaction: { mode: 'index', intersect: false },
              plugins: {
                legend: { display: false },
                tooltip: {
                  backgroundColor: '#1b1610',
                  borderColor: '#9c7c3c',
                  borderWidth: 1,
                  titleColor: '#d6ba85',
                  bodyColor: '#fff',
                  callbacks: {
                    label: function (ctx) {
                      return ' ' + ctx.parsed.y.toLocaleString('tr-TR', {
                        minimumFractionDigits: 2, maximumFractionDigits: 2,
                      }) + ' TL';
                    },
                  },
                },
              },
              scales: {
                x: {
                  ticks: { color: '#8a8271', maxTicksLimit: 8, maxRotation: 0 },
                  grid: { color: 'rgba(255,255,255,.05)' },
                },
                y: {
                  ticks: {
                    color: '#8a8271',
                    callback: function (deger) {
                      return deger.toLocaleString('tr-TR');
                    },
                  },
                  grid: { color: 'rgba(255,255,255,.07)' },
                },
              },
            },
          });
    }

    var aralikKutusu = document.getElementById('detail-ranges');
    if (aralikKutusu) {
      aralikKutusu.querySelectorAll('button[data-gun]').forEach(function (btn) {
        btn.addEventListener('click', function () {
          aralikKutusu.querySelectorAll('button').forEach(function (b) {
            b.classList.remove('is-active');
          });
          btn.classList.add('is-active');
          grafigiYukle(parseInt(btn.getAttribute('data-gun'), 10) || 7);
        });
      });
    }

    grafigiYukle(7);
  });
})();
