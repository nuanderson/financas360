from django.contrib import admin
from .models import Company, ChartOfAccounts, Transaction, Budget

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    filter_horizontal = ('users',)

@admin.register(ChartOfAccounts)
class ChartOfAccountsAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'account_type', 'company', 'parent_account')
    list_filter = ('company', 'account_type')
    search_fields = ('code', 'name')
    ordering = ('code',)

admin.site.register(Transaction)
admin.site.register(Budget)
