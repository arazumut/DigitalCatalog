from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('catalog/<slug:slug>/', views.company_catalog_view, name='company_catalog'),
    path('catalog/<slug:slug>/product/<int:product_id>/', views.product_detail_view, name='product_detail'),
    path('catalog/<slug:slug>/search/', views.search_products_view, name='search_products'),
    path('catalog/<slug:slug>/qr-code/', views.generate_qr_code_view, name='generate_qr'),
    
    # Kategori yönetimi
    path('categories/', views.category_list_view, name='category_list'),
    path('categories/create/', views.category_create_view, name='category_create'),
    path('categories/<int:category_id>/update/', views.category_update_view, name='category_update'),
    path('categories/<int:category_id>/delete/', views.category_delete_view, name='category_delete'),
    
    # Ürün yönetimi
    path('products/', views.product_list_view, name='product_list'),
    path('products/create/', views.product_create_view, name='product_create'),
    path('products/<int:product_id>/update/', views.product_update_view, name='product_update'),
    path('products/<int:product_id>/delete/', views.product_delete_view, name='product_delete'),
    path('products/images/<int:image_id>/delete/', views.product_image_delete_view, name='product_image_delete'),
    path('products/images/<int:image_id>/set-primary/', views.set_primary_image_view, name='set_primary_image'),
] 