from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import (
    Product, News, FinancialData, Category,
    ProductColorOption, ContactMessage, Blog,
)


class PanelLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'panel-input', 'autofocus': True})
        self.fields['password'].widget.attrs.update({'class': 'panel-input'})


class ProductForm(forms.ModelForm):
    """
    Ana ürün formu. Görsel galerisi (ProductImage), renk seçenekleri ve ölçü
    seçenekleri BU formda YOK - onlar panel_views.py içinde product_create/
    product_edit view'ında ayrıca, request.POST/request.FILES üzerinden elle
    işlenir (bkz. o view'lardaki yorumlar). Renk/ölçü ürün bazlı OPSİYONELDİR:
    hiç işaretlenmezse/girilmezse o varyasyon sitede hiç görünmez.
    """
    renkler = forms.MultipleChoiceField(
        choices=ProductColorOption.RENK_SECENEKLERI,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Renk Seçenekleri (opsiyonel)",
    )
    olculer = forms.CharField(
        required=False,
        label="Ölçü Seçenekleri (opsiyonel)",
        help_text="Virgülle ayırarak yaz, ör: 12,13,14,15,16",
        widget=forms.TextInput(attrs={'class': 'panel-input', 'placeholder': 'ör. 12,13,14,15,16'}),
    )

    class Meta:
        model = Product
        fields = [
            'name', 'description', 'category', 'sku', 'stone_type',
            'product_type',
            'weight_gram', 'purity', 'labor_cost', 'price_multiplier',
            'fixed_price',
            'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'panel-input'}),
            'description': forms.Textarea(attrs={'class': 'panel-input', 'rows': 4}),
            'category': forms.Select(attrs={'class': 'panel-input'}),
            'sku': forms.TextInput(attrs={'class': 'panel-input', 'placeholder': 'ör. YZK-001'}),
            'stone_type': forms.Select(attrs={'class': 'panel-input'}),
            'product_type': forms.Select(attrs={'class': 'panel-input', 'id': 'id_product_type'}),
            'weight_gram': forms.NumberInput(attrs={'class': 'panel-input', 'step': '0.01'}),
            'purity': forms.Select(attrs={'class': 'panel-input'}),
            'labor_cost': forms.NumberInput(attrs={'class': 'panel-input', 'step': '0.01'}),
            'price_multiplier': forms.NumberInput(attrs={'class': 'panel-input', 'step': '0.0001'}),
            'fixed_price': forms.NumberInput(attrs={'class': 'panel-input', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'panel-checkbox'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Düzenleme ekranında mevcut renk seçimlerini işaretli göster.
        if self.instance and self.instance.pk:
            self.fields['renkler'].initial = list(
                self.instance.renk_secenekleri.values_list('renk', flat=True)
            )
            self.fields['olculer'].initial = ', '.join(
                self.instance.olcu_secenekleri.values_list('olcu', flat=True)
            )

    def clean(self):
        cleaned = super().clean()
        urun_tipi = cleaned.get('product_type')

        if urun_tipi == 'iscilikli':
            if cleaned.get('weight_gram') in (None, ''):
                self.add_error('weight_gram', 'İşçilikli ürünlerde gramaj zorunludur.')
            if cleaned.get('purity') in (None, ''):
                self.add_error('purity', 'İşçilikli ürünlerde ayar zorunludur.')
        elif urun_tipi == 'sabit':
            if cleaned.get('fixed_price') in (None, ''):
                self.add_error('fixed_price', 'Sabit fiyatlı ürünlerde satış fiyatı zorunludur.')

        return cleaned

    def clean_olculer(self):
        ham = self.cleaned_data.get('olculer', '')
        parcalar = [p.strip() for p in ham.split(',') if p.strip()]
        # Tekrarları kaldır, sırayı koru.
        gorulmus = []
        for p in parcalar:
            if p not in gorulmus:
                gorulmus.append(p)
        return gorulmus


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'display_order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'panel-input', 'placeholder': 'ör. Yüzük, Kolye, Bilezik'}),
            'display_order': forms.NumberInput(attrs={'class': 'panel-input'}),
        }


class ContactMessageForm(forms.ModelForm):
    """Site içindeki İletişim & Mağaza sayfasındaki genel iletişim formu."""
    class Meta:
        model = ContactMessage
        fields = ['name', 'phone', 'email', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'panel-input', 'placeholder': 'Ad Soyad'}),
            'phone': forms.TextInput(attrs={'class': 'panel-input', 'placeholder': 'Telefon (opsiyonel)'}),
            'email': forms.EmailInput(attrs={'class': 'panel-input', 'placeholder': 'E-posta (opsiyonel)'}),
            'message': forms.Textarea(attrs={'class': 'panel-input', 'rows': 5, 'placeholder': 'Mesajınız'}),
        }


_FINANCIAL_WIDGETS = {
    'code': forms.TextInput(attrs={'class': 'panel-input', 'placeholder': 'ör. GRAM24, USD (boşluksuz, büyük harf)'}),
    'name': forms.TextInput(attrs={'class': 'panel-input'}),
    'buy_price': forms.NumberInput(attrs={'class': 'panel-input', 'step': '0.0001'}),
    'sell_price': forms.NumberInput(attrs={'class': 'panel-input', 'step': '0.0001'}),
    'buy_multiplier': forms.NumberInput(attrs={'class': 'panel-input', 'step': '0.0001'}),
    'sell_multiplier': forms.NumberInput(attrs={'class': 'panel-input', 'step': '0.0001'}),
    'display_order': forms.NumberInput(attrs={'class': 'panel-input'}),
    'is_visible': forms.CheckboxInput(attrs={'class': 'panel-checkbox'}),
}


class FinancialCreateForm(forms.ModelForm):
    """
    Panelden yeni bir piyasa kalemi (altın/döviz/özel) eklemek için kullanılır.
    Kod, robotun otomatik tanıdığı kodlardan biri DEĞİLSE (ör. HAS, CEYREK, USD
    gibi services.py'de tanımlı olanlar dışında bir şeyse), fiyatı robot ASLA
    güncellemez - burada girdiğin alış/satış fiyatı sabit kalır, elle
    güncellemen gerekir.
    """
    class Meta:
        model = FinancialData
        fields = [
            'code', 'name', 'buy_price', 'sell_price',
            'buy_multiplier', 'sell_multiplier', 'is_visible', 'display_order',
        ]
        widgets = _FINANCIAL_WIDGETS

    def clean_code(self):
        code = self.cleaned_data['code'].strip().upper().replace(' ', '')
        if FinancialData.objects.filter(code=code).exists():
            raise forms.ValidationError('Bu kod zaten kullanılıyor, başka bir kod seç.')
        return code


class FinancialEditForm(forms.ModelForm):
    """
    Panelden mevcut bir kalemi düzenlemek için kullanılır. Kod alanı burada
    YOK - kod, robotun kaydı eşleştirdiği anahtardır, sonradan değiştirilmez.
    Robotun tanıdığı bir kodsa (ör. HAS, CEYREK...) buradan girilen alış/satış
    fiyatı bir sonraki otomatik güncellemede robot tarafından üzerine yazılır;
    çarpanlar, görünürlük ve sıra alanları HER ZAMAN korunur.
    """
    class Meta:
        model = FinancialData
        fields = [
            'name', 'buy_price', 'sell_price',
            'buy_multiplier', 'sell_multiplier', 'is_visible', 'display_order',
        ]
        widgets = _FINANCIAL_WIDGETS


class BlogForm(forms.ModelForm):
    class Meta:
        model = Blog
        fields = ['title', 'excerpt', 'content', 'cover_image', 'display_order', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'panel-input'}),
            'excerpt': forms.TextInput(attrs={'class': 'panel-input', 'placeholder': 'Boş bırakırsan içerikten otomatik kısaltılır'}),
            'content': forms.Textarea(attrs={'class': 'panel-input', 'rows': 10}),
            'cover_image': forms.ClearableFileInput(attrs={'class': 'panel-input'}),
            'display_order': forms.NumberInput(attrs={'class': 'panel-input'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'panel-checkbox'}),
        }


class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ['title', 'content', 'image', 'category', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'panel-input'}),
            'content': forms.Textarea(attrs={'class': 'panel-input', 'rows': 8}),
            'image': forms.ClearableFileInput(attrs={'class': 'panel-input'}),
            'category': forms.Select(attrs={'class': 'panel-input'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'panel-checkbox'}),
        }
