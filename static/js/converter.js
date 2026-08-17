/*
 * Döviz ve Altın Çevirici.
 * Tüm kalemlerin TL cinsinden birim fiyatını rates_api'den alır,
 * iki kalem arasında çapraz çevrim yapar: sonuç = miktar * fiyat(kaynak) / fiyat(hedef)
 */
(function () {
  document.addEventListener('DOMContentLoaded', function () {
    var box = document.getElementById('converter');
    if (!box) return;

    var ratesUrl = box.getAttribute('data-rates-url');
    var amountEl = document.getElementById('conv-amount');
    var fromEl = document.getElementById('conv-from');
    var toEl = document.getElementById('conv-to');
    var resultEl = document.getElementById('conv-result');
    var noteEl = document.getElementById('conv-note');
    var swapBtn = document.getElementById('conv-swap');

    var rates = {}; // code -> { name, final_sell_price, ... }

    function formatNumber(num) {
      return num.toLocaleString('tr-TR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 4,
      });
    }

    function calculate() {
      var amount = parseFloat(amountEl.value);
      var fromItem = rates[fromEl.value];
      var toItem = rates[toEl.value];

      if (isNaN(amount) || !fromItem || !toItem) {
        resultEl.textContent = '-';
        return;
      }

      var fromPrice = parseFloat(fromItem.final_sell_price);
      var toPrice = parseFloat(toItem.final_sell_price);

      if (!fromPrice || !toPrice) {
        resultEl.textContent = '-';
        return;
      }

      var result = (amount * fromPrice) / toPrice;
      resultEl.textContent = formatNumber(result);
    }

    function loadRates() {
      fetch(ratesUrl, { cache: 'no-store' })
        .then(function (res) { return res.json(); })
        .then(function (items) {
          rates = {};
          items.forEach(function (item) {
            rates[item.code] = item;
          });
          noteEl.textContent = 'Kurlar güncel (' + new Date().toLocaleTimeString('tr-TR') + ')';
          calculate();
        })
        .catch(function () {
          noteEl.textContent = 'Kurlar alınamadı, birkaç saniye sonra tekrar denenecek.';
        });
    }

    amountEl.addEventListener('input', calculate);
    fromEl.addEventListener('change', calculate);
    toEl.addEventListener('change', calculate);
    swapBtn.addEventListener('click', function () {
      var tmp = fromEl.value;
      fromEl.value = toEl.value;
      toEl.value = tmp;
      calculate();
    });

    loadRates();
    setInterval(loadRates, 15000); // kurları 15 saniyede bir tazele
  });
})();
