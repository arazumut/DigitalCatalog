from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from .models import Sector, Company, Category, Product, ProductImage, ProductFeature, ProductFeatureValue
from django.db.models import Q
import qrcode
from io import BytesIO
from PIL import Image
from django.core.files import File
from .utils import track_catalog_visit, track_product_view, track_category_view
from django.utils import timezone
from datetime import timedelta
import json
from .utils import (
    track_catalog_visit, track_product_view, track_category_view,
    get_visitor_count, get_visit_count, get_top_products, get_top_categories,
    get_daily_visits, get_visitor_devices, render_to_pdf, generate_catalog_pdf
)

def home_view(request):
    """Ana sayfa görünümü"""
    sectors = Sector.objects.all()
    featured_companies = Company.objects.all()[:6]
    
    context = {
        'sectors': sectors,
        'featured_companies': featured_companies,
    }
    return render(request, 'catalog/home.html', context)

def company_catalog_view(request, slug):
    """Firma kataloğu görünümü"""
    company = get_object_or_404(Company, slug=slug)
    categories = company.categories.all()
    
    # Ziyaret istatistiğini kaydet
    if hasattr(request, 'visitor'):
        track_catalog_visit(company, request.visitor)
    
    selected_category = request.GET.get('category', None)
    if selected_category:
        category = get_object_or_404(Category, id=selected_category, company=company)
        products = category.products.all()
        
        # Kategori görüntüleme istatistiğini kaydet
        if hasattr(request, 'visitor'):
            track_category_view(category, request.visitor)
    else:
        # Varsayılan olarak ilk kategoriyi seç
        if categories.exists():
            category = categories.first()
            products = category.products.all()
            
            # Kategori görüntüleme istatistiğini kaydet
            if hasattr(request, 'visitor') and category:
                track_category_view(category, request.visitor)
        else:
            category = None
            products = []
    
    context = {
        'company': company,
        'categories': categories,
        'selected_category': category,
        'products': products,
    }
    return render(request, 'catalog/company_catalog.html', context)


def product_detail_view(request, slug, product_id):
    """Ürün detay görünümü"""
    company = get_object_or_404(Company, slug=slug)
    product = get_object_or_404(Product, id=product_id, category__company=company)
    
    # Ürün görüntüleme istatistiğini kaydet
    if hasattr(request, 'visitor'):
        track_product_view(product, request.visitor)
    
    context = {
        'company': company,
        'product': product,
        'images': product.images.all(),
        'features': product.feature_values.all()
    }
    return render(request, 'catalog/product_detail.html', context)

def search_products_view(request, slug):
    """Ürün arama görünümü"""
    company = get_object_or_404(Company, slug=slug)
    query = request.GET.get('q', '')
    
    # Ziyaret istatistiğini kaydet
    if hasattr(request, 'visitor'):
        track_catalog_visit(company, request.visitor)
    
    if query:
        products = Product.objects.filter(
            Q(category__company=company) & 
            (Q(name__icontains=query) | Q(description__icontains=query))
        )
    else:
        products = []
    
    context = {
        'company': company,
        'products': products,
        'query': query,
    }
    return render(request, 'catalog/search_results.html', context)

def generate_qr_code_view(request, slug):
    """QR kod oluşturma görünümü"""
    company = get_object_or_404(Company, slug=slug)
    
    # QR kod yoksa oluştur
    if not company.qr_code:
        company.save()  # save metodu QR kodu oluşturacak
    
    return redirect(company.qr_code.url)

@login_required
def category_list_view(request):
    """Kategori listesi görünümü"""
    try:
        company = Company.objects.get(user=request.user)
        categories = company.categories.all()
    except Company.DoesNotExist:
        return redirect('create_company')
    
    context = {
        'company': company,
        'categories': categories,
    }
    return render(request, 'catalog/category_list.html', context)

@login_required
def category_create_view(request):
    """Kategori oluşturma görünümü"""
    try:
        company = Company.objects.get(user=request.user)
    except Company.DoesNotExist:
        return redirect('create_company')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        image = request.FILES.get('image')
        
        category = Category.objects.create(
            company=company,
            name=name,
            description=description,
            image=image
        )
        
        messages.success(request, "Kategori başarıyla oluşturuldu!")
        return redirect('catalog:category_list')
    
    return render(request, 'catalog/category_form.html', {'company': company})

@login_required
def category_update_view(request, category_id):
    """Kategori güncelleme görünümü"""
    try:
        company = Company.objects.get(user=request.user)
        category = get_object_or_404(Category, id=category_id, company=company)
    except Company.DoesNotExist:
        return redirect('create_company')
    
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.description = request.POST.get('description', '')
        if 'image' in request.FILES:
            category.image = request.FILES.get('image')
        category.save()
        
        messages.success(request, "Kategori başarıyla güncellendi!")
        return redirect('catalog:category_list')
    
    return render(request, 'catalog/category_form.html', {
        'company': company,
        'category': category
    })

@login_required
def category_delete_view(request, category_id):
    """Kategori silme görünümü"""
    try:
        company = Company.objects.get(user=request.user)
        category = get_object_or_404(Category, id=category_id, company=company)
    except Company.DoesNotExist:
        return redirect('create_company')
    
    if request.method == 'POST':
        category.delete()
        messages.success(request, "Kategori başarıyla silindi!")
        return redirect('catalog:category_list')
    
    return render(request, 'catalog/category_confirm_delete.html', {
        'company': company,
        'category': category
    })

@login_required
def product_list_view(request):
    """Ürün listesi görünümü"""
    try:
        company = Company.objects.get(user=request.user)
        category_id = request.GET.get('category')
        
        if category_id:
            category = get_object_or_404(Category, id=category_id, company=company)
            products = category.products.all()
        else:
            products = Product.objects.filter(category__company=company)
            
        categories = company.categories.all()
    except Company.DoesNotExist:
        return redirect('create_company')
    
    context = {
        'company': company,
        'products': products,
        'categories': categories,
        'selected_category_id': category_id,
    }
    return render(request, 'catalog/product_list.html', context)

@login_required
def product_create_view(request):
    """Ürün oluşturma görünümü"""
    try:
        company = Company.objects.get(user=request.user)
        categories = company.categories.all()
        
        if not categories:
            messages.warning(request, "Ürün eklemeden önce en az bir kategori oluşturmalısınız!")
            return redirect('catalog:category_create')
            
    except Company.DoesNotExist:
        return redirect('create_company')
    
    if request.method == 'POST':
        category_id = request.POST.get('category')
        category = get_object_or_404(Category, id=category_id, company=company)
        
        product = Product.objects.create(
            category=category,
            name=request.POST.get('name'),
            description=request.POST.get('description', ''),
            price=request.POST.get('price') if request.POST.get('price') else None,
            show_price=request.POST.get('show_price') == 'on',
            discount_price=request.POST.get('discount_price') if request.POST.get('discount_price') else None,
            stock=request.POST.get('stock') if request.POST.get('stock') else None,
            show_stock=request.POST.get('show_stock') == 'on',
            featured=request.POST.get('featured') == 'on',
        )
        
        # Ürün resimlerini kaydet
        images = request.FILES.getlist('images')
        for i, image in enumerate(images):
            ProductImage.objects.create(
                product=product,
                image=image,
                is_primary=(i == 0)  # İlk resmi ana resim olarak işaretle
            )
        
        # Ürün özelliklerini kaydet
        if company.sector:
            features = ProductFeature.objects.filter(sector=company.sector)
            for feature in features:
                value = request.POST.get(f'feature_{feature.id}')
                if value:
                    ProductFeatureValue.objects.create(
                        product=product,
                        feature=feature,
                        value=value
                    )
        
        messages.success(request, "Ürün başarıyla oluşturuldu!")
        return redirect('catalog:product_list')
    
    # Sektöre ait özellikleri getir
    features = []
    if company.sector:
        features = ProductFeature.objects.filter(sector=company.sector)
    
    context = {
        'company': company,
        'categories': categories,
        'features': features,
    }
    return render(request, 'catalog/product_form.html', context)

@login_required
def product_update_view(request, product_id):
    """Ürün güncelleme görünümü"""
    try:
        company = Company.objects.get(user=request.user)
        product = get_object_or_404(Product, id=product_id, category__company=company)
        categories = company.categories.all()
    except Company.DoesNotExist:
        return redirect('create_company')
    
    if request.method == 'POST':
        category_id = request.POST.get('category')
        category = get_object_or_404(Category, id=category_id, company=company)
        
        product.category = category
        product.name = request.POST.get('name')
        product.description = request.POST.get('description', '')
        product.price = request.POST.get('price') if request.POST.get('price') else None
        product.show_price = request.POST.get('show_price') == 'on'
        product.discount_price = request.POST.get('discount_price') if request.POST.get('discount_price') else None
        product.stock = request.POST.get('stock') if request.POST.get('stock') else None
        product.show_stock = request.POST.get('show_stock') == 'on'
        product.featured = request.POST.get('featured') == 'on'
        product.save()
        
        # Yeni ürün resimleri ekle
        images = request.FILES.getlist('images')
        if images:
            # Eğer yeni resimler eklendiyse, ilk resmi ana resim yap, diğerlerini normal resim
            for i, image in enumerate(images):
                ProductImage.objects.create(
                    product=product,
                    image=image,
                    is_primary=(i == 0 and not product.images.filter(is_primary=True).exists())
                )
        
        # Ürün özelliklerini güncelle
        if company.sector:
            features = ProductFeature.objects.filter(sector=company.sector)
            for feature in features:
                value = request.POST.get(f'feature_{feature.id}')
                if value:
                    obj, created = ProductFeatureValue.objects.update_or_create(
                        product=product,
                        feature=feature,
                        defaults={'value': value}
                    )
                else:
                    # Değer boşsa ve varsa sil
                    ProductFeatureValue.objects.filter(product=product, feature=feature).delete()
        
        messages.success(request, "Ürün başarıyla güncellendi!")
        return redirect('catalog:product_list')
    
    # Sektöre ait özellikleri getir
    features = []
    if company.sector:
        features = ProductFeature.objects.filter(sector=company.sector)
    
    context = {
        'company': company,
        'product': product,
        'categories': categories,
        'features': features,
        'product_images': product.images.all(),
        'feature_values': {fv.feature_id: fv.value for fv in product.feature_values.all()}
    }
    return render(request, 'catalog/product_form.html', context)

@login_required
def product_delete_view(request, product_id):
    """Ürün silme görünümü"""
    try:
        company = Company.objects.get(user=request.user)
        product = get_object_or_404(Product, id=product_id, category__company=company)
    except Company.DoesNotExist:
        return redirect('create_company')
    
    if request.method == 'POST':
        product.delete()
        messages.success(request, "Ürün başarıyla silindi!")
        return redirect('catalog:product_list')
    
    return render(request, 'catalog/product_confirm_delete.html', {
        'company': company,
        'product': product
    })

@login_required
def product_image_delete_view(request, image_id):
    """Ürün resmi silme görünümü (AJAX)"""
    try:
        company = Company.objects.get(user=request.user)
        image = get_object_or_404(ProductImage, id=image_id, product__category__company=company)
    except Company.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'İzin reddedildi'}, status=403)
    
    is_primary = image.is_primary
    image.delete()
    
    # Eğer silinen resim ana resimse ve başka resimler varsa, bir tanesini ana resim yap
    if is_primary:
        product = image.product
        remaining_images = product.images.all()
        if remaining_images.exists():
            first_image = remaining_images.first()
            first_image.is_primary = True
            first_image.save()
    
    return JsonResponse({'success': True})

@login_required
def set_primary_image_view(request, image_id):
    """Ürün ana resmini ayarlama görünümü (AJAX)"""
    try:
        company = Company.objects.get(user=request.user)
        image = get_object_or_404(ProductImage, id=image_id, product__category__company=company)
    except Company.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'İzin reddedildi'}, status=403)
    
    product = image.product
    
    # Önce tüm resimleri ana resim olmaktan çıkar
    product.images.update(is_primary=False)
    
    # Seçilen resmi ana resim yap
    image.is_primary = True
    image.save()
    
    return JsonResponse({'success': True})

@login_required
def statistics_dashboard_view(request):
    """İstatistik gösterge paneli görünümü"""
    if not request.user.is_authenticated:
        return redirect('login')
        
    company = get_object_or_404(Company, user=request.user)
    
    # İstek parametreleri ve periyot ayarları
    period = request.GET.get('period', '30')
    days = int(period)
    
    # Önbellek anahtarı (cache key) 
    cache_key = f"stats_{company.id}_{days}"
    
    try:
        # Çeşitli istatistikleri hesapla
        visitor_count = get_visitor_count(company, days)
        visit_count = get_visit_count(company, days)
        top_products = get_top_products(company, 5, days)
        top_categories = get_top_categories(company, 5, days)
        daily_visits = get_daily_visits(company, days)
        devices = get_visitor_devices(company, days)
        
        # Chart.js verilerini hazırla
        daily_labels = [str(visit['day']) for visit in daily_visits]
        daily_data = [visit['count'] for visit in daily_visits]
        
        device_labels = list(devices.keys())
        device_data = list(devices.values())
        
        # JSON formatına dönüştür
        import json
        daily_labels_json = json.dumps(daily_labels)
        daily_data_json = json.dumps(daily_data)  
        device_labels_json = json.dumps(device_labels)
        device_data_json = json.dumps(device_data)
        
        context = {
            'company': company,
            'period': period,
            'visitor_count': visitor_count,
            'visit_count': visit_count,
            'top_products': top_products,
            'top_categories': top_categories,
            'daily_visits': daily_visits,
            'devices': devices,
            'daily_labels_json': daily_labels_json,
            'daily_data_json': daily_data_json,
            'device_labels_json': device_labels_json,
            'device_data_json': device_data_json
        }
    except Exception as e:
        # Hata durumunda varsayılan değerler
        context = {
            'company': company,
            'period': period,
            'visitor_count': 0,
            'visit_count': 0,
            'top_products': [],
            'top_categories': [],
            'daily_visits': [],
            'devices': {'mobile': 0, 'tablet': 0, 'desktop': 0, 'other': 0},
            'daily_labels_json': '[]',
            'daily_data_json': '[]',
            'device_labels_json': '[]', 
            'device_data_json': '[]',
            'error': str(e)
        }
    
    return render(request, 'catalog/statistics_dashboard.html', context)

@login_required
def statistics_api_view(request):
    """İstatistik verileri API görünümü - AJAX istekleri için"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    company = get_object_or_404(Company, user=request.user)
    
    # İstek parametreleri
    period = request.GET.get('period', '30')
    days = int(period)
    
    # Önbellek anahtarı
    cache_key = f"stats_api_{company.id}_{days}"
    
    try:
        # İstatistikleri hesapla
        visitor_count = get_visitor_count(company, days)
        visit_count = get_visit_count(company, days)
        top_products = get_top_products(company, 5, days)
        top_categories = get_top_categories(company, 5, days)
        daily_visits = list(get_daily_visits(company, days))
        devices = get_visitor_devices(company, days)
        
        data = {
            'visitor_count': visitor_count,
            'visit_count': visit_count,
            'top_products': top_products,
            'top_categories': top_categories,
            'daily_visits': daily_visits,
            'devices': devices
        }
    except Exception as e:
        data = {
            'error': str(e),
            'visitor_count': 0,
            'visit_count': 0,
            'top_products': [],
            'top_categories': [],
            'daily_visits': [],
            'devices': {'mobile': 0, 'tablet': 0, 'desktop': 0, 'other': 0}
        }
    
    return JsonResponse(data)

@login_required
def generate_pdf_view(request):
    """Kullanıcının firması için katalog PDF'i oluşturur"""
    company = request.user.company
    
    if request.method == 'POST':
        # Form verilerini işle
        selected_categories = request.POST.getlist('categories')
        if selected_categories:
            selected_categories = [int(cat_id) for cat_id in selected_categories]
            pdf = generate_catalog_pdf(company, selected_categories=selected_categories)
        else:
            pdf = generate_catalog_pdf(company)
        
        # Dosya adını hazırla
        filename = f"{company.name.replace(' ', '_')}_katalog.pdf"
        
        # PDF'i indir
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.write(pdf.content)
        return response
    
    # GET isteği için form sayfasını göster
    categories = Category.objects.filter(company=company)
    context = {
        'company': company,
        'categories': categories,
    }
    
    return render(request, 'catalog/generate_pdf.html', context)

@login_required
def preview_pdf_view(request):
    """Kullanıcının firması için katalog PDF'ini önizleme olarak gösterir"""
    company = request.user.company
    
    if request.method == 'POST':
        # Form verilerini işle
        selected_categories = request.POST.getlist('categories')
        if selected_categories:
            selected_categories = [int(cat_id) for cat_id in selected_categories]
            pdf = generate_catalog_pdf(company, selected_categories=selected_categories)
        else:
            pdf = generate_catalog_pdf(company)
        
        # Tarayıcıda göster
        return pdf
    
    # GET isteği için önizleme sayfasına yönlendir
    return redirect('catalog:generate_pdf')
