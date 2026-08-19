from django.urls import path
from . import views
from . import panel_views

urlpatterns = [
    path('piyasa-durumu/', views.market_page, name='market'),
    path('piyasa-durumu/<str:code>/', views.market_detail, name='market_detail'),
    path('urunler/', views.product_list, name='product_list'),
    path('urunler/<slug:slug>/', views.product_detail, name='product_detail'),
    path('haberler/<slug:slug>/', views.news_detail, name='news_detail'),
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),
    path('cevirici/', views.converter_page, name='converter'),
    path('iletisim/', views.contact_page, name='contact'),
    path('whatsapp/', views.whatsapp_redirect, name='whatsapp_redirect'),
    path('api/kurlar/', views.rates_api, name='rates_api'),
    path('api/kurlar/<str:code>/gecmis/', views.rate_history_api, name='rate_history_api'),

    # ---- Dükkan sahibi paneli (ana menüde linki yok) ----
    path('panel/giris/', panel_views.PanelLoginView.as_view(), name='panel_login'),
    path('panel/cikis/', panel_views.PanelLogoutView.as_view(), name='panel_logout'),
    path('panel/', panel_views.dashboard, name='panel_dashboard'),

    path('panel/finansal/', panel_views.finance_list, name='panel_finance_list'),
    path('panel/finansal/kaynak-sec/', panel_views.finance_source_picker, name='panel_finance_source_picker'),
    path('panel/finansal/yeni/', panel_views.finance_create, name='panel_finance_create'),
    path('panel/finansal/<str:code>/duzenle/', panel_views.finance_edit, name='panel_finance_edit'),
    path('panel/finansal/<str:code>/sil/', panel_views.finance_delete, name='panel_finance_delete'),

    path('panel/urunler/', panel_views.product_list, name='panel_product_list'),
    path('panel/urunler/yeni/', panel_views.product_create, name='panel_product_create'),
    path('panel/urunler/<int:pk>/duzenle/', panel_views.product_edit, name='panel_product_edit'),
    path('panel/urunler/<int:pk>/sil/', panel_views.product_delete, name='panel_product_delete'),
    path('panel/urunler/gorsel/<int:pk>/sil/', panel_views.product_image_delete, name='panel_product_image_delete'),
    path('panel/urunler/<int:pk>/gorsel-sirala/', panel_views.product_image_reorder, name='panel_product_image_reorder'),

    path('panel/kategoriler/', panel_views.category_list, name='panel_category_list'),
    path('panel/kategoriler/<int:pk>/sil/', panel_views.category_delete, name='panel_category_delete'),

    path('panel/mesajlar/', panel_views.contact_message_list, name='panel_contact_message_list'),
    path('panel/mesajlar/<int:pk>/okundu/', panel_views.contact_message_mark_read, name='panel_contact_message_mark_read'),
    path('panel/mesajlar/<int:pk>/sil/', panel_views.contact_message_delete, name='panel_contact_message_delete'),

    path('panel/whatsapp-istatistik/', panel_views.whatsapp_stats, name='panel_whatsapp_stats'),

    path('panel/haberler/', panel_views.news_list, name='panel_news_list'),
    path('panel/haberler/yeni/', panel_views.news_create, name='panel_news_create'),
    path('panel/haberler/<int:pk>/duzenle/', panel_views.news_edit, name='panel_news_edit'),
    path('panel/haberler/<int:pk>/sil/', panel_views.news_delete, name='panel_news_delete'),

    path('panel/blog/', panel_views.blog_list, name='panel_blog_list'),
    path('panel/blog/yeni/', panel_views.blog_create, name='panel_blog_create'),
    path('panel/blog/<int:pk>/duzenle/', panel_views.blog_edit, name='panel_blog_edit'),
    path('panel/blog/<int:pk>/sil/', panel_views.blog_delete, name='panel_blog_delete'),
]
