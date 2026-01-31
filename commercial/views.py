from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from dateutil.relativedelta import relativedelta
from .models import Customer, Supplier, Service, Sale, BankAccount, MonthlyGoal
from .forms import CustomerForm, SupplierForm, ServiceForm, SaleForm, BankAccountForm, ExpenseForm, MonthlyGoalForm
from core.models import Company, Transaction
import json
from datetime import datetime

# --- MIXIN DE SEGURANÇA ---
class CompanyFilteredMixin:
    """Garante que o usuário só veja/edite dados da empresa ativa"""
    def get_queryset(self):
        # Pega a empresa ativa da sessão (assumindo que você tem essa lógica no middleware ou session)
        # Se não tiver, ajuste para pegar de self.request.user.companies.first() ou similar
        company_id = self.kwargs.get('company_id') 
        # NOTA: O ideal é pegar do active_company na view se já estiver disponível
        return super().get_queryset().filter(company_id=company_id)

    def form_valid(self, form):
        company_id = self.kwargs.get('company_id')
        company = Company.objects.get(id=company_id)
        form.instance.company = company
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_company'] = Company.objects.get(id=self.kwargs.get('company_id'))
        return context

# --- CLIENTES ---
class CustomerListView(LoginRequiredMixin, CompanyFilteredMixin, ListView):
    model = Customer
    template_name = 'commercial/customer_list.html'
    context_object_name = 'customers'

class CustomerCreateView(LoginRequiredMixin, CompanyFilteredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'commercial/customer_form.html'
    
    def get_success_url(self):
        return reverse_lazy('commercial:customer_list', kwargs={'company_id': self.kwargs['company_id']})

class CustomerUpdateView(LoginRequiredMixin, CompanyFilteredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'commercial/customer_form.html'
    
    def get_success_url(self):
        return reverse_lazy('commercial:customer_list', kwargs={'company_id': self.kwargs['company_id']})

# --- FORNECEDORES ---
class SupplierListView(LoginRequiredMixin, CompanyFilteredMixin, ListView):
    model = Supplier
    template_name = 'commercial/supplier_list.html'
    context_object_name = 'suppliers'

class SupplierCreateView(LoginRequiredMixin, CompanyFilteredMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'commercial/supplier_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company_id'] = self.kwargs['company_id']
        return kwargs

    def get_success_url(self):
        return reverse_lazy('commercial:supplier_list', kwargs={'company_id': self.kwargs['company_id']})

class SupplierUpdateView(LoginRequiredMixin, CompanyFilteredMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'commercial/supplier_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company_id'] = self.kwargs['company_id']
        return kwargs

    def get_success_url(self):
        return reverse_lazy('commercial:supplier_list', kwargs={'company_id': self.kwargs['company_id']})

# --- SERVIÇOS ---
class ServiceListView(LoginRequiredMixin, CompanyFilteredMixin, ListView):
    model = Service
    template_name = 'commercial/service_list.html'
    context_object_name = 'services'

class ServiceCreateView(LoginRequiredMixin, CompanyFilteredMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = 'commercial/service_form.html'
    
    def get_success_url(self):
        return reverse_lazy('commercial:service_list', kwargs={'company_id': self.kwargs['company_id']})

class ServiceUpdateView(LoginRequiredMixin, CompanyFilteredMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = 'commercial/service_form.html'
    
    def get_success_url(self):
        return reverse_lazy('commercial:service_list', kwargs={'company_id': self.kwargs['company_id']})

# --- VENDAS / COMERCIAL ---

class SaleListView(LoginRequiredMixin, CompanyFilteredMixin, ListView):
    model = Sale
    template_name = 'commercial/sale_list.html'
    context_object_name = 'sales'
    ordering = ['-sale_date'] # Vendas mais recentes primeiro

class SaleCreateView(LoginRequiredMixin, CompanyFilteredMixin, CreateView):
    model = Sale
    form_class = SaleForm
    template_name = 'commercial/sale_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company_id'] = self.kwargs['company_id']
        return kwargs

    def get_success_url(self):
        # Ao salvar, volta para a lista de vendas
        return reverse_lazy('commercial:sale_list', kwargs={'company_id': self.kwargs['company_id']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Busca os serviços dessa empresa
        services = Service.objects.filter(company_id=self.kwargs['company_id'])
        
        # Cria um dicionário simples: { ID_DO_SERVICO: PRECO}
        prices = {service.id: float(service.default_price) for service in services}

        # Envia para o HTML como um texto JSON
        context['service_prices_json'] = json.dumps(prices)

        return context

# --- CONTAS BANCÁRIAS (TESOURARIA) ---

class BankAccountListView(LoginRequiredMixin, CompanyFilteredMixin, ListView):
    model = BankAccount
    template_name = 'commercial/bank_account_list.html'
    context_object_name = 'bank_accounts'

class BankAccountCreateView(LoginRequiredMixin, CompanyFilteredMixin, CreateView):
    model = BankAccount
    form_class = BankAccountForm
    template_name = 'commercial/bank_account_form.html'
    
    def get_success_url(self):
        return reverse_lazy('commercial:bank_account_list', kwargs={'company_id': self.kwargs['company_id']})

class BankAccountUpdateView(LoginRequiredMixin, CompanyFilteredMixin, UpdateView):
    model = BankAccount
    form_class = BankAccountForm
    template_name = 'commercial/bank_account_form.html'
    
    def get_success_url(self):
        return reverse_lazy('commercial:bank_account_list', kwargs={'company_id': self.kwargs['company_id']})

# --- FINANCEIRO: CONTAS A RECEBER ---

class ReceivableListView(LoginRequiredMixin, CompanyFilteredMixin, ListView):
    model = Transaction
    template_name = 'commercial/receivable_list.html'
    context_object_name = 'transactions'
    
    def get_queryset(self):
        # Filtra: Da empresa ativa + Tipo Receita + Status Pendente
        return Transaction.objects.filter(
            company_id=self.kwargs['company_id'],
            account__account_type='R',              # Receita
            status='PENDING'       # Apenas o que não foi pago
        ).order_by('due_date')     # Ordena por vencimento (mais urgentes primeiro)

# --- AÇÃO: DAR BAIXA (RECEBER) ---
def mark_as_paid(request, company_id, pk):
    """
    Muda o status da transação para PAGO e define a data de pagamento como HOJE.
    """
    transaction = get_object_or_404(Transaction, pk=pk, company_id=company_id)
    
    # Atualiza os dados
    transaction.status = 'PAID'
    transaction.payment_date = timezone.now().date()
    transaction.save()
    
    messages.success(request, f"Recebimento de {transaction.description} confirmado com sucesso!")
    
    # Volta para a lista de contas a receber
    return redirect('commercial:receivable_list', company_id=company_id)

# --- FINANCEIRO: CONTAS A PAGAR ---

class ExpenseCreateView(LoginRequiredMixin, CompanyFilteredMixin, CreateView):
    model = Transaction
    form_class = ExpenseForm
    template_name = 'commercial/expense_form.html'
    
    def form_valid(self, form):
        # Define campos automáticos que não estão no form
        form.instance.company_id = self.kwargs['company_id']
        form.instance.type = 'D' # Define como DESPESA
        form.instance.status = 'PENDING' # Nasce como Pendente
        form.instance.date = timezone.now().date() # Data de criação da transação
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company_id'] = self.kwargs['company_id']
        return kwargs

    def get_success_url(self):
        return reverse_lazy('commercial:payable_list', kwargs={'company_id': self.kwargs['company_id']})

class PayableListView(LoginRequiredMixin, CompanyFilteredMixin, ListView):
    model = Transaction
    template_name = 'commercial/payable_list.html'
    context_object_name = 'transactions'
    
    def get_queryset(self):
        return Transaction.objects.filter(
            company_id=self.kwargs['company_id'],
            # Filtra onde a conta é de DESPESA ('D')
            account__account_type='D',
            status='PENDING'
        ).order_by('due_date')

# --- AÇÃO: PAGAR CONTA ---
def mark_as_paid_expense(request, company_id, pk):
    transaction = get_object_or_404(Transaction, pk=pk, company_id=company_id)
    
    transaction.status = 'PAID'
    transaction.payment_date = timezone.now().date()
    transaction.save()
    
    messages.success(request, f"Conta '{transaction.description}' paga com sucesso!")
    return redirect('commercial:payable_list', company_id=company_id)

# --- EXTRATO BANCÁRIO ---

class BankAccountDetailView(LoginRequiredMixin, CompanyFilteredMixin, DetailView):
    model = BankAccount
    template_name = 'commercial/bank_account_detail.html'
    context_object_name = 'bank_account'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 1. Busca todas as transações DESTE banco
        transactions = Transaction.objects.filter(
            bank_account=self.object
        ).order_by('-date', '-id') # Mais recentes primeiro
        
        # 2. Calcula o Saldo em Tempo Real
        # Soma tudo que entrou (Receita Paga)
        total_in = transactions.filter(account__account_type='R', status='PAID').aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Soma tudo que saiu (Despesa Paga)
        total_out = transactions.filter(account__account_type='D', status='PAID').aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Saldo Atual = Saldo Inicial + Entradas - Saídas
        current_balance = self.object.initial_balance + total_in - total_out
        
        # Envia para o HTML
        context['transactions'] = transactions
        context['current_balance'] = current_balance
        context['total_in'] = total_in
        context['total_out'] = total_out
        
        return context

# --- DASHBOARD (HOME) ---

class DashboardView(LoginRequiredMixin, CompanyFilteredMixin, TemplateView):
    template_name = 'commercial/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company_id = self.kwargs['company_id']
        today = timezone.now().date()
        first_day_month = today.replace(day=1)
        
        # --- CARDS (MANTIDOS) ---
        sales_month = Sale.objects.filter(
            company_id=company_id,
            sale_date__gte=first_day_month,
            status='CONFIRMED'
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

        to_receive = Transaction.objects.filter(company_id=company_id, account__account_type='R', status='PENDING').aggregate(Sum('amount'))['amount__sum'] or 0
        to_pay = Transaction.objects.filter(company_id=company_id, account__account_type='D', status='PENDING').aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Saldo (Cálculo Rápido)
        total_initial = BankAccount.objects.filter(company_id=company_id).aggregate(Sum('initial_balance'))['initial_balance__sum'] or 0
        total_in = Transaction.objects.filter(company_id=company_id, account__account_type='R', status='PAID').aggregate(Sum('amount'))['amount__sum'] or 0
        total_out = Transaction.objects.filter(company_id=company_id, account__account_type='D', status='PAID').aggregate(Sum('amount'))['amount__sum'] or 0
        current_balance = total_initial + total_in - total_out

        # --- GRÁFICO 1: FLUXO DE CAIXA (Últimos 6 Meses) ---
        last_6_months = today - relativedelta(months=5)
        
        # Receitas por Mês
        inflows = Transaction.objects.filter(
            company_id=company_id, 
            account__account_type='R', 
            status='PAID',
            date__gte=last_6_months.replace(day=1)
        ).annotate(month=TruncMonth('date')).values('month').annotate(total=Sum('amount')).order_by('month')

        # Despesas por Mês
        outflows = Transaction.objects.filter(
            company_id=company_id, 
            account__account_type='D', 
            status='PAID',
            date__gte=last_6_months.replace(day=1)
        ).annotate(month=TruncMonth('date')).values('month').annotate(total=Sum('amount')).order_by('month')

        # Prepara dados para o JS (Labels e Arrays)
        months_labels = []
        data_in = []
        data_out = []
        
        # Lógica simples para preencher os meses (garante ordem correta mesmo se mês for zerado)
        for i in range(5, -1, -1):
            date_cursor = today - relativedelta(months=i)
            month_str = date_cursor.strftime('%b/%Y') # Ex: Jan/2026
            months_labels.append(month_str)
            
            # Busca valor no queryset
            val_in = next((item['total'] for item in inflows if item['month'].month == date_cursor.month), 0)
            val_out = next((item['total'] for item in outflows if item['month'].month == date_cursor.month), 0)
            
            data_in.append(float(val_in))
            data_out.append(float(val_out))

        # --- GRÁFICO 2: FATURAMENTO POR SERVIÇO (Top 5) ---
        services_ranking = Sale.objects.filter(
            company_id=company_id,
            status='CONFIRMED'
        ).values('service__name').annotate(total=Sum('total_amount')).order_by('-total')[:5]

        service_labels = [item['service__name'] for item in services_ranking]
        service_data = [float(item['total']) for item in services_ranking]

        # Contexto Final
        context.update({
            'sales_month': sales_month,
            'to_receive': to_receive,
            'to_pay': to_pay,
            'current_balance': current_balance,
            # Dados dos Gráficos
            'chart_months': json.dumps(months_labels),
            'chart_in': json.dumps(data_in),
            'chart_out': json.dumps(data_out),
            'service_labels': json.dumps(service_labels),
            'service_data': json.dumps(service_data),
        })
        
        return context

# --- DRE GERENCIAL (Report) ---

class DREView(LoginRequiredMixin, CompanyFilteredMixin, TemplateView):
    template_name = 'commercial/dre_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company_id = self.kwargs['company_id']
        
        # Filtro de Data (Padrão: Mês Atual)
        month_str = self.request.GET.get('month')
        if month_str:
            date_ref = datetime.strptime(month_str, '%Y-%m').date()
        else:
            date_ref = timezone.now().date().replace(day=1)

        # Função auxiliar para somar por prefixo de código
        def get_sum(prefix_list, type_filter=None):
            # Cria filtro OR para múltiplos prefixos
            query = Q()
            for prefix in prefix_list:
                query |= Q(account__code__startswith=prefix)
            
            filters = {
                'company_id': company_id,
                'status': 'PAID', # DRE é regime de CAIXA (o que realmente aconteceu)
                'date__year': date_ref.year,
                'date__month': date_ref.month
            }
            if type_filter:
                filters['account__account_type'] = type_filter
                
            return Transaction.objects.filter(query, **filters).aggregate(Sum('amount'))['amount__sum'] or 0

        # --- CÁLCULO DA DRE (Baseado nos seus Prints) ---

        # 1. RECEITAS TOTAIS (Começam com 1)
        gross_revenue = get_sum(['1.01', '1.03', '1.04']) # Operacional + Outras + Financeiras
        deductions = get_sum(['1.02']) # Deduções/Impostos
        net_revenue = gross_revenue - deductions

        # 2. CUSTOS VARIÁVEIS (Começam com 2)
        variable_costs = get_sum(['2'])
        
        # = MARGEM DE CONTRIBUIÇÃO (Lucro Bruto)
        contribution_margin = net_revenue - variable_costs

        # 3. DESPESAS FIXAS (Começam com 3)
        fixed_expenses = get_sum(['3'])
        
        # = RESULTADO OPERACIONAL (EBITDA aproximado)
        operating_result = contribution_margin - fixed_expenses

        # 4. NÃO OPERACIONAL (Começam com 4)
        # Vamos assumir que o grupo 4 inteiro reduz o lucro, exceto se for configurado diferente.
        non_operating = get_sum(['4']) 

        # = RESULTADO LÍQUIDO (Lucro/Prejuízo Final)
        net_profit = operating_result - non_operating

        # DETALHAMENTO PARA A TABELA (Drill-down)
        # Pega todas as contas com movimento no mês para listar
        details = Transaction.objects.filter(
            company_id=company_id,
            status='PAID',
            date__year=date_ref.year,
            date__month=date_ref.month
        ).values('account__code', 'account__name', 'account__account_type').annotate(total=Sum('amount')).order_by('account__code')

        context.update({
            'current_month': date_ref.strftime('%Y-%m'),
            
            # Totais
            'gross_revenue': gross_revenue,
            'deductions': deductions,
            'net_revenue': net_revenue,
            'variable_costs': variable_costs,
            'contribution_margin': contribution_margin,
            'fixed_expenses': fixed_expenses,
            'operating_result': operating_result,
            'non_operating': non_operating,
            'net_profit': net_profit,
            
            # Detalhes
            'details': details
        })

        return context

# --- QUADRO DE METAS ---

class GoalsDashboardView(LoginRequiredMixin, CompanyFilteredMixin, ListView):
    model = MonthlyGoal
    template_name = 'commercial/goals_dashboard.html'
    context_object_name = 'goals'

    def get_queryset(self):
        # Pega o mês da URL ou usa o mês atual
        month_str = self.request.GET.get('month')
        if month_str:
            self.reference_date = datetime.strptime(month_str, '%Y-%m').date()
        else:
            self.reference_date = timezone.now().date().replace(day=1)
            
        return MonthlyGoal.objects.filter(
            company_id=self.kwargs['company_id'],
            month__year=self.reference_date.year,
            month__month=self.reference_date.month
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        goals_data = []
        
        for goal in context['goals']:
            realized = Transaction.objects.filter(
                company_id=self.kwargs['company_id'],
                account=goal.account,
                date__year=self.reference_date.year,
                date__month=self.reference_date.month,
                status='PAID'
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            # Calcula Porcentagem
            if goal.target_amount > 0:
                percent = (realized / goal.target_amount * 100)
            else:
                percent = 0
            
            # Cálculo do Saldo/Diferença (Para não usar |sub no template)
            difference = goal.target_amount - realized
            
            goals_data.append({
                'name': goal.account.name,
                'type': goal.account.account_type,
                'target': goal.target_amount,
                'realized': realized,
                'percent': round(percent), # Arredonda aqui!
                'difference': difference,  # Manda a diferença pronta
                'id': goal.id
            })
            
        context['goals_data'] = goals_data
        context['current_month'] = self.reference_date.strftime('%Y-%m')
        return context

# View para Criar/Editar Meta
class GoalCreateView(LoginRequiredMixin, CompanyFilteredMixin, CreateView):
    model = MonthlyGoal
    form_class = MonthlyGoalForm
    template_name = 'commercial/goal_form.html'
    
    def form_valid(self, form):
        form.instance.company_id = self.kwargs['company_id']
        # Força o dia 1 para padronizar
        form.instance.month = form.instance.month.replace(day=1)
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company_id'] = self.kwargs['company_id']
        return kwargs

    def get_success_url(self):
        return reverse_lazy('commercial:goals_dashboard', kwargs={'company_id': self.kwargs['company_id']})