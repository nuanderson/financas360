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

    # Filtrar as contas pelo company selecionado
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'account':
            company_id = request.GET.get('company')  # Captura a empresa via GET da URL
            if company_id:
                kwargs["queryset"] = ChartOfAccounts.objects.filter(company_id=company_id)
            else:
                kwargs["queryset"] = ChartOfAccounts.objects.none()  # Nenhuma conta até selecionar empresa
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('account', 'date', 'amount', 'company')
    list_filter = ('date', 'account__company', 'account__account_type')
    search_fields = ('description', 'account__name')
    ordering = ('-date',)


