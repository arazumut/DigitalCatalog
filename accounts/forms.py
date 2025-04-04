from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from catalog.models import Company, Sector
from .models import UserProfile

class UserRegisterForm(UserCreationForm):
    """Kullanıcı kayıt formu"""
    email = forms.EmailField()
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Form alanları için etiketleri Türkçeye çevirelim
        self.fields['username'].label = "Kullanıcı Adı"
        self.fields['email'].label = "E-posta"
        self.fields['password1'].label = "Parola"
        self.fields['password2'].label = "Parola Doğrulama"

class UserLoginForm(AuthenticationForm):
    """Kullanıcı giriş formu"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Form alanları için etiketleri Türkçeye çevirelim
        self.fields['username'].label = "Kullanıcı Adı"
        self.fields['password'].label = "Parola"

class UserProfileUpdateForm(forms.ModelForm):
    """Kullanıcı profil güncelleme formu"""
    email = forms.EmailField(label="E-posta")
    first_name = forms.CharField(max_length=30, label="Ad", required=False)
    last_name = forms.CharField(max_length=150, label="Soyad", required=False)
    
    class Meta:
        model = UserProfile
        fields = ['phone', 'profile_image']
        labels = {
            'phone': 'Telefon',
            'profile_image': 'Profil Resmi',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.user:
            self.fields['email'].initial = self.instance.user.email
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            profile.save()
        return profile

class CompanyForm(forms.ModelForm):
    """Firma oluşturma ve güncelleme formu"""
    class Meta:
        model = Company
        fields = ['name', 'sector', 'logo', 'phone', 'address', 'description', 'website',
                 'primary_color', 'secondary_color', 'text_color']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
    def save(self, commit=True):
        company = super().save(commit=False)
        if self.user and not company.pk:  # Yeni şirket oluşturuluyorsa
            company.user = self.user
        if commit:
            company.save()
        return company 