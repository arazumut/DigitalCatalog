from django.contrib import admin
from .models import (
    Sector, Company, Category, ProductFeature, 
    Product, ProductImage, ProductFeatureValue
)

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductFeatureValueInline(admin.TabularInline):
    model = ProductFeatureValue
    extra = 1

class CategoryInline(admin.TabularInline):
    model = Category
    extra = 1

@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'sector', 'user', 'created_at')
    list_filter = ('sector', 'created_at')
    search_fields = ('name', 'user__username', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [CategoryInline]

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'order')
    list_filter = ('company',)
    search_fields = ('name', 'company__name')
    list_editable = ('order',)

@admin.register(ProductFeature)
class ProductFeatureAdmin(admin.ModelAdmin):
    list_display = ('name', 'sector')
    list_filter = ('sector',)
    search_fields = ('name', 'sector__name')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'show_price', 'featured', 'order')
    list_filter = ('category', 'featured', 'show_price', 'created_at')
    search_fields = ('name', 'description', 'category__name')
    list_editable = ('price', 'show_price', 'featured', 'order')
    inlines = [ProductImageInline, ProductFeatureValueInline]

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'is_primary', 'order')
    list_filter = ('is_primary',)
    list_editable = ('is_primary', 'order')

@admin.register(ProductFeatureValue)
class ProductFeatureValueAdmin(admin.ModelAdmin):
    list_display = ('product', 'feature', 'value')
    list_filter = ('feature',)
    search_fields = ('value', 'product__name', 'feature__name')
