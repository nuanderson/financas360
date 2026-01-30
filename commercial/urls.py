from django.urls import path
from . import views

app_name = 'commercial'

urlpatterns = [
    # CLIENTES
    path('empresa/<int:company_id>/clientes/', views.CustomerListView.as_view(), name='customer_list'),
    path('empresa/<int:company_id>/clientes/novo/', views.CustomerCreateView.as_view(), name='customer_create'),
    path('empresa/<int:company_id>/clientes/<int:pk>/editar/', views.CustomerUpdateView.as_view(), name='customer_update'),

    # FORNECEDORES
    path('empresa/<int:company_id>/fornecedores/', views.SupplierListView.as_view(), name='supplier_list'),
    path('empresa/<int:company_id>/fornecedores/novo/', views.SupplierCreateView.as_view(), name='supplier_create'),
    path('empresa/<int:company_id>/fornecedores/<int:pk>/editar/', views.SupplierUpdateView.as_view(), name='supplier_update'),

    # SERVIÇOS
    path('empresa/<int:company_id>/servicos/', views.ServiceListView.as_view(), name='service_list'),
    path('empresa/<int:company_id>/servicos/novo/', views.ServiceCreateView.as_view(), name='service_create'),
    path('empresa/<int:company_id>/servicos/<int:pk>/editar/', views.ServiceUpdateView.as_view(), name='service_update'),

    # VENDAS
    path('empresa/<int:company_id>/vendas/', views.SaleListView.as_view(), name='sale_list'),
    path('empresa/<int:company_id>/vendas/novo/', views.SaleCreateView.as_view(), name='sale_create'),

    # CONTAS BANCÁRIAS
    path('empresa/<int:company_id>/bancos/', views.BankAccountListView.as_view(), name='bank_account_list'),
    path('empresa/<int:company_id>/bancos/novo/', views.BankAccountCreateView.as_view(), name='bank_account_create'),
    path('empresa/<int:company_id>/bancos/<int:pk>/editar/', views.BankAccountUpdateView.as_view(), name='bank_account_update'),

    # FINANCEIRO - CONTAS A RECEBER
    path('empresa/<int:company_id>/contas-a-receber/', views.ReceivableListView.as_view(), name='receivable_list'),
    path('empresa/<int:company_id>/contas-a-receber/<int:pk>/baixar/', views.mark_as_paid, name='mark_as_paid'),

    # FINANCEIRO - CONTAS A PAGAR
    path('empresa/<int:company_id>/contas-a-pagar/', views.PayableListView.as_view(), name='payable_list'),
    path('empresa/<int:company_id>/contas-a-pagar/nova/', views.ExpenseCreateView.as_view(), name='expense_create'),
    path('empresa/<int:company_id>/contas-a-pagar/<int:pk>/pagar/', views.mark_as_paid_expense, name='mark_as_paid_expense'),

    # EXTRATO (Adicione esta linha junto com os outros de banco)
    path('empresa/<int:company_id>/bancos/<int:pk>/extrato/', views.BankAccountDetailView.as_view(), name='bank_account_detail'),

    # DASHBOARD
    path('empresa/<int:company_id>/dashboard/', views.DashboardView.as_view(), name='dashboard'),
]