import os
import django
import random

# 1. Django Ayarlarını Tanıtıyoruz
# (Proje adın 'core' olduğu için 'core.settings' yazdık)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# 2. Modelleri Çağırıyoruz
from store.models import FinancialData

def robot_calistir():
    print("📡 Dış piyasadan veriler çekiliyor (Simülasyon)...")
    print("-" * 50)
    
    # SENARYO: Piyasadan şu an gelen canlı veriler bunlar olsun
    # (Normalde burası internetten çekilecek, şimdilik elle yazıyoruz)
    gelen_piyasa_verileri = {
        'HAS':    {'alis': 3050.00, 'satis': 3060.00}, # Has Altın
        'USD':    {'alis': 34.10,   'satis': 34.20},   # Dolar
        'EUR':    {'alis': 37.50,   'satis': 37.60},   # Euro
        'CEYREK': {'alis': 4900.00, 'satis': 5000.00}, # Çeyrek Altın
    }

    for kod, veriler in gelen_piyasa_verileri.items():
        # Bu kod veritabanında var mı? Varsa getir, yoksa oluştur.
        obj, created = FinancialData.objects.get_or_create(
            code=kod,
            defaults={'name': kod} # Eğer yoksa adını kodla aynı yap
        )
        
        # ROBOT GÖREVİ: Sadece Alış/Satış fiyatlarını güncelle
        # (Senin kar marjına dokunmaz)
        obj.buy_price = veriler['alis']
        obj.sell_price = veriler['satis']
        
        obj.save()
        
        # EKRANA BİLGİ VER
        print(f"✅ {kod} GÜNCELLENDİ")
        print(f"   • Piyasa Fiyatı : {obj.sell_price} TL")
        print(f"   • Senin Karın   : %{obj.profit_margin}")
        print(f"   • SİTE FİYATI   : {obj.final_sell_price} TL")
        print("-" * 50)

if __name__ == "__main__":
    robot_calistir()