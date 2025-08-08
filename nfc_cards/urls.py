from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Página inicial geral
    path('', views.home, name='home'),
    
    # URLs de autenticação
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register_view, name='register'),
    
    # URLs para usuários autenticados
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('minha-empresa/', views.minha_empresa_view, name='minha_empresa'),
    path('criar-empresa/', views.create_empresa_view, name='create_empresa'),
    
    # URLs por empresa
    path('<slug:empresa_slug>/', views.empresa_home, name='empresa_home'),
    
    # URLs para Pessoas por empresa
    path('<slug:empresa_slug>/pessoas/', views.PersonListView.as_view(), name='person_list'),
    path('<slug:empresa_slug>/pessoas/nova/', views.PersonCreateView.as_view(), name='person_create'),
    path('<slug:empresa_slug>/pessoas/<slug:person_slug>/', views.PersonDetailView.as_view(), name='person_detail'),
    
    # URLs para Pets por empresa
    path('<slug:empresa_slug>/pets/', views.PetListView.as_view(), name='pet_list'),
    path('<slug:empresa_slug>/pets/novo/', views.PetCreateView.as_view(), name='pet_create'),
    path('<slug:empresa_slug>/pets/<slug:pet_slug>/', views.PetDetailView.as_view(), name='pet_detail'),
    
    # URLs para NFC (mantém compatibilidade)
    path('nfc/<str:codigo>/', views.nfc_redirect, name='nfc_redirect'),
    path('api/nfc/<str:codigo>/', views.api_nfc_info, name='api_nfc_info'),
    
    # URLs diretos por empresa para NFC
    path('<slug:empresa_slug>/nfc/<str:codigo>/', views.nfc_redirect_empresa, name='nfc_redirect_empresa'),
    path('<slug:empresa_slug>/api/nfc/<str:codigo>/', views.api_nfc_info_empresa, name='api_nfc_info_empresa'),
]