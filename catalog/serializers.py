from rest_framework import serializers
from .models import (
    Sector, Company, Category, Product, 
    ProductImage, ProductFeatureValue, ProductFeature
)

class SectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sector
        fields = ['id', 'name']


class CompanySerializer(serializers.ModelSerializer):
    sector_name = serializers.CharField(source='sector.name', read_only=True)
    
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'slug', 'sector', 'sector_name', 'description', 
            'logo', 'primary_color', 'secondary_color', 'text_color',
            'address', 'phone', 'website', 'created_at'
        ]
        read_only_fields = ['slug', 'created_at']


class CategorySerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'company', 'company_name', 'name', 'description', 'image', 'order', 'product_count']
    
    def get_product_count(self, obj):
        return obj.products.count()


class ProductFeatureSerializer(serializers.ModelSerializer):
    sector_name = serializers.CharField(source='sector.name', read_only=True)
    
    class Meta:
        model = ProductFeature
        fields = ['id', 'sector', 'sector_name', 'name']


class ProductFeatureValueSerializer(serializers.ModelSerializer):
    feature_name = serializers.CharField(source='feature.name', read_only=True)
    
    class Meta:
        model = ProductFeatureValue
        fields = ['id', 'product', 'feature', 'feature_name', 'value']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'image', 'is_primary', 'order']


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    company_name = serializers.CharField(source='category.company.name', read_only=True)
    primary_image = serializers.SerializerMethodField()
    discount_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'category', 'category_name', 'company_name', 'name', 
            'description', 'price', 'show_price', 'discount_price', 
            'stock', 'show_stock', 'featured', 'primary_image', 'discount_percentage'
        ]
    
    def get_primary_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if not primary_image:
            primary_image = obj.images.first()
        
        if primary_image:
            return self.context['request'].build_absolute_uri(primary_image.image.url)
        return None
    
    def get_discount_percentage(self, obj):
        if obj.price and obj.discount_price and obj.price > 0:
            discount = float(obj.price) - float(obj.discount_price)
            percentage = (discount / float(obj.price)) * 100
            return round(percentage)
        return 0


class ProductDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    company = serializers.SerializerMethodField()
    images = ProductImageSerializer(many=True, read_only=True)
    features = ProductFeatureValueSerializer(source='feature_values', many=True, read_only=True)
    discount_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'category', 'category_name', 'company', 'name', 
            'description', 'price', 'show_price', 'discount_price', 
            'stock', 'show_stock', 'featured', 'created_at', 'updated_at',
            'images', 'features', 'discount_percentage'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_company(self, obj):
        company = obj.category.company
        return {
            'id': company.id,
            'name': company.name,
            'slug': company.slug,
            'logo': self.context['request'].build_absolute_uri(company.logo.url) if company.logo else None
        }
    
    def get_discount_percentage(self, obj):
        if obj.price and obj.discount_price and obj.price > 0:
            discount = float(obj.price) - float(obj.discount_price)
            percentage = (discount / float(obj.price)) * 100
            return round(percentage)
        return 0 