from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/update/', views.profile_update_view, name='update_profile'),
    path('company/create/', views.company_create_view, name='create_company'),
    path('company/update/', views.company_update_view, name='update_company'),
] 