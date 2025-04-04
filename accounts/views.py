from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegisterForm, UserLoginForm, UserProfileUpdateForm, CompanyForm
from catalog.models import Company
from django.urls import reverse

def register_view(request):
    """Kullanıcı kaydı görünümü"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Hesabınız başarıyla oluşturuldu!")
            return redirect('catalog:home')
    else:
        form = UserRegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    """Kullanıcı girişi görünümü"""
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "Başarıyla giriş yaptınız!")
                return redirect('dashboard')
    else:
        form = UserLoginForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def logout_view(request):
    """Kullanıcı çıkışı görünümü"""
    logout(request)
    messages.success(request, "Başarıyla çıkış yaptınız!")
    return redirect('catalog:home')

@login_required
def dashboard_view(request):
    """Kullanıcı paneli görünümü"""
    try:
        company = Company.objects.get(user=request.user)
        has_company = True
    except Company.DoesNotExist:
        company = None
        has_company = False
    
    context = {
        'company': company,
        'has_company': has_company,
    }
    return render(request, 'accounts/dashboard.html', context)

@login_required
def profile_update_view(request):
    """Kullanıcı profili güncelleme görünümü"""
    profile = request.user.profile
    
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profiliniz başarıyla güncellendi!")
            return redirect('dashboard')
    else:
        form = UserProfileUpdateForm(instance=profile)
    
    return render(request, 'accounts/profile_update.html', {'form': form})

@login_required
def company_create_view(request):
    """Firma oluşturma görünümü"""
    # Kullanıcının zaten bir şirketi varsa, güncelleme sayfasına yönlendir
    try:
        company = Company.objects.get(user=request.user)
        return redirect('update_company')
    except Company.DoesNotExist:
        pass
    
    if request.method == 'POST':
        form = CompanyForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            company = form.save()
            messages.success(request, "Firmanız başarıyla oluşturuldu!")
            return redirect('dashboard')
    else:
        form = CompanyForm(user=request.user)
    
    return render(request, 'accounts/company_form.html', {'form': form, 'title': 'Firma Oluştur'})

@login_required
def company_update_view(request):
    """Firma güncelleme görünümü"""
    try:
        company = Company.objects.get(user=request.user)
    except Company.DoesNotExist:
        return redirect('create_company')
    
    if request.method == 'POST':
        form = CompanyForm(request.POST, request.FILES, instance=company, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Firma bilgileriniz başarıyla güncellendi!")
            return redirect('dashboard')
    else:
        form = CompanyForm(instance=company, user=request.user)
    
    return render(request, 'accounts/company_form.html', {'form': form, 'title': 'Firma Güncelle'})
