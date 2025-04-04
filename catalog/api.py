from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import (
    Sector, Company, Category, Product, 
    ProductImage, ProductFeatureValue, ProductFeature
)
from .serializers import (
    SectorSerializer, CompanySerializer, CategorySerializer,
    ProductFeatureSerializer, ProductFeatureValueSerializer,
    ProductImageSerializer, ProductListSerializer, ProductDetailSerializer
)

class SectorViewSet(viewsets.ReadOnlyModelViewSet):
    """Sektör API görünümü"""
    queryset = Sector.objects.all()
    serializer_class = SectorSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class CompanyViewSet(viewsets.ReadOnlyModelViewSet):
    """Firma API görünümü"""
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']
    lookup_field = 'slug'
    
    @action(detail=True, methods=['get'])
    def categories(self, request, slug=None):
        """Firmanın kategorilerini listeler"""
        company = self.get_object()
        categories = Category.objects.filter(company=company)
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def featured_products(self, request, slug=None):
        """Firmanın öne çıkan ürünlerini listeler"""
        company = self.get_object()
        products = Product.objects.filter(
            category__company=company, 
            featured=True
        ).select_related('category').prefetch_related('images')
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def products(self, request, slug=None):
        """Firmanın tüm ürünlerini listeler"""
        company = self.get_object()
        category_id = request.query_params.get('category', None)
        
        if category_id:
            products = Product.objects.filter(
                category__company=company,
                category_id=category_id
            ).select_related('category').prefetch_related('images')
        else:
            products = Product.objects.filter(
                category__company=company
            ).select_related('category').prefetch_related('images')
        
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Kategori API görünümü"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    
    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """Kategorinin ürünlerini listeler"""
        category = self.get_object()
        products = Product.objects.filter(
            category=category
        ).select_related('category').prefetch_related('images')
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """Ürün API görünümü"""
    queryset = Product.objects.all().select_related('category').prefetch_related('images', 'feature_values')
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductDetailSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        return context
    
    @action(detail=False, methods=['get'])
    def by_company(self, request):
        """Firma slug'ına göre ürünleri listeler"""
        company_slug = request.query_params.get('company_slug', None)
        if not company_slug:
            return Response({"error": "company_slug parametresi gereklidir"}, status=400)
        
        company = get_object_or_404(Company, slug=company_slug)
        products = Product.objects.filter(
            category__company=company
        ).select_related('category').prefetch_related('images')
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)


class ProductFeatureViewSet(viewsets.ReadOnlyModelViewSet):
    """Ürün Özelliği API görünümü"""
    queryset = ProductFeature.objects.all()
    serializer_class = ProductFeatureSerializer
    permission_classes = [permissions.AllowAny] 