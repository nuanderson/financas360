from django.contrib import admin
from .models import Company, ChartOfAccounts, Transaction, Budget

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'management_type')
    search_fields = ('name',)
    filter_horizontal = ('users',)
    list_field = ('management_type',)

@admin.register(ChartOfAccounts)
class ChartOfAccountsAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'account_type', 'company', 'parent_account')
    list_filter = ('company', 'account_type')
    search_fields = ('code', 'name')
    ordering = ('code',)

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    # Agora podemos mostrar e filtrar pela empresa diretamente
    list_display = ('account', 'year', 'annual_amount', 'company')
    list_filter = ('year', 'company') # Filtro direto e eficiente
    search_fields = ('account__name', 'account__code')

admin.site.register(Transaction)