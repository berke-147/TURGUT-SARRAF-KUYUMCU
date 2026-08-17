/*
 * Piyasa Durumu panosu (koyu tema, ticker tablo).
 * store/views.py -> rates_api uç noktasını periyodik olarak çağırıp
 * ÜRÜN/YÖN/ALIŞ/SATIŞ/FARK/%/SAAT sütunlarını sayfa yenilenmeden günceller.
 */
(function () {
  var REFRESH_MS = 3000;

  document.addEventListener('DOMContentLoaded', function () {
    var grid = document.getElementById('rate-grid');
    if (!grid || !grid.classList.contains('price-board')) return;

    var ratesUrl = grid.getAttribute('data-rates-url');
    if (!ratesUrl) return;

    var updatedEl = document.getElementById('board-updated');
    var changedEl = document.getElementById('board-changed');

    function formatNum(value, decimals) {
      var num = parseFloat(value);
      if (isNaN(num)) return value;
      var dec = (typeof decimals === 'number') ? decimals : 2;
      return num.toLocaleString('tr-TR', {
        minimumFractionDigits: dec,
        maximumFractionDigits: dec,
      });
    }

    function formatInt(value) {
      var num = parseFloat(value);
      if (isNaN(num)) return value;
      return Math.round(num).toLocaleString('tr-TR', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      });
    }

    function applyDirection(el, pct) {
      el.classList.remove('up', 'down');
      if (pct > 0) el.classList.add('up');
      else if (pct < 0) el.classList.add('down');
    }

    function refreshBoard() {
      fetch(ratesUrl, { cache: 'no-store' })
        .then(function (response) {
          if (!response.ok) throw new Error('İstek başarısız: ' + response.status);
          return response.json();
        })
        .then(function (items) {
          var nowStr = new Date().toLocaleTimeString('tr-TR');
          var anyChanged = false;

          items.forEach(function (item) {
            // --- Başlıktaki hızlı özet (HAS / ONS-USD) ---
            var quick = grid.querySelector('[data-quick="' + item.code + '"]');
            if (quick) {
              var qBuy = quick.querySelector('[data-bf="qbuy"]');
              var qSell = quick.querySelector('[data-bf="qsell"]');
              if (item.code === 'HAS') {
                // Başlık HAS alanına HER ZAMAN ham alış ve ham satış gelir
                if (qBuy) qBuy.textContent = formatNum(item.raw_buy_price || item.buy_price, 2);
                if (qSell) qSell.textContent = formatNum(item.raw_sell_price || item.sell_price, 2);
              } else {
                if (qBuy) qBuy.textContent = formatNum(item.buy_price, 2);
                if (qSell) qSell.textContent = formatNum(item.final_sell_price, 2);
              }
            }

            // --- Tablo satırı ---
            var row = grid.querySelector('.board-row[data-code="' + item.code + '"]');
            if (!row) return;

            var buyEl = row.querySelector('[data-bf="buy"]');
            var priceEl = row.querySelector('[data-bf="price"]');
            var farkEl = row.querySelector('[data-bf="fark"]');
            var changeEl = row.querySelector('[data-bf="change"]');
            var dirEl = row.querySelector('[data-bf="dir"]');
            var timeEl = row.querySelector('[data-bf="time"]');

            var newPriceText = formatInt(item.final_sell_price);
            if (priceEl && priceEl.textContent !== newPriceText) {
              anyChanged = true;
              if (timeEl) timeEl.textContent = nowStr;
            }
            if (priceEl) priceEl.textContent = newPriceText;
            if (buyEl) buyEl.textContent = formatInt(item.buy_price);

            var pct = parseFloat(item.change_percent) || 0;
            var fark = parseFloat(item.change_amount) || 0;

            if (changeEl) {
              changeEl.textContent = (pct > 0 ? '+' : '') + pct.toFixed(2) + '%';
              applyDirection(changeEl, pct);
            }
            if (farkEl) {
              farkEl.textContent = (fark > 0 ? '+' : '') + formatInt(fark);
              applyDirection(farkEl, fark);
            }
            if (dirEl) {
              dirEl.textContent = pct > 0 ? '▲' : pct < 0 ? '▼' : '–';
              applyDirection(dirEl, pct);
            }
          });

          if (updatedEl) updatedEl.textContent = nowStr;
          if (anyChanged && changedEl) changedEl.textContent = nowStr;
        })
        .catch(function (err) {
          console.error('Piyasa panosu güncellenemedi:', err);
        });
    }

    refreshBoard();
    setInterval(refreshBoard, REFRESH_MS);
  });
})();
