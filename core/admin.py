from django.contrib import admin
from django.urls import path
from django.db.models import Count
from django.db.models.functions import TruncDay
from django.template.response import TemplateResponse
from django.utils.html import format_html
from .models import Company, ChartOfAccounts, Transaction, Budget

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'management_type')
    search_fields = ('name',)
    filter_horizontal = ('users',)
    list_field = ('management_type',)

@admin.register(ChartOfAccounts)
class ChartOfAccountsAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'account_type', 'company')
    list_filter = ('company',)
    search_fields = ('code', 'name', 'company__name')
    ordering = ('code',)

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    # Agora podemos mostrar e filtrar pela empresa diretamente
    list_display = ('account', 'year', 'month', 'amount', 'company')
    list_filter = ('year', 'company') # Filtro direto e eficiente
    search_fields = ('account__name', 'account__code')
    autocomplete_fields = ['account']

    # Filtrar as contas pelo company selecionado
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'account':
            company_id = request.GET.get('company')  # Captura a empresa via GET da URL
            # Tenta pegar a empresa se estivermos editando um orçamento existente
            if not company_id and '/change/' in request.path:
                 try:
                     budget_id = request.path.split('/')[-3]
                     budget = Budget.objects.get(pk=budget_id)
                     company_id = budget.company.id
                 except:
                     pass
            if company_id:
                kwargs["queryset"] = ChartOfAccounts.objects.filter(company_id=company_id).order_by('code')
            else:
                kwargs["queryset"] = ChartOfAccounts.objects.all().order_by('company', 'code')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('account', 'date', 'amount', 'company', 'created_by', 'created_at')
    list_filter = ('date', 'account__company', 'created_by') # Adicionei created_by no filtro lateral
    search_fields = ('description', 'account__name')
    readonly_fields = ('created_by', 'created_at')
    ordering = ('-date',)

    def changelist_view(self, request, extra_context=None):
        # Forçamos o template manualmente antes de renderizar
        self.change_list_template = "admin/core/transaction/change_list.html"
        return super().changelist_view(request, extra_context=extra_context)

    # Salva automaticamente quem criou
    def save_model(self, request, obj, form, change):
        # DEBUG: Isso vai aparecer no seu terminal preto quando você salvar
        print(f"--- TENTANDO SALVAR --- Usuário atual: {request.user}")

        # Se não tem dono (novo ou antigo vazio), define o dono agora
        if not obj.created_by:
            obj.created_by = request.user
            print(f"--- DONO DEFINIDO COMO: {obj.created_by} ---")
            
        super().save_model(request, obj, form, change)

    # 1. Adiciona a URL do relatório dentro deste Admin
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('produtividade/', self.admin_site.admin_view(self.productivity_view), name='transaction_productivity'),
        ]
        return my_urls + urls

    # 2. A lógica do Relatório (fica aqui dentro, e não na views.py)
    def productivity_view(self, request):
        # Filtros de data (opcionais, pegando da URL)
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        queryset = Transaction.objects.all()
        
        # Se tiver filtro de data, aplica
        if start_date and end_date:
            queryset = queryset.filter(created_at__date__range=[start_date, end_date])

        # Agrupa por Dia e Usuário e Conta
        report_data = queryset.annotate(
            day=TruncDay('created_at')
        ).values('day', 'created_by__username').annotate(
            count=Count('id')
        ).order_by('-day', '-count')

        context = {
            # Traz o contexto padrão do admin (menu lateral, título, etc)
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'report_data': report_data,
            'title': 'Relatório de Produtividade',
            'start_date': start_date,
            'end_date': end_date,
        }
        
        # Renderiza o template que vamos criar abaixo
        return TemplateResponse(request, 'admin/productivity.html', context)



