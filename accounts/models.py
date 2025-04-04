from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    """Kullanıcı profili"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile", verbose_name="Kullanıcı")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Telefon")
    profile_image = models.ImageField(upload_to="profiles/", blank=True, null=True, verbose_name="Profil Resmi")
    
    def __str__(self):
        return f"{self.user.username} Profili"
    
    class Meta:
        verbose_name = "Kullanıcı Profili"
        verbose_name_plural = "Kullanıcı Profilleri"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Yeni kullanıcı oluşturulduğunda profil oluştur"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Kullanıcı kaydedildiğinde profili de kaydet"""
    instance.profile.save()
