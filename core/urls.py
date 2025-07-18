from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'core'

urlpatterns = [
    path('empresa/<int:company_id>/plano-de-contas/', views.chart_of_accounts_list, name='chart_of_accounts_list'),
    path('empresa/<int:company_id>/plano-de-contas/<int:account_id>/editar/', views.account_update, name='account_update'),
    path('empresa/<int:company_id>/plano-de-contas/<int:account_id>/excluir/', views.account_delete, name='account_delete'),
    path('empresa/<int:company_id>/ativar/', views.set_active_company, name='set_active_company'),
    # Página de Login
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    # Ação de Logout
    path('logout/', auth_views.LogoutView.as_view(next_page='core:login'), name='logout'),
    # Página principal após o login (Hub de Empresas)
    path('empresas/', views.company_list, name='company_list'),
]
