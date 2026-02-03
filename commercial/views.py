from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from dateutil.relativedelta import relativedelta
from .models import Customer, Supplier, Service, Sale, BankAccount, MonthlyGoal
from .forms import CustomerForm, SupplierForm, ServiceForm, SaleForm, BankAccountForm, ExpenseForm, MonthlyGoalForm
from core.models import Company, Transaction
from django.http import JsonResponse
import json
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

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
    ordering = ['-sale_date', '-id']

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

# 1. EDITAR VENDA
class SaleUpdateView(LoginRequiredMixin, CompanyFilteredMixin, UpdateView):
    model = Sale
    form_class = SaleForm
    template_name = 'commercial/sale_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Venda / Orçamento'
        return context

    def get_success_url(self):
        return reverse_lazy('commercial:sale_list', kwargs={'company_id': self.kwargs['company_id']})

# 2. FECHAR VENDA (Orçamento -> Confirmado)
def sale_confirm(request, company_id, pk):
    # Busca a venda garantindo que pertence à empresa atual
    sale = get_object_or_404(Sale, pk=pk, company_id=company_id)
    
    # LÓGICA DE SEGURANÇA: Só executa se ainda não estiver confirmado
    if sale.status != 'CONFIRMED':
        
        # 1. Muda o status para Fechado
        sale.status = 'CONFIRMED'
        sale.save()
        
        # 2. GERA O FINANCEIRO (CONTAS A RECEBER)
        # Verifica se já gerou antes para não duplicar se o usuário clicar duas vezes
        if not Transaction.objects.filter(sale_origin=sale).exists():
            
            # Calcula valor da parcela
            if sale.installments > 0:
                installment_value = sale.total_amount / sale.installments
            else:
                installment_value = sale.total_amount # Caso seja à vista/0 parcelas

            for i in range(sale.installments or 1):
                # Calcula vencimento (Data da venda + i meses)
                due_date = sale.sale_date + relativedelta(months=i)
                
                # Cria a transação
                Transaction.objects.create(
                    company=sale.company,
                    # Tenta pegar a categoria do serviço. Se não tiver, precisa tratar!
                    # Assumindo que seu model Service tem um campo 'category' ou 'account'
                    account=sale.service.category if hasattr(sale.service, 'category') else None, 
                    amount=installment_value,
                    date=due_date,
                    description=f"Venda {sale.id} - {sale.customer.name} ({i+1}/{sale.installments})",
                    status='PENDING', # A Receber
                    type='I',         # Income (Receita)
                    sale_origin=sale, # Link para poder cancelar depois
                    created_by=request.user
                )
        
        messages.success(request, f"Venda confirmada e financeiro gerado!")
    else:
        messages.info(request, "Esta venda já está fechada.")
    
    return redirect('commercial:sale_list', company_id=company_id)

# 3. CANCELAR VENDA
def sale_cancel(request, company_id, pk):
    # Busca a venda
    sale = get_object_or_404(Sale, pk=pk, company_id=company_id)
    
    # 1. Remove as transações financeiras geradas por essa venda (se houver)
    # Isso evita "lixo" no financeiro
    Transaction.objects.filter(sale_origin=sale).delete()
    
    # 2. Exclui a venda permanentemente
    sale.delete()
    
    messages.success(request, "Venda/Orçamento excluído com sucesso.")
    
    return redirect('commercial:sale_list', company_id=company_id)

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

# --- FINANCEIRO: CONTAS A RECEBER (ATUALIZADO) ---

class AccountReceivableListView(LoginRequiredMixin, CompanyFilteredMixin, ListView):
    model = Transaction
    template_name = 'commercial/receivable_list.html' # <--- AJUSTADO PARA O SEU NOME DE ARQUIVO
    context_object_name = 'transactions'

    def get_queryset(self):
        company_id = self.kwargs['company_id']
        
        # 1. Filtra receitas ('R') desta empresa
        qs = Transaction.objects.filter(company_id=company_id, account__account_type='R')
        
        # 2. FILTRO DE COMPETÊNCIA (MÊS)
        month_str = self.request.GET.get('month')
        
        if month_str:
            try:
                year, month = month_str.split('-')
                qs = qs.filter(date__year=year, date__month=month)
            except ValueError:
                pass 
        else:
            # Padrão: Mês atual
            today = date.today()
            qs = qs.filter(date__year=today.year, date__month=today.month)
            
        return qs.order_by('date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_month'] = self.request.GET.get('month', date.today().strftime('%Y-%m'))
        return context

# --- AÇÃO: ALTERAR STATUS (RECEBER / DESFAZER) ---
def account_receivable_toggle(request, company_id, pk):
    """
    Alterna o status: Se Pendente -> Vira Pago. Se Pago -> Vira Pendente.
    """
    transaction = get_object_or_404(Transaction, pk=pk, company_id=company_id)
    
    if transaction.status == 'PENDING':
        # BAIXA (Receber)
        transaction.status = 'PAID'
        transaction.payment_date = timezone.now().date()
        messages.success(request, f"Recebimento de '{transaction.description}' confirmado!")
    else:
        # ESTORNO (Desfazer)
        transaction.status = 'PENDING'
        transaction.payment_date = None # Limpa a data de pagamento
        messages.warning(request, f"Recebimento de '{transaction.description}' cancelado. Voltou para pendente.")
        
    transaction.save()
    
    # Redireciona mantendo o filtro de mês para o usuário não perder a tela que estava
    # Se a transação for de "2026-02", o filtro volta para "2026-02"
    month_param = f"?month={transaction.date.strftime('%Y-%m')}"
    
    # Usa o 'reverse' para montar a URL com o parametro GET
    return redirect(reverse('commercial:receivable_list', kwargs={'company_id': company_id}) + month_param)

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

# 1. LISTA COM FILTRO DE MÊS (Substitui PayableListView antiga)
class AccountPayableListView(LoginRequiredMixin, CompanyFilteredMixin, ListView):
    model = Transaction
    template_name = 'commercial/payable_list.html' # Nome do seu arquivo template
    context_object_name = 'transactions'

    def get_queryset(self):
        company_id = self.kwargs['company_id']
        
        # Filtra DESPESAS ('D') desta empresa
        qs = Transaction.objects.filter(company_id=company_id, account__account_type='D')
        
        # FILTRO DE COMPETÊNCIA (MÊS)
        month_str = self.request.GET.get('month')
        
        if month_str:
            try:
                year, month = month_str.split('-')
                qs = qs.filter(date__year=year, date__month=month)
            except ValueError:
                pass 
        else:
            # Padrão: Mês atual
            today = date.today()
            qs = qs.filter(date__year=today.year, date__month=today.month)
            
        return qs.order_by('date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_month'] = self.request.GET.get('month', date.today().strftime('%Y-%m'))
        return context

# 2. AÇÃO DE PAGAR / DESFAZER (Substitui mark_as_paid_expense antiga)
def account_payable_toggle(request, company_id, pk):
    transaction = get_object_or_404(Transaction, pk=pk, company_id=company_id)
    
    if transaction.status == 'PENDING':
        # PAGAR
        transaction.status = 'PAID'
        transaction.payment_date = timezone.now().date()
        messages.success(request, f"Conta '{transaction.description}' paga com sucesso!")
    else:
        # ESTORNO (Desfazer)
        transaction.status = 'PENDING'
        transaction.payment_date = None
        messages.warning(request, f"Pagamento de '{transaction.description}' cancelado. Voltou para pendente.")
        
    transaction.save()
    
    # Redireciona mantendo o filtro de mês
    month_param = f"?month={transaction.date.strftime('%Y-%m')}"
    return redirect(reverse('commercial:payable_list', kwargs={'company_id': company_id}) + month_param)

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
        
        # 1. Determina as Datas (Mês Atual e Mês Anterior)
        month_str = self.request.GET.get('month')
        if month_str:
            date_ref = datetime.strptime(month_str, '%Y-%m').date()
        else:
            date_ref = timezone.now().date().replace(day=1)
            
        # Data do mês anterior
        prev_date_ref = date_ref - relativedelta(months=1)

        # 2. Função Auxiliar para Calcular os Números de um Mês Específico
        def calculate_dre_numbers(target_date):
            # Helper para somar transações PAGAS
            def get_sum(prefix_list, type_filter=None):
                query = Q()
                for prefix in prefix_list:
                    query |= Q(account__code__startswith=prefix)
                
                filters = {
                    'company_id': company_id,
                    'status': 'PAID',
                    # --- CORREÇÃO AQUI: REGIME DE CAIXA REAL ---
                    # Filtramos pela data do PAGAMENTO, não pela competência
                    'payment_date__year': target_date.year,
                    'payment_date__month': target_date.month
                }
                if type_filter:
                    filters['account__account_type'] = type_filter
                    
                return Transaction.objects.filter(query, **filters).aggregate(Sum('amount'))['amount__sum'] or 0

            # Cálculos da DRE
            gross_revenue = get_sum(['1.01', '1.03', '1.04']) 
            deductions = get_sum(['1.02']) 
            net_revenue = gross_revenue - deductions
            variable_costs = get_sum(['2'])
            contribution_margin = net_revenue - variable_costs
            fixed_expenses = get_sum(['3'])
            operating_result = contribution_margin - fixed_expenses
            non_operating = get_sum(['4'])
            net_profit = operating_result - non_operating

            return {
                'gross_revenue': gross_revenue,
                'deductions': deductions,
                'net_revenue': net_revenue,
                'variable_costs': variable_costs,
                'contribution_margin': contribution_margin,
                'fixed_expenses': fixed_expenses,
                'operating_result': operating_result,
                'non_operating': non_operating,
                'net_profit': net_profit,
            }

        # 3. Executa o cálculo para os dois períodos
        current = calculate_dre_numbers(date_ref)
        previous = calculate_dre_numbers(prev_date_ref)

        # 4. Calcula as Variâncias (%)
        variances = {}
        for key, value in current.items():
            prev_val = previous.get(key, 0)
            if prev_val and prev_val != 0:
                diff = value - prev_val
                percent = (diff / abs(prev_val)) * 100
            else:
                percent = 0
            
            variances[key] = percent

        # 5. Detalhes para o Drill-down (Corrigido para Payment Date também)
        details = Transaction.objects.filter(
            company_id=company_id,
            status='PAID',
            # --- CORREÇÃO AQUI TAMBÉM ---
            payment_date__year=date_ref.year,
            payment_date__month=date_ref.month
        ).values('account__code', 'account__name', 'account__account_type').annotate(total=Sum('amount')).order_by('account__code')

        # Atualiza contexto
        context.update({
            'current_month': date_ref.strftime('%Y-%m'),
            'prev_month_label': prev_date_ref.strftime('%b/%Y'),
            'details': details,
            
            # Dados Atuais
            **current,
            
            # Variâncias
            'var_gross_revenue': variances['gross_revenue'],
            'var_net_revenue': variances['net_revenue'],
            'var_variable_costs': variances['variable_costs'],
            'var_contribution_margin': variances['contribution_margin'],
            'var_fixed_expenses': variances['fixed_expenses'],
            'var_operating_result': variances['operating_result'],
            'var_non_operating': variances['non_operating'],
            'var_net_profit': variances['net_profit'],
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


def get_supplier_details(request):
    supplier_id = request.GET.get('supplier_id')
    data = {'category_id': None}
    
    if supplier_id:
        try:
            supplier = Supplier.objects.get(id=supplier_id)
            
            # --- CORREÇÃO AQUI ---
            # Usamos 'default_account' conforme seu Model
            if supplier.default_account: 
                data['category_id'] = supplier.default_account.id
                
        except Supplier.DoesNotExist:
            pass
            
    return JsonResponse(data)