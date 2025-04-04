from django.utils import timezone
from .models import Visitor

class VisitorMiddleware:
    """Ziyaretçileri izlemek için middleware"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Ziyaretçi bilgilerini al veya oluştur
        if not request.path.startswith('/admin/') and not request.path.startswith('/static/'):
            visitor = self._get_or_create_visitor(request)
            request.visitor = visitor  # View'larda erişim için
        
        # İstek işlemeye devam et
        response = self.get_response(request)
        return response
    
    def _get_or_create_visitor(self, request):
        """Ziyaretçiyi al veya oluştur"""
        ip_address = self._get_client_ip(request)
        
        try:
            visitor = Visitor.objects.get(ip_address=ip_address)
            # Mevcut ziyaretçiyi güncelle
            visitor.visit_count += 1
            visitor.user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]
            visitor.referrer = request.META.get('HTTP_REFERER', '')[:255] if request.META.get('HTTP_REFERER') else None
            visitor.last_visit = timezone.now()
            visitor.save()
        except Visitor.DoesNotExist:
            # Yeni ziyaretçi oluştur
            visitor = Visitor.objects.create(
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                referrer=request.META.get('HTTP_REFERER', '')[:255] if request.META.get('HTTP_REFERER') else None,
            )
            
        return visitor
    
    def _get_client_ip(self, request):
        """Ziyaretçinin IP adresini al"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip 