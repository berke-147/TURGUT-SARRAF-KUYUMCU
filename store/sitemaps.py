"""
Google'a (ve diğer arama motorlarına) sitenin tüm sayfalarını bildiren
sitemap.xml'i otomatik üretir. Yeni bir ürün/haber eklendiğinde ya da
yayından kaldırıldığında elle güncellemen gerekmez - her istek anında
veritabanından taze üretilir.

/sitemap.xml adresinde yayınlanır (bkz. core/urls.py).
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Product, News, Blog


class StaticViewSitemap(Sitemap):
    """Ürün/haber gibi tekil kaydı olmayan, sabit sayfalar."""
    priority = 0.6
    changefreq = 'daily'
    protocol = 'https'

    def items(self):
        return ['home', 'market', 'product_list', 'converter', 'blog_list', 'contact']

    def location(self, item):
        return reverse(item)


class ProductSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.8
    protocol = 'https'

    def items(self):
        return Product.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.created_at

    def location(self, obj):
        return reverse('product_detail', args=[obj.slug])


class NewsSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.5
    protocol = 'https'

    def items(self):
        return News.objects.filter(is_published=True, slug__gt='')

    def lastmod(self, obj):
        return obj.created_at

    def location(self, obj):
        return reverse('news_detail', args=[obj.slug])


class BlogSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.5
    protocol = 'https'

    def items(self):
        return Blog.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.created_at

    def location(self, obj):
        return reverse('blog_detail', args=[obj.slug])
