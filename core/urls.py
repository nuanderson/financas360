from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home_redirect, name='home'),
    # Hub de Empresas
    path('empresas/', views.company_list, name='company_list'),
    path('selecionar-empresa/<int:company_id>/', views.select_company, name='select_company'),
    path('empresas/nova/', views.CompanyCreateView.as_view(), name='company_create'),
    path('empresas/<int:pk>/editar/', views.CompanyUpdateView.as_view(), name='company_update'),
    path('empresas/<int:pk>/excluir/', views.CompanyDeleteView.as_view(), name='company_delete'),
    # Página da Empresa
    path('empresa/<int:company_id>/plano-de-contas/', views.chart_of_accounts_list, name='chart_of_accounts_list'),
    path('empresa/<int:company_id>/plano-de-contas/<int:account_id>/editar/', views.AccountUpdateView.as_view(), name='account_update'),
    path('empresa/<int:company_id>/plano-de-contas/<int:account_id>/excluir/', views.AccountDeleteView.as_view(), name='account_delete'),
    path('empresa/<int:company_id>/plano-de-contas/importar/', views.import_chart_of_accounts, name='import_chart_of_accounts'),
    path('empresa/<int:company_id>/ativar/', views.set_active_company, name='set_active_company'),
    path('empresa/<int:company_id>/dashboard/', views.dashboard_dispatcher, name='dashboard'),
    path('dashboard/', views.dashboard_dispatcher, name='dashboard_no_id'),
    path('empresa/<int:company_id>/dashboard', views.dashboard_dispatcher, name='dashboard'),
    # Página de Lançamentos
    path('lancamentos/', views.transaction_list, name='transaction_list'),
    path('lancamentos/<int:pk>/editar/', views.TransactionUpdateView.as_view(), name='transaction_update'),
    path('lancamentos/<int:pk>/excluir/', views.TransactionDeleteView.as_view(), name='transaction_delete'),
    path('lancamentos/importar/', views.import_transactions, name='import_transactions'),
    path('lancamentos/importar/modelo/', views.download_transaction_template, name='download_transaction_template'),
    # Lançamento de Orçamento (admin)
    path('orcamento/', views.budget_edit_view, name='budget_edit'),
    path('orcamento/definir/', views.budget_entry, name='budget_entry'),
    # Hub de Relatórios
    path('relatorios/', views.reports_hub, name='reports_hub'),
    # DRE Gerencial
    path('relatorios/dre/', views.dre_report, name='dre_report'),
    path('relatorios/dre/pdf/', views.dre_report_pdf, name='dre_report_pdf'),
    # DRE Mensal
    path('relatorios/dre/mensal/', views.dre_mensal, name='dre_mensal'),
    path('relatorios/dre/mensal/pdf/', views.dre_mensal_pdf, name='dre_mensal_pdf'),
    # DRE Comparativo
    path('relatorios/dre/comparativo/', views.dre_comparativo, name='dre_comparativo'),
    # Orçamento vs. Realizado
    path('relatorios/orcamento-vs-realizado/', views.budget_vs_actual_report, name='budget_vs_actual_report'),
    # Extrato Analítico
    path('relatorios/extrato/', views.extrato_analitico, name='extrato_analitico'),
    # Produtividade da Equipe
    path('relatorios/produtividade/', views.productivity_report, name='productivity_report'),
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
    path('api/revenue-vs-expense-12m/', views.revenue_vs_expense_12m_data, name='revenue_vs_expense_12m_data'),
    # Gerenciamento de Usuários (admin only)
    path('usuarios/', views.user_list, name='user_list'),
    path('usuarios/novo/', views.user_create, name='user_create'),
    path('usuarios/<int:user_id>/editar/', views.user_edit, name='user_edit'),
    path('usuarios/<int:user_id>/toggle-ativo/', views.user_toggle_active, name='user_toggle_active'),
    path('usuarios/<int:user_id>/excluir/', views.user_delete, name='user_delete'),
    # Bloco de Notas
    path('notas/', views.note_list, name='note_list'),
    path('notas/nova/', views.NoteCreateView.as_view(), name='note_create'),
    path('notas/editar/<int:pk>/', views.NoteUpdateView.as_view(), name='note_update'),
    path('notas/excluir/<int:pk>/', views.NoteDeleteView.as_view(), name='note_delete'),
    path('notas/tags/nova/', views.tag_create, name='tag_create'),
    path('notas/arquivar/<int:pk>/', views.note_archive, name='note_archive'),
]
