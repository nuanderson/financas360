from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home_redirect, name='home'),
    # Hub de Empresas
    path('empresas/', views.company_list, name='company_list'),
    path('empresas/nova/', views.CompanyCreateView.as_view(), name='company_create'),
    path('empresas/<int:pk>/editar/', views.CompanyUpdateView.as_view(), name='company_update'),
    path('empresas/<int:pk>/excluir/', views.CompanyDeleteView.as_view(), name='company_delete'),
    # Página da Empresa
    path('empresa/<int:company_id>/plano-de-contas/', views.chart_of_accounts_list, name='chart_of_accounts_list'),
    path('empresa/<int:company_id>/plano-de-contas/<int:account_id>/editar/', views.AccountUpdateView.as_view(), name='account_update'),
    path('empresa/<int:company_id>/plano-de-contas/<int:account_id>/excluir/', views.AccountDeleteView.as_view(), name='account_delete'),
    path('empresa/<int:company_id>/plano-de-contas/importar/', views.import_chart_of_accounts, name='import_chart_of_accounts'),
    path('empresa/<int:company_id>/ativar/', views.set_active_company, name='set_active_company'),
    path('empresa/<int:company_id>/dashboard', views.dashboard_dispatcher, name='dashboard'),
    # Página de Lançamentos
    path('lancamentos/', views.transaction_list, name='transaction_list'),
    path('lancamentos/<int:pk>/editar/', views.TransactionUpdateView.as_view(), name='transaction_update'),
    path('lancamentos/<int:pk>/excluir/', views.TransactionDeleteView.as_view(), name='transaction_delete'),
    path('lancamentos/importar/', views.import_transactions, name='import_transactions'),
    path('lancamentos/importar/modelo/', views.download_transaction_template, name='download_transaction_template'),
    # Página de Lançamentos de Orçamentos
    path('orcamento/', views.budget_edit_view, name='budget_edit'),
    # Página de Relatórios
    path('relatorios/dre/', views.dre_report, name='dre_report'),
    path('relatorios/dre/pdf/', views.dre_report_pdf, name='dre_report_pdf'),
    # Página do Quadro Orçamentário
    path('quadro-orcamentario/', views.budget_dashboard, name='budget_dashboard'),
    path('quadro-orcamentario/exportar/', views.export_budget_xls, name='export_budget_xls'),
    # Página de Login
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    # Ação de Logout
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
    # API do Gráfico
    path('api/dados-grafico-despesas', views.expense_chart_data, name='expense_chart_data'),
    path('api/resumo-receita-despesa/', views.revenue_expense_summary_data, name='revenue_expense_summary_data'),
    path('api/budget-deviations-chart/', views.budget_deviations_chart_data, name='budget_deviations_chart_data'),
    path('api/budget-vs-actual-timeline/', views.budget_vs_actual_timeline_data, name='budget_vs_actual_timeline_data'),
    path('api/expense-percentage-chart/', views.expense_percentage_chart_data, name='expense_percentage_chart_data'),
]
