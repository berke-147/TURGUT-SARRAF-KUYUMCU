/*
 * Piyasa Durumu kartlarını sayfayı yeniden yüklemeden günceller.
 * store/views.py -> rates_api uç noktasını periyodik olarak çağırır.
 *
 * Not: Bu sadece EKRANI veritabanındaki en güncel değerle senkron tutar.
 * Değerlerin gerçekten tazelenmesi için "python manage.py update_rates"
 * komutunun sunucu tarafında düzenli aralıklarla çalışması gerekir.
 */
(function () {
  var REFRESH_MS = 3000; // 3 saniyede bir güncelle

  document.addEventListener('DOMContentLoaded', function () {
    var grid = document.getElementById('rate-grid');
    if (!grid) return;
    // /piyasa-durumu/ sayfasındaki koyu tema pano board.js tarafından yönetilir.
    if (grid.classList.contains('price-board')) return;

    var ratesUrl = grid.getAttribute('data-rates-url');
    if (!ratesUrl) return;

    var note = document.getElementById('rate-updated-note');

    function formatTL(value) {
      var num = parseFloat(value);
      if (isNaN(num)) return value;
      return num.toLocaleString('tr-TR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }) + ' TL';
    }

    function refreshRates() {
      fetch(ratesUrl, { cache: 'no-store' })
        .then(function (response) {
          if (!response.ok) throw new Error('İstek başarısız: ' + response.status);
          return response.json();
        })
        .then(function (items) {
          items.forEach(function (item) {
            var card = grid.querySelector('[data-code="' + item.code + '"]');
            if (!card) return;

            var priceEl = card.querySelector('[data-field="price"]');
            var buyEl = card.querySelector('[data-field="buy"]');
            var changeEl = card.querySelector('[data-field="change"]');

            if (priceEl) priceEl.textContent = formatTL(item.final_sell_price);
            if (buyEl) buyEl.textContent = 'Alış: ' + formatTL(item.buy_price);

            if (changeEl) {
              var pct = parseFloat(item.change_percent);
              if (isNaN(pct)) pct = 0;
              var sign = pct > 0 ? '+' : '';
              changeEl.textContent = sign + pct.toFixed(2) + '%';
              changeEl.classList.remove('up', 'down');
              if (pct > 0) changeEl.classList.add('up');
              else if (pct < 0) changeEl.classList.add('down');
            }
          });

          if (note) {
            var now = new Date();
            note.textContent = 'Son güncelleme: ' + now.toLocaleTimeString('tr-TR');
          }
        })
        .catch(function (err) {
          console.error('Kur verisi güncellenemedi:', err);
        });
    }

    refreshRates();
    setInterval(refreshRates, REFRESH_MS);
  });
})();
