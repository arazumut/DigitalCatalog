from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from colorfield.fields import ColorField
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image, ImageDraw

class Sector(models.Model):
    """Firma sektörleri"""
    name = models.CharField(max_length=100, verbose_name="Sektör Adı")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Sektör"
        verbose_name_plural = "Sektörler"

class Company(models.Model):
    """Firma bilgileri"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="company", verbose_name="Kullanıcı")
    name = models.CharField(max_length=200, verbose_name="Firma Adı")
    sector = models.ForeignKey(Sector, on_delete=models.SET_NULL, null=True, related_name="companies", verbose_name="Sektör")
    logo = models.ImageField(upload_to="logos/", blank=True, null=True, verbose_name="Logo")
    slug = models.SlugField(unique=True, blank=True, verbose_name="Slug")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Telefon")
    address = models.TextField(blank=True, verbose_name="Adres")
    description = models.TextField(blank=True, verbose_name="Açıklama")
    website = models.URLField(blank=True, verbose_name="Web Sitesi")
    
    # Katalog görünüm ayarları
    primary_color = ColorField(default="#0077b6", verbose_name="Ana Renk")
    secondary_color = ColorField(default="#023e8a", verbose_name="İkincil Renk")
    text_color = ColorField(default="#000000", verbose_name="Metin Rengi")
    
    # QR Kod
    qr_code = models.ImageField(upload_to="qrcodes/", blank=True, null=True, verbose_name="QR Kod")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")
    
    def save(self, *args, **kwargs):
        # Slug oluştur
        if not self.slug:
            self.slug = slugify(self.name)
        
        # QR kod oluştur
        if not self.qr_code:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(f"https://{self.get_absolute_url()}")
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            self.qr_code.save(f"{self.slug}-qr.png", File(buffer), save=False)
        
        super().save(*args, **kwargs)
        
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("catalog:company_catalog", kwargs={"slug": self.slug})
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Firma"
        verbose_name_plural = "Firmalar"

class Category(models.Model):
    """Ürün kategorileri"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="categories", verbose_name="Firma")
    name = models.CharField(max_length=100, verbose_name="Kategori Adı")
    description = models.TextField(blank=True, verbose_name="Açıklama")
    image = models.ImageField(upload_to="categories/", blank=True, null=True, verbose_name="Resim")
    order = models.PositiveIntegerField(default=0, verbose_name="Sıralama")
    
    def __str__(self):
        return f"{self.company.name} - {self.name}"
    
    class Meta:
        verbose_name = "Kategori"
        verbose_name_plural = "Kategoriler"
        ordering = ["order", "name"]

class ProductFeature(models.Model):
    """Sektöre göre değişebilen ürün özellikleri"""
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, related_name="features", verbose_name="Sektör")
    name = models.CharField(max_length=100, verbose_name="Özellik Adı")
    
    def __str__(self):
        return f"{self.sector.name} - {self.name}"
    
    class Meta:
        verbose_name = "Ürün Özelliği"
        verbose_name_plural = "Ürün Özellikleri"

class Product(models.Model):
    """Ürün modeli"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products", verbose_name="Kategori")
    name = models.CharField(max_length=200, verbose_name="Ürün Adı")
    description = models.TextField(blank=True, verbose_name="Açıklama")
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Fiyat")
    show_price = models.BooleanField(default=True, verbose_name="Fiyat Göster")
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="İndirimli Fiyat")
    stock = models.PositiveIntegerField(default=0, blank=True, null=True, verbose_name="Stok")
    show_stock = models.BooleanField(default=False, verbose_name="Stok Göster")
    order = models.PositiveIntegerField(default=0, verbose_name="Sıralama")
    featured = models.BooleanField(default=False, verbose_name="Öne Çıkan")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")
    
    def __str__(self):
        return self.name
    
    @property
    def company(self):
        return self.category.company
    
    class Meta:
        verbose_name = "Ürün"
        verbose_name_plural = "Ürünler"
        ordering = ["order", "name"]

class ProductImage(models.Model):
    """Ürün resimleri"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images", verbose_name="Ürün")
    image = models.ImageField(upload_to="products/", verbose_name="Resim")
    is_primary = models.BooleanField(default=False, verbose_name="Ana Resim")
    order = models.PositiveIntegerField(default=0, verbose_name="Sıralama")
    
    def __str__(self):
        return f"{self.product.name} - Resim {self.order}"
    
    class Meta:
        verbose_name = "Ürün Resmi"
        verbose_name_plural = "Ürün Resimleri"
        ordering = ["order"]

class ProductFeatureValue(models.Model):
    """Ürün özellik değerleri"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="feature_values", verbose_name="Ürün")
    feature = models.ForeignKey(ProductFeature, on_delete=models.CASCADE, verbose_name="Özellik")
    value = models.CharField(max_length=255, verbose_name="Değer")
    
    def __str__(self):
        return f"{self.product.name} - {self.feature.name}: {self.value}"
    
    class Meta:
        verbose_name = "Ürün Özellik Değeri"
        verbose_name_plural = "Ürün Özellik Değerleri"
        unique_together = ("product", "feature")

class Visitor(models.Model):
    """Ziyaretçi bilgileri"""
    ip_address = models.GenericIPAddressField(verbose_name="IP Adresi")
    user_agent = models.TextField(blank=True, null=True, verbose_name="Tarayıcı Bilgisi")
    referrer = models.URLField(blank=True, null=True, verbose_name="Referans URL")
    first_visit = models.DateTimeField(auto_now_add=True, verbose_name="İlk Ziyaret")
    last_visit = models.DateTimeField(auto_now=True, verbose_name="Son Ziyaret")
    visit_count = models.PositiveIntegerField(default=1, verbose_name="Ziyaret Sayısı")
    
    def __str__(self):
        return f"{self.ip_address} - {self.visit_count} ziyaret"
    
    class Meta:
        verbose_name = "Ziyaretçi"
        verbose_name_plural = "Ziyaretçiler"

class CatalogVisit(models.Model):
    """Katalog ziyareti"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="visits", verbose_name="Firma")
    visitor = models.ForeignKey(Visitor, on_delete=models.CASCADE, related_name="catalog_visits", verbose_name="Ziyaretçi")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Ziyaret Zamanı")
    
    def __str__(self):
        return f"{self.company.name} - {self.visitor.ip_address} - {self.timestamp}"
    
    class Meta:
        verbose_name = "Katalog Ziyareti"
        verbose_name_plural = "Katalog Ziyaretleri"
        indexes = [
            models.Index(fields=['company', 'timestamp']),
        ]

class ProductView(models.Model):
    """Ürün görüntüleme"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="views", verbose_name="Ürün")
    visitor = models.ForeignKey(Visitor, on_delete=models.CASCADE, related_name="product_views", verbose_name="Ziyaretçi")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Görüntüleme Zamanı")
    
    def __str__(self):
        return f"{self.product.name} - {self.visitor.ip_address} - {self.timestamp}"
    
    class Meta:
        verbose_name = "Ürün Görüntüleme"
        verbose_name_plural = "Ürün Görüntülemeleri"
        indexes = [
            models.Index(fields=['product', 'timestamp']),
        ]

class CategoryView(models.Model):
    """Kategori görüntüleme"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="views", verbose_name="Kategori")
    visitor = models.ForeignKey(Visitor, on_delete=models.CASCADE, related_name="category_views", verbose_name="Ziyaretçi")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Görüntüleme Zamanı")
    
    def __str__(self):
        return f"{self.category.name} - {self.visitor.ip_address} - {self.timestamp}"
    
    class Meta:
        verbose_name = "Kategori Görüntüleme"
        verbose_name_plural = "Kategori Görüntülemeleri"
        indexes = [
            models.Index(fields=['category', 'timestamp']),
        ]
