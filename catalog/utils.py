from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from .models import CatalogVisit, ProductView, CategoryView, Visitor, Product
import io
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa
from django.conf import settings
import os

def track_catalog_visit(company, visitor):
    """Katalog ziyaretini kaydet"""
    return CatalogVisit.objects.create(company=company, visitor=visitor)

def track_product_view(product, visitor):
    """Ürün görüntülemeyi kaydet"""
    return ProductView.objects.create(product=product, visitor=visitor)

def track_category_view(category, visitor):
    """Kategori görüntülemeyi kaydet"""
    return CategoryView.objects.create(category=category, visitor=visitor)

def get_visitor_count(company, days=30):
    """Belirli bir süredeki benzersiz ziyaretçi sayısını getir"""
    start_date = timezone.now() - timedelta(days=days)
    return CatalogVisit.objects.filter(
        company=company, 
        timestamp__gte=start_date
    ).values('visitor').distinct().count()

def get_visit_count(company, days=30):
    """Belirli bir süredeki toplam ziyaret sayısını getir"""
    start_date = timezone.now() - timedelta(days=days)
    return CatalogVisit.objects.filter(
        company=company, 
        timestamp__gte=start_date
    ).count()

def get_top_products(company, limit=5, days=30):
    """En çok görüntülenen ürünleri getir"""
    start_date = timezone.now() - timedelta(days=days)
    result = []
    products = ProductView.objects.filter(
        product__category__company=company,
        timestamp__gte=start_date
    ).values('product', 'product__name').annotate(
        view_count=Count('product')
    ).order_by('-view_count')[:limit]
    
    for p in products[:limit]:
        result.append({
            'name': p['product__name'],
            'view_count': p['view_count']
        })
    
    return result

def get_top_categories(company, limit=5, days=30):
    """En çok görüntülenen kategorileri getir"""
    start_date = timezone.now() - timedelta(days=days)
    result = []
    categories = CategoryView.objects.filter(
        category__company=company,
        timestamp__gte=start_date
    ).values('category', 'category__name').annotate(
        view_count=Count('category')
    ).order_by('-view_count')[:limit]
    
    for c in categories[:limit]:
        result.append({
            'name': c['category__name'],
            'view_count': c['view_count']
        })
    
    return result

def get_daily_visits(company, days=30):
    """Günlük ziyaret istatistiklerini getir - Optimize edilmiş"""
    start_date = timezone.now() - timedelta(days=days)
    
    if days > 90:
        return get_weekly_visits(company, days)
    
    try:
        from django.db.models.functions import TruncDate
        return CatalogVisit.objects.filter(
            company=company,
            timestamp__gte=start_date
        ).annotate(
            day=TruncDate('timestamp')
        ).values('day').annotate(count=Count('id')).order_by('day')
    except:
        return CatalogVisit.objects.filter(
            company=company,
            timestamp__gte=start_date
        ).extra(
            select={'day': "DATE(timestamp)"}
        ).values('day').annotate(count=Count('id')).order_by('day')

def get_weekly_visits(company, days=90):
    """Haftalık ziyaret istatistiklerini getir - Uzun dönemler için"""
    start_date = timezone.now() - timedelta(days=days)
    from django.db.models.functions import TruncWeek
    
    try:
        return CatalogVisit.objects.filter(
            company=company,
            timestamp__gte=start_date
        ).annotate(
            day=TruncWeek('timestamp')
        ).values('day').annotate(count=Count('id')).order_by('day')
    except:
        daily = CatalogVisit.objects.filter(
            company=company,
            timestamp__gte=start_date
        ).extra(
            select={'day': "DATE(timestamp)"}
        ).values('day').annotate(count=Count('id')).order_by('day')
        
        weekly = {}
        for item in daily:
            week = str(item['day'])[0:7]
            if week in weekly:
                weekly[week] += item['count']
            else:
                weekly[week] = item['count']
                
        return [{'day': week, 'count': count} for week, count in weekly.items()]

def get_visitor_devices(company, days=30):
    """Ziyaretçilerin cihaz dağılımını getir - Optimize edilmiş"""
    start_date = timezone.now() - timedelta(days=days)
    
    visitors = Visitor.objects.filter(
        catalog_visits__company=company,
        catalog_visits__timestamp__gte=start_date
    ).values('id', 'user_agent').distinct()
    
    devices = {
        'mobile': 0,
        'tablet': 0,
        'desktop': 0,
        'other': 0
    }
    
    for visitor in visitors:
        user_agent = visitor.get('user_agent', '').lower()
        if not user_agent:
            devices['other'] += 1
        elif 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
            devices['mobile'] += 1
        elif 'tablet' in user_agent or 'ipad' in user_agent:
            devices['tablet'] += 1
        elif 'windows' in user_agent or 'macintosh' in user_agent or 'linux' in user_agent:
            devices['desktop'] += 1
        else:
            devices['other'] += 1
    
    return devices

def render_to_pdf(template_src, context_dict={}):
    """HTML şablonunu PDF'e dönüştüren yardımcı fonksiyon"""
    template = get_template(template_src)
    html = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

def generate_catalog_pdf(company, products=None, selected_categories=None):
    """Firma kataloğunu PDF olarak oluşturur"""
    
    if products is None:
        if selected_categories:
            # Seçilen kategorilerdeki ürünleri al
            products = Product.objects.filter(
                category__company=company,
                category__id__in=selected_categories
            ).select_related('category').prefetch_related('images', 'feature_values')
        else:
            # Tüm ürünleri al
            products = Product.objects.filter(
                category__company=company
            ).select_related('category').prefetch_related('images', 'feature_values')
    
    # Kategorilere göre ürünleri grupla
    categories = {}
    for product in products:
        if product.category.id not in categories:
            categories[product.category.id] = {
                'category': product.category,
                'products': []
            }
        categories[product.category.id]['products'].append(product)
    
    # Şablon bağlamını hazırla
    context = {
        'company': company,
        'categories': categories.values(),
        'is_pdf': True,  # PDF oluşturulduğunu belirtmek için
        'MEDIA_ROOT': settings.MEDIA_ROOT,
        'static_url': settings.STATIC_URL,
    }
    
    # PDF oluştur
    pdf = render_to_pdf('catalog/pdf_catalog.html', context)
    return pdf 