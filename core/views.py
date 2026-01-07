from django.forms import modelformset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import UpdateView, DeleteView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Company, ChartOfAccounts, Transaction, Budget
from .forms import ChartOfAccountsForm, TransactionForm, CompanyForm, CSVImportForm, BudgetForm, TransactionFilterForm
from django.contrib import messages
from django.db.models import Sum, Q, F, Value, DecimalField
from django.db.models.functions import Coalesce 
from datetime import datetime, date
from django.http import JsonResponse, HttpResponse
from dateutil.relativedelta import relativedelta
from django.template.loader import render_to_string
from django.core import serializers
from django.core.paginator import Paginator
from weasyprint import HTML
from decimal import Decimal, InvalidOperation
import calendar
import csv
import io
import json


class AccountUpdateView(LoginRequiredMixin, UpdateView):
    # De qual modelo esta view vai editar os dados
    model = ChartOfAccounts
    # Qual formulário ela vai usar
    form_class = ChartOfAccountsForm
    # Qual template ela vai renderizar
    template_name = 'core/account_update.html'
    # Como a URL chama o ID da conta (pk = primary key)
    pk_url_kwarg = 'account_id'

    def get_queryset(self):
        """
        Sobrescrevemos o queryset para garantir a segurança.
        Isso garante que um usuário só pode editar contas da empresa que ele gerencia.
        """
        company_id = self.kwargs.get('company_id')
        company = get_object_or_404(Company, pk=company_id, users=self.request.user)
        return ChartOfAccounts.objects.filter(company=company)

    def get_form_kwargs(self):
        """
        Este método passa argumentos extras para o __init__ do nosso formulário.
        Usamos para passar a 'company' para que o dropdown de 'conta pai' seja filtrado.
        """
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.get_object().company
        return kwargs

    def get_success_url(self):
        """
        Define para onde o usuário será redirecionado após salvar o formulário com sucesso.
        """
        company_id = self.kwargs.get('company_id')
        return reverse_lazy('core:chart_of_accounts_list', kwargs={'company_id': company_id})

    def get_context_data(self, **kwargs):
        """
        Adiciona dados extras ao contexto do template.
        Precisamos da 'company' no template para o link 'Voltar para a lista' funcionar.
        """
        context = super().get_context_data(**kwargs)
        context['company'] = self.get_object().company
        return context


class AccountDeleteView(LoginRequiredMixin, DeleteView):
    model = ChartOfAccounts
    template_name = 'core/account_confirm_delete.html'
    pk_url_kwarg = 'account_id'

    def get_queryset(self):
        """ Mesma lógica de segurança da view de Update. """
        company_id = self.kwargs.get('company_id')
        company = get_object_or_404(Company, pk=company_id, users=self.request.user)
        return ChartOfAccounts.objects.filter(company=company)

    def get_success_url(self):
        """ Define para onde ir após a exclusão bem-sucedida. """
        company_id = self.kwargs.get('company_id')
        return reverse_lazy('core:chart_of_accounts_list', kwargs={'company_id': company_id})
    
    def get_context_data(self, **kwargs):
        """ Adiciona a 'company' ao contexto para o link 'Cancelar' funcionar. """
        context = super().get_context_data(**kwargs)
        context['company'] = self.get_object().company
        return context

@login_required
def company_list(request):
    # Busca no banco todas as empresas que estão associadas ao usuário logado
    companies = Company.objects.filter(users=request.user)
    context = {
        'companies': companies
    }
    return render(request, 'core/company_list.html', context)

@login_required
def chart_of_accounts_list(request, company_id):
    # Busca a empresa ou retorna um erro 404 se não existir.
    # A verificação 'users=request.user' é uma checagem de segurança CRUCIAL
    # para garantir que o usuário só acesse empresas que ele gerencia.
    company = get_object_or_404(Company, pk=company_id, users=request.user)

    # Lógica para processar o formulário quando ele é enviado (método POST)
    if request.method == 'POST':
        # Passamos a 'company' para o formulário, para a lógica de filtro que criamos
        form = ChartOfAccountsForm(request.POST, company=company)
        if form.is_valid():
            # Cria o objeto mas não salva no banco ainda
            new_account = form.save(commit=False)
            # Associa a empresa correta
            new_account.company = company
            # Agora sim, salva no banco
            new_account.save()
            # Redireciona para a mesma página, mostrando a lista atualizada
            return redirect('core:chart_of_accounts_list', company_id=company.id)
    else:
        # Se for um acesso normal (método GET), apenas cria um formulário vazio
        form = ChartOfAccountsForm(company=company)

    # Busca todas as contas associadas a esta empresa para listar na tela
    accounts = ChartOfAccounts.objects.filter(company=company).order_by('code')
    
    context = {
        'company': company,
        'accounts': accounts,
        'form': form,
    }
    return render(request, 'core/chart_of_accounts_list.html', context)


@login_required
def set_active_company(request, company_id):
    # Checagem de segurança para garantir que o usuário tem acesso a esta empresa
    company = get_object_or_404(Company, pk=company_id, users=request.user)

    # Aqui está a mágica: guardamos o ID da empresa na sessão do usuário
    request.session['active_company_id'] = company.id

    # Redirecionamos o usuário para a página do plano de contas da empresa recém-ativada
    return redirect('core:chart_of_accounts_list', company_id=company.id)



@login_required
def transaction_list(request):
    # Busca a empresa ativa diretamente da sessão
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        messages.error(request, "Por favor, selecione uma empresa primeiro.")
        return redirect('core:company_list')
    
    active_company = get_object_or_404(Company, pk=active_company_id, users=request.user)

    # Formulário de Adição (POST)
    if request.method == 'POST':
        form = TransactionForm(request.POST, company=active_company)
        if form.is_valid():
            new_transaction = form.save(commit=False)
            new_transaction.company = active_company
            new_transaction.save()
            messages.success(request, "Lançamento salvo com sucesso!")
            return redirect('core:transaction_list')
    else:
        form = TransactionForm(company=active_company)

    # Lógica de Filtro (GET)
    transactions_list = Transaction.objects.filter(company=active_company).order_by('-date', '-pk')
    filter_form = TransactionFilterForm(request.GET, company=active_company)

    if filter_form.is_valid():
        start_date = filter_form.cleaned_data.get('start_date')
        end_date = filter_form.cleaned_data.get('end_date')
        account = filter_form.cleaned_data.get('account')

        if start_date:
            transactions_list = transactions_list.filter(date__gte=start_date)
        if end_date:
            transactions_list = transactions_list.filter(date__lte=end_date)
        if account:
            transactions_list = transactions_list.filter(account=account)

    # Lógica de Paginação
    paginator = Paginator(transactions_list, 15) # Mostra 15 lançamentos por página
    page_number = request.GET.get('page')
    transactions = paginator.get_page(page_number)

    # Prepara os parâmetros GET para serem usados nos links de paginação,
    # garantindo que os filtros sejam mantidos.
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']

    # Dados para o filtro de conta do formulário de adição
    all_accounts = ChartOfAccounts.objects.filter(company=active_company).values('pk', 'code', 'name', 'account_type')
    all_accounts_json_str = json.dumps(list(all_accounts))

    context = {
        'transactions': transactions,
        'form': form,
        'filter_form': filter_form,
        'all_accounts_json_str': all_accounts_json_str,
    }
    return render(request, 'core/transaction_list.html', context)


class TransactionUpdateView(LoginRequiredMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'core/transaction_form.html' # Vamos reutilizar um template de formulário

    def get_queryset(self):
        """ Garante que o usuário só pode editar lançamentos da empresa ativa na sessão. """
        active_company_id = self.request.session.get('active_company_id')
        if not active_company_id:
            return Transaction.objects.none() # Não retorna nada se não houver empresa ativa

        # Filtra as transações pela empresa ativa
        active_company = get_object_or_404(Company, pk=active_company_id, users=self.request.user)
        return Transaction.objects.filter(company=active_company)

    def get_form_kwargs(self):
        """ Passa a empresa ativa para o formulário. """
        kwargs = super().get_form_kwargs()
        # CORREÇÃO: Busca a empresa da sessão, não do request.
        active_company_id = self.request.session.get('active_company_id')
        if active_company_id:
            # Encontramos a empresa para passar ao formulário,
            # para que ele possa filtrar o campo 'account' corretamente.
            kwargs['company'] = get_object_or_404(Company, pk=active_company_id)
        return kwargs

    def get_context_data(self, **kwargs):
        """ Adiciona um título dinâmico ao contexto. """
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Editar Lançamento'
        return context

    def get_success_url(self):
        """ Redireciona para a lista de lançamentos após o sucesso. """
        return reverse_lazy('core:transaction_list')


class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    model = Transaction
    template_name = 'core/transaction_confirm_delete.html'

    def get_queryset(self):
        """ Mesma lógica de segurança da view de Update. """
        active_company_id = self.request.session.get('active_company_id')
        if not active_company_id:
            return Transaction.objects.none()

        active_company = get_object_or_404(Company, pk=active_company_id, users=self.request.user)
        return Transaction.objects.filter(company=active_company)

    def get_success_url(self):
        """ Redireciona para a lista de lançamentos após o sucesso. """
        messages.success(self.request, "Lançamento excluído com sucesso.")
        return reverse_lazy('core:transaction_list')

class CompanyCreateView(LoginRequiredMixin, CreateView):
    model = Company
    form_class = CompanyForm
    template_name = 'core/company_form.html'
    success_url = reverse_lazy('core:company_list') # Para onde ir após criar

    def form_valid(self, form):
        """
        Este método é chamado quando o formulário é válido.
        Aqui nós associamos o usuário logado à nova empresa.
        """
        # Salva o objeto da empresa primeiro
        response = super().form_valid(form)
        # Adiciona o usuário atual à relação ManyToMany
        self.object.users.add(self.request.user)
        messages.success(self.request, "Empresa criada com sucesso!")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Adicionar Nova Empresa'
        return context


class CompanyUpdateView(LoginRequiredMixin, UpdateView):
    model = Company
    form_class = CompanyForm
    template_name = 'core/company_form.html'
    success_url = reverse_lazy('core:company_list')

    def get_queryset(self):
        """ Garante que um usuário só pode editar as empresas que ele gerencia. """
        return self.request.user.companies.all()

    def form_valid(self, form):
        messages.success(self.request, "Empresa atualizada com sucesso!")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Editar Empresa'
        return context


class CompanyDeleteView(LoginRequiredMixin, DeleteView):
    model = Company
    template_name = 'core/company_confirm_delete.html'
    success_url = reverse_lazy('core:company_list')

    def get_queryset(self):
        """ Garante que um usuário só pode excluir as empresas que ele gerencia. """
        return self.request.user.companies.all()

    def form_valid(self, form):
        messages.success(self.request, f"A empresa '{self.object.name}' foi excluída com sucesso.")
        return super().form_valid(form)

@login_required
def home_redirect(request):
    # Verificamos se há uma empresa ativa na sessão
    active_company_id = request.session.get('active_company_id')

    if active_company_id:
        # Se houver, redireciona para o dashboard daquela empresa
        return redirect('core:dashboard', company_id=active_company_id)
    else:
        # Se não houver, redireciona para a lista de empresas para o usuário escolher uma
        return redirect('core:company_list')


@login_required
def dashboard_dispatcher(request, company_id):
    """
    Esta view atua como um "roteador". Ela busca a empresa,
    verifica seu tipo de gestão e chama a view de dashboard apropriada.
    """
    company = get_object_or_404(Company, pk=company_id, users=request.user)

    if company.management_type == 'Pública':
        # Chama a view focada em orçamento
        return dashboard_orcamento(request, company)
    else:  # 'Particular'
        # Chama a view focada em lucratividade
        return dashboard_lucratividade(request, company)


@login_required
def dashboard_lucratividade(request, company):
    """
    Dashboard focado em Gestão Particular (Lucratividade).
    """
    today = date.today()
    start_date_str = request.GET.get('start_date', today.replace(day=1).strftime('%Y-%m-%d'))
    end_date_str = request.GET.get('end_date',
                                   (today.replace(day=calendar.monthrange(today.year, today.month)[1])).strftime(
                                       '%Y-%m-%d'))
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    transactions = Transaction.objects.filter(
        company=company,
        date__range=[start_date, end_date]
    )

    total_revenue = transactions.filter(account__account_type='R').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = transactions.filter(account__account_type__in=['D', 'E']).aggregate(Sum('amount'))['amount__sum'] or 0
    net_result = total_revenue - total_expenses

    folha_total_lc = Transaction.objects.filter(
        company=company, date__range=[start_date, end_date], account__code__startswith="2.01.1.01"
    ).aggregate(total=Coalesce(Sum('amount'), Value(Decimal('0.00'))))['total']

    percentual_folha_lc = (folha_total_lc / total_expenses * 100) if total_expenses > 0 else 0

    rec_serv_terceiros = Transaction.objects.filter(
        company=company, date__range=[start_date, end_date], account__code__startswith="1.01.01"
    ).aggregate(total=Coalesce(Sum('amount'), Value(Decimal('0.00'))))['total']

    percentual_rec_serv_terceiros = (rec_serv_terceiros / total_revenue * 100) if total_revenue > 0 else 0

    rec_convenios = Transaction.objects.filter(
        company=company, date__range=[start_date, end_date], account__code__startswith="1.01.02"
    ).aggregate(total=Coalesce(Sum('amount'), Value(Decimal('0.00'))))['total']

    percentual_rec_convenios = (rec_convenios / total_revenue * 100) if total_revenue > 0 else 0

    rec_particulares = Transaction.objects.filter(
        company=company, date__range=[start_date, end_date], account__code__startswith="1.01.03"
    ).aggregate(total=Coalesce(Sum('amount'), Value(Decimal('0.00'))))['total']

    percentual_rec_particulares = (rec_particulares / total_revenue * 100) if total_revenue > 0 else 0

    rec_conv_desconto = Transaction.objects.filter(
        company=company, date__range=[start_date, end_date], account__code__startswith="1.01.04"
    ).aggregate(total=Coalesce(Sum('amount'), Value(Decimal('0.00'))))['total']

    percentual_rec_conv_desconto = (rec_conv_desconto / total_revenue * 100) if total_revenue > 0 else 0

    rec_fundo_programa_emenda = Transaction.objects.filter(
        company=company, date__range=[start_date, end_date], account__code__startswith="1.01.05"
    ).aggregate(total=Coalesce(Sum('amount'), Value(Decimal('0.00'))))['total']

    percentual_rec_fundo_programa_emenda = (rec_fundo_programa_emenda / total_revenue * 100) if total_revenue > 0 else 0

    rec_outras_receitas = Transaction.objects.filter(
        company=company, date__range=[start_date, end_date], account__code__startswith="1.01.06"
    ).aggregate(total=Coalesce(Sum('amount'), Value(Decimal('0.00'))))['total']

    percentual_rec_outras_receitas = (rec_outras_receitas / total_revenue * 100) if total_revenue > 0 else 0

    context = {
        'company': company,
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'net_result': net_result,
        'start_date_str': start_date_str,
        'end_date_str': end_date_str,
        'percentual_folha_lc': percentual_folha_lc,
        'percentual_rec_serv_terceiros': percentual_rec_serv_terceiros,
        'percentual_rec_convenios': percentual_rec_convenios,
        'percentual_rec_particulares': percentual_rec_particulares,
        'percentual_rec_conv_desconto': percentual_rec_conv_desconto,
        'percentual_rec_fundo_programa_emenda': percentual_rec_fundo_programa_emenda,
        'percentual_rec_outras_receitas': percentual_rec_outras_receitas,
    }

    # Renderiza o template específico de lucratividade
    return render(request, 'core/dashboard_lucratividade.html', context)


@login_required
def dashboard_orcamento(request, company):
    """
    Dashboard focado em Gestão Pública (Orçamento vs. Realizado).
    """
    # --- Lógica do Filtro de Data
    today = date.today()
    start_date_str = request.GET.get('start_date', today.replace(day=1).strftime('%Y-%m-%d'))
    end_date_str = request.GET.get('end_date', (today.replace(day=calendar.monthrange(today.year, today.month)[1])).strftime('%Y-%m-%d'))
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    # 1. Total Realizado (Gastos): Busca APENAS as despesas no período
    expense_transactions = Transaction.objects.filter(
        company=company, 
        date__range=[start_date, end_date], 
        account__account_type='D'
    )
    total_realizado = expense_transactions.aggregate(
        total=Coalesce(Sum('amount'), Value(Decimal('0.00')))
    )['total']

    total_expenses = expense_transactions.filter(account__account_type='D').aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')

    # 2. Total Orçado: Soma das RECEITAS orçadas, proporcional ao período
    orcamento_anual_receitas = Budget.objects.filter(
        account__company=company,
        year=start_date.year,
        account__account_type='R' 
    ).aggregate(total=Coalesce(Sum('annual_amount'), Value(Decimal('0.00'))))['total']

    # Calcula a proporção do orçamento de receita para o período selecionado
    dias_no_ano = Decimal(366 if calendar.isleap(start_date.year) else 365)
    dias_no_periodo = Decimal((end_date - start_date).days + 1)
    
    total_orcado_periodo = ((orcamento_anual_receitas * 12) / dias_no_ano) * dias_no_periodo
    
    # 3. Percentual de Execução (Gasto Realizado vs. Orçamento de Receita)
    percentual_executado = 0
    if total_orcado_periodo > 0:
        percentual_executado = (total_realizado / total_orcado_periodo) * 100

     # Indicadores Adicionais
    glosas_total = Transaction.objects.filter(
        company=company, date__range=[start_date, end_date], account__code__startswith="1.03"
    ).aggregate(total=Coalesce(Sum('amount'), Value(Decimal('0.00'))))['total']

    repasse_total = Transaction.objects.filter(
        company=company, date__range=[start_date, end_date], account__code__startswith="1.01"
    ).aggregate(total=Coalesce(Sum('amount'), Value(Decimal('0.00'))))['total']

    percentual_glosa = (glosas_total / repasse_total * 100) if repasse_total > 0 else 0

    folha_total = Transaction.objects.filter(
        company=company, date__range=[start_date, end_date], account__code__startswith="2.01.01"
    ).aggregate(total=Coalesce(Sum('amount'), Value(Decimal('0.00'))))['total']

    percentual_folha = (folha_total / total_realizado * 100) if total_realizado > 0 else 0

    receitas_extra = Transaction.objects.filter(
        company=company, date__range=[start_date, end_date], account__code="1.04"
    ).aggregate(total=Coalesce(Sum('amount'), Value(Decimal('0.00'))))['total']

    servicos_terceiros = Transaction.objects.filter(
        company=company, date__range=[start_date, end_date], account__code__startswith="2.01.03"
    ).aggregate(total=Coalesce(Sum('amount'), Value(Decimal('0.00'))))['total']

    percentual_servicos_terceiros = (servicos_terceiros / total_realizado * 100) if total_realizado > 0 else 0

    materiais = Transaction.objects.filter(
        company=company, date__range=[start_date, end_date], account__code__startswith="2.01.02"
    ).aggregate(total=Coalesce(Sum('amount'), Value(Decimal('0.00'))))['total']

    percentual_materiais = (materiais / total_realizado * 100) if total_realizado > 0 else 0

    apoio_gestao = Transaction.objects.filter(
        company=company, date__range=[start_date, end_date], account__code__startswith="2.01.04"
    ).aggregate(total=Coalesce(Sum('amount'), Value(Decimal('0.00'))))['total']

    percentual_apoio_gestao = (apoio_gestao / total_realizado * 100) if total_realizado > 0 else 0

    outras_despesas = Transaction.objects.filter(
        company=company, date__range=[start_date, end_date], account__code__startswith="2.01.05"
    ).aggregate(total=Coalesce(Sum('amount'), Value(Decimal('0.00'))))['total']

    percentual_outras_despesas = (outras_despesas / total_realizado * 100) if total_realizado > 0 else 0

    despesas_administrativas = Transaction.objects.filter(
        company=company, date__range=[start_date, end_date], account__code__startswith="2.01.06"
    ).aggregate(total=Coalesce(Sum('amount'), Value(Decimal('0.00'))))['total']

    percentual_despesas_administrativas = (despesas_administrativas / total_realizado * 100) if total_realizado > 0 else 0

    # Lógica de cor da barra de progresso (continua igual)
    progress_color = 'success'
    if percentual_executado > 95:
        progress_color = 'danger'
    elif percentual_executado > 80:
        progress_color = 'warning'

    context = {
        'company': company,
        'start_date_str': start_date_str,
        'end_date_str': end_date_str,
        'total_orcado_periodo': total_orcado_periodo,
        'total_realizado': total_realizado,
        'percentual_executado_display': percentual_executado,
        'percentual_executado_raw': f'{percentual_executado:.2f}'.replace(',', '.'),
        'progress_color': progress_color,
        'percentual_glosa': percentual_glosa,
        'percentual_folha': percentual_folha,
        'receitas_extra': receitas_extra,
        'servicos_terceiros': servicos_terceiros,
        'percentual_servicos_terceiros': percentual_servicos_terceiros,
        'materiais': materiais,
        'percentual_materiais': percentual_materiais,
        'apoio_gestao': apoio_gestao,
        'percentual_apoio_gestao': percentual_apoio_gestao,
        'outras_despesas': outras_despesas,
        'percentual_outras_despesas': percentual_outras_despesas,
        'despesas_administrativas': despesas_administrativas,
        'percentual_despesas_administrativas': percentual_despesas_administrativas,
    }
    return render(request, 'core/dashboard_orcamento.html', context)

@login_required
def expense_chart_data(request):
    # Pega a empresa ativa da sessão
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return JsonResponse({'error': 'Nenhuma empresa ativa'}, status=404)

    company = get_object_or_404(Company, pk=active_company_id, users=request.user)

    today = date.today()
    start_date_str = request.GET.get('start_date', today.replace(day=1).strftime('%Y-%m-%d'))
    end_date_str = request.GET.get('end_date', (today.replace(day=calendar.monthrange(today.year, today.month)[1])).strftime('%Y-%m-%d'))

    # Filtra as despesas para o PERÍODO SELECIONADO
    expenses = Transaction.objects.filter(
        company=company,
        account__account_type__in=['D', 'E'], 
        date__range=[start_date_str, end_date_str]
    )

    # O resto do código continua igual
    category_expenses = expenses.values(
        'account__parent_account__name'
    ).annotate(
        total=Coalesce(Sum('amount'), Value(0.0), output_field=DecimalField())
    ).order_by('-total')

    labels = [item['account__parent_account__name'] or 'Sem Categoria' for item in category_expenses]
    data = [float(item['total']) for item in category_expenses]

    return JsonResponse({'labels': labels, 'data': data})


@login_required
def revenue_expense_summary_data(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return JsonResponse({'error': 'Nenhuma empresa ativa'}, status=404)

    company = get_object_or_404(Company, pk=active_company_id, users=request.user)

    # --- INÍCIO DA LÓGICA DE FILTRO DE DATA ---
    today = date.today()
    start_date_str = request.GET.get('start_date', today.replace(day=1).strftime('%Y-%m-%d'))
    end_date_str = request.GET.get('end_date', (today.replace(day=calendar.monthrange(today.year, today.month)[1])).strftime('%Y-%m-%d'))

    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    # --- FIM DA LÓGICA DE FILTRO DE DATA ---

    labels = []
    revenue_data = []
    expense_data = []

    # Itera mês a mês dentro do período selecionado pelo usuário
    current_date = start_date
    while current_date <= end_date:
        target_month = current_date.month
        target_year = current_date.year

        labels.append(current_date.strftime("%b/%Y"))

        # Filtra os lançamentos para o mês e ano da iteração
        transactions = Transaction.objects.filter(
            company=company,
            date__year=target_year,
            date__month=target_month
        )

        # Calcula os totais para aquele mês
        revenue = transactions.filter(account__account_type='R').aggregate(
            total=Coalesce(Sum('amount'), Value(0.0), output_field=DecimalField())
        )['total']

        expense = transactions.filter(account__account_type__in=['D', 'E']).aggregate(
            total=Coalesce(Sum('amount'), Value(0.0), output_field=DecimalField())
        )['total']

        revenue_data.append(float(revenue))
        expense_data.append(float(expense))

        # Avança para o primeiro dia do próximo mês
        current_date = (current_date.replace(day=1) + relativedelta(months=1))

    return JsonResponse({
        'labels': labels,
        'revenue_data': revenue_data,
        'expense_data': expense_data,
    })


@login_required
def import_chart_of_accounts(request, company_id):
    company = get_object_or_404(Company, pk=company_id, users=request.user)
    
    if request.method == 'POST':
        form = CSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'Este não é um arquivo CSV válido.')
                return redirect('core:import_chart_of_accounts', company_id=company.id)

            # Decodifica o arquivo da forma mais robusta possível
            try:
                data_set = csv_file.read().decode('utf-8-sig')
            except UnicodeDecodeError:
                csv_file.seek(0)
                data_set = csv_file.read().decode('latin-1')
            
            io_string = io.StringIO(data_set)

            # Detecção automática do separador (vírgula ou ponto e vírgula)
            try:
                dialect = csv.Sniffer().sniff(io_string.readline(), delimiters=';,')
                io_string.seek(0) # Volta para o início do arquivo
                reader = csv.DictReader(io_string, dialect=dialect)
                # Verifica se as colunas essenciais existem no cabeçalho
                if not all(key in reader.fieldnames for key in ['code', 'name', 'account_type']):
                    raise csv.Error("O cabeçalho do CSV é inválido. Faltam colunas obrigatórias.")
            except csv.Error as e:
                messages.error(request, f"Erro ao processar o arquivo CSV: {e}. Verifique o cabeçalho e o separador.")
                return redirect('core:import_chart_of_accounts', company_id=company.id)
            
            parent_accounts_map = {}
            child_accounts_rows = []
            success_count = 0
            error_count = 0

            # --- PRIMEIRA PASSAGEM: Criar contas principais (sem pai) ---
            for row in reader:
                # Se a coluna 'parent_code' estiver vazia ou não existir, é uma conta principal
                if not row.get('parent_code'):
                    try:
                        account, created = ChartOfAccounts.objects.get_or_create(
                            company=company,
                            code=row['code'],
                            defaults={
                                'name': row['name'],
                                'account_type': row['account_type'].upper()
                            }
                        )
                        if created:
                            success_count += 1
                        # Guarda a conta criada no mapa para referência futura
                        parent_accounts_map[account.code] = account
                    except Exception as e:
                        error_count += 1
                        messages.warning(request, f"Erro ao importar a conta {row.get('code', 'desconhecida')}: {e}")
                else:
                    # Se tiver um pai, guarda a linha para a segunda passagem
                    child_accounts_rows.append(row)

            # --- SEGUNDA PASSAGEM: Criar contas-filhas ---
            for row in child_accounts_rows:
                try:
                    # Busca a conta pai no mapa que criamos
                    parent_account = parent_accounts_map.get(row['parent_code'])
                    if parent_account:
                        account, created = ChartOfAccounts.objects.get_or_create(
                            company=company,
                            code=row['code'],
                            defaults={
                                'name': row['name'],
                                'account_type': row['account_type'].upper(),
                                'parent_account': parent_account
                            }
                        )
                        if created:
                            success_count += 1
                        # Adiciona a conta filha recém-criada ao mapa, caso ela também seja pai de outra
                        parent_accounts_map[account.code] = account
                    else:
                        # Se não encontrou o pai, registra um erro
                        error_count += 1
                        messages.warning(request, f"Não foi possível criar a conta '{row.get('code')}' pois a conta-pai '{row.get('parent_code')}' não foi encontrada ou criada na primeira passagem.")
                except Exception as e:
                    error_count += 1
                    messages.warning(request, f"Erro ao importar a conta {row.get('code', 'desconhecida')}: {e}")

            # Mensagem final para o usuário
            if success_count > 0:
                messages.success(request, f"{success_count} contas foram importadas ou atualizadas com sucesso.")
            if error_count > 0:
                 messages.error(request, f"Falha ao importar {error_count} contas. Verifique as mensagens de aviso.")
            
            return redirect('core:chart_of_accounts_list', company_id=company.id)

    else: # Se o método for GET
        form = CSVImportForm()

    context = {
        'form': form,
        'company': company,
    }
    return render(request, 'core/import_chart_of_accounts.html', context)


def get_account_total(account, transactions):
    """
    Função auxiliar recursiva.
    Calcula o total de um conta somando seus próprios lançamentos
    e os totais de todas as suas contas-filhas.
    """
    total = transactions.filter(account=account).aggregate(
        total=Coalesce(Sum('amount'), Value(0.0), output_field=DecimalField())
    )['total']

    # Pega todas as subcontas desta conta
    sub_accounts = account.sub_accounts.all()
    for sub_account in sub_accounts:
        # Chama a si mesma para cada subconta e soma o resultado
        total += get_account_total(sub_account, transactions)

    return total

@login_required
def dre_report(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        messages.error(request, "Por favor, selecione uma empresa primeiro.")
        return redirect('core:company_list')
    active_company = get_object_or_404(Company, pk=active_company_id, users=request.user)
    
    # Reutilizamos a mesma lógica de filtro de data do dashboard
    today = date.today()
    start_date_str = request.GET.get('start_date', today.replace(day=1).strftime('%Y-%m-%d'))
    end_date_str = request.GET.get('end_date', (today.replace(day=calendar.monthrange(today.year, today.month)[1])).strftime('%Y-%m-%d'))
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    # Filtra todas as transações da empresa para o período selecionado
    transactions = Transaction.objects.filter(
        company=active_company,
        date__range=[start_date, end_date]
    )

    # Buscamos as contas-raiz do plano de contas (Receitas e Despesas)
    root_revenue_account = ChartOfAccounts.objects.get(company=active_company, code='1')
    root_expense_account = ChartOfAccounts.objects.get(company=active_company, code='2')

    # Calculamos os totais usando nossa função recursiva
    total_revenue = get_account_total(root_revenue_account, transactions)
    total_expense = get_account_total(root_expense_account, transactions)
    net_result = total_revenue - total_expense

    # Montamos uma estrutura de dados para o template
    dre_data = {
        'revenue_lines': [],
        'expense_lines': [],
    }

    # Função para construir a estrutura de linhas para o template
    def build_structure(account, level=0):
        total = get_account_total(account, transactions)
        line_data = {'account': account, 'total': total, 'level': level}

        if account.account_type == 'R':
            dre_data['revenue_lines'].append(line_data)
        else:
            dre_data['expense_lines'].append(line_data)

        for sub_account in account.sub_accounts.all().order_by('code'):
            build_structure(sub_account, level + 1)

    # Construímos a estrutura começando pelas contas-raiz
    build_structure(root_revenue_account)
    build_structure(root_expense_account)

    context = {
        'company': active_company,
        'start_date_str': start_date_str,
        'end_date_str': end_date_str,
        'dre_data': dre_data,
        'total_revenue': total_revenue,
        'total_expense': total_expense,
        'net_result': net_result,
    }
    return render(request, 'core/dre_report.html', context)


@login_required
def dre_report_pdf(request):
    # Esta view usa EXATAMENTE a mesma lógica de cálculo da dre_report

    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        messages.error(request, "Nenhuma empresa ativa.")
        return redirect('core:company_list')

    active_company = get_object_or_404(Company, pk=active_company_id, users=request.user)

    today = date.today()
    start_date_str = request.GET.get('start_date', today.replace(day=1).strftime('%Y-%m-%d'))
    end_date_str = request.GET.get('end_date', (today.replace(day=calendar.monthrange(today.year, today.month)[1])).strftime('%Y-%m-%d'))
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    transactions = Transaction.objects.filter(company=active_company, date__range=[start_date, end_date])

    try:
        root_revenue_account = ChartOfAccounts.objects.get(company=active_company, code='1')
        root_expense_account = ChartOfAccounts.objects.get(company=active_company, code='2')
    except ChartOfAccounts.DoesNotExist:
        messages.error(request, "Plano de contas base não encontrado.")
        return redirect('core:chart_of_accounts_list', company_id=active_company.id)

    total_revenue = get_account_total(root_revenue_account, transactions)
    total_expense = get_account_total(root_expense_account, transactions)
    net_result = total_revenue - total_expense
    dre_data = {'revenue_lines': [], 'expense_lines': []}

    def build_structure(account, level=0):
        total = get_account_total(account, transactions)
        line_data = {'account': account, 'total': total, 'level': level}
        if account.account_type == 'R': dre_data['revenue_lines'].append(line_data)
        else: dre_data['expense_lines'].append(line_data)
        for sub_account in account.sub_accounts.all().order_by('code'): build_structure(sub_account, level + 1)

    build_structure(root_revenue_account)
    build_structure(root_expense_account)

    context = {
        'company': active_company,
        'start_date_str': start_date.strftime('%d/%m/%Y'),
        'end_date_str': end_date.strftime('%d/%m/%Y'),
        'dre_data': dre_data,
        'total_revenue': total_revenue,
        'total_expense': total_expense,
        'net_result': net_result,
    }

    # 1. Renderiza nosso template PDF para uma string HTML
    html_string = render_to_string('core/dre_report_pdf.html', context)

    # 2. Cria o objeto WeasyPrint a partir do HTML
    html = HTML(string=html_string)

    # 3. Gera o PDF em memória
    pdf = html.write_pdf()

    # 4. Retorna o PDF como um arquivo para download
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="DRE_{active_company.name}.pdf"'
    return response


@login_required
def budget_dashboard(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        messages.error(request, "Por favor, selecione uma empresa primeiro.")
        return redirect('core:company_list')
    active_company = get_object_or_404(Company, pk=active_company_id, users=request.user)

    now_year = datetime.now().year
    
    # Busca anos com transações realizadas
    transaction_years = Transaction.objects.filter(company=active_company).dates('date', 'year')
    year_list = set([d.year for d in transaction_years])
    
    # Busca anos com orçamento definido (caso tenha orçamento mas não tenha transação ainda)
    budget_years = Budget.objects.filter(account__company=active_company).values_list('year', flat=True).distinct()
    year_list.update(budget_years)
    
    # Garante que o ano atual esteja na lista, mesmo sem dados
    year_list.add(now_year)
    
    # Ordena decrescente (2025, 2024, 2023...)
    available_years = sorted(list(year_list), reverse=True)

    # Pega o ano da URL (?year=2023) ou usa o ano atual
    selected_year_get = request.GET.get('year')
    try:
        current_year = int(selected_year_get) if selected_year_get else now_year
    except ValueError:
        current_year = now_year

    accounts = ChartOfAccounts.objects.filter(company=active_company).order_by('code')
    budgets = Budget.objects.filter(account__company=active_company, year=current_year)
    transactions = Transaction.objects.filter(company=active_company, date__year=current_year)

    monthly_totals = {}
    for month in range(1, 13):
        month_total = transactions.filter(date__month=month).values('account').annotate(total=Sum('amount'))
        for item in month_total:
            monthly_totals[(item['account'], month)] = item['total']

    budget_map = {b.account.id: b.annual_amount for b in budgets}

    report_data = []
    account_map = {acc.id: {'children': [], 'data': {
        'account': acc,
        'annual_budget': budget_map.get(acc.id, Decimal(0)),
        'monthly_actuals': [monthly_totals.get((acc.id, m), Decimal(0)) for m in range(1, 13)]
    }} for acc in accounts}

    for acc in accounts:
        if acc.parent_account_id and acc.parent_account_id in account_map:
            account_map[acc.parent_account_id]['children'].append(account_map[acc.id])

    def aggregate_totals(node):
        for child_node in node['children']:
            aggregate_totals(child_node)
            node['data']['annual_budget'] += child_node['data']['annual_budget']
            for i in range(12):
                node['data']['monthly_actuals'][i] += child_node['data']['monthly_actuals'][i]
    
    for acc_id, node in account_map.items():
        if node['data']['account'].parent_account_id is None:
            aggregate_totals(node)

    def build_report_list(node, level=0):
        node['data']['level'] = level
        report_data.append(node['data'])
        for child_node in sorted(node['children'], key=lambda x: x['data']['account'].code):
            build_report_list(child_node, level + 1)

    for acc_id, node in account_map.items():
        if node['data']['account'].parent_account_id is None:
            build_report_list(node)

    for row in report_data:
        monthly_budget = row['annual_budget'] if row['annual_budget'] > 0 else 0
        row['monthly_data'] = []

        for i in range(12):
            actual = row['monthly_actuals'][i]

            # --- Lógica de Cores para o 'Realizado' ---
            realizado_css_class = ""
            is_over_budget = monthly_budget > 0 and actual > monthly_budget

            if row['account'].account_type in ['D', 'E']:
                if is_over_budget:
                    realizado_css_class = "bg-danger text-white"  # RUIM: Acima do orçamento
                elif actual > 0:
                    realizado_css_class = "bg-primary text-white" # BOM: Dentro do orçamento

            elif row['account'].account_type == 'R': # Se for Receita
                if is_over_budget:
                    realizado_css_class = "bg-primary text-white" # BOM: Acima do orçamento (AZUL)
                elif actual < monthly_budget:
                    realizado_css_class = "bg-danger text-white" # RUIM: Abaixo do orçamento (VERMELHO)

            # --- Lógica de Cores para a 'Variação' ---
            variation = Decimal(0)
            if i > 0:
                previous_actual = row['monthly_actuals'][i-1]
                if previous_actual != 0:
                    variation = ((actual - previous_actual) / previous_actual) * 100

            variacao_css_class = ""
            if variation == 0:
                variacao_css_class = "badge bg-secondary" # NEUTRO
            elif row['account'].account_type == 'R': # Se for Receita
                variacao_css_class = "badge bg-success" if variation > 0 else "badge bg-danger" # Aumento é bom, queda é ruim
            elif row['account'].account_type == 'D' or 'E': # Se for Despesa
                variacao_css_class = "badge bg-danger" if variation > 0 else "badge bg-success" # Aumento é ruim, queda é bom
            

            row['monthly_data'].append({
                'actual': actual,
                'variation': variation,
                'realizado_css_class': realizado_css_class,
                'variacao_css_class': variacao_css_class,
            })

    summary_data = {
        'revenue': {'monthly_actuals': [Decimal(0)]*12, 'monthly_variations': [Decimal(0)]*12},
        'expense': {'monthly_actuals': [Decimal(0)]*12, 'monthly_variations': [Decimal(0)]*12},
        'net_result': {'monthly_actuals': [Decimal(0)]*12, 'monthly_variations': [Decimal(0)]*12},
    }

    # Extrai os dados das contas-raiz que já foram calculados
    for row in report_data:
        if row['account'].code == '1': # Assumindo que 1 é Receita
            summary_data['revenue']['monthly_actuals'] = row['monthly_actuals']
            summary_data['revenue']['monthly_variations'] = [m['variation'] for m in row['monthly_data']]
        elif row['account'].code == '2': # Assumindo que 2 é Despesa
            summary_data['expense']['monthly_actuals'] = row['monthly_actuals']
            summary_data['expense']['monthly_variations'] = [m['variation'] for m in row['monthly_data']]

    # Calcula o Resultado Líquido e sua variação
    for i in range(12):
        rev = summary_data['revenue']['monthly_actuals'][i]
        exp = summary_data['expense']['monthly_actuals'][i]
        summary_data['net_result']['monthly_actuals'][i] = rev - exp

        if i > 0:
            prev_rev = summary_data['revenue']['monthly_actuals'][i-1]
            prev_exp = summary_data['expense']['monthly_actuals'][i-1]
            previous_net_result = prev_rev - prev_exp
            current_net_result = rev - exp
            if previous_net_result != 0:
                summary_data['net_result']['monthly_variations'][i] = ((current_net_result - previous_net_result) / abs(previous_net_result)) * 100


    context = {
        'company': active_company, 
        'year': current_year,
        'available_years': available_years, 
        'report_data': report_data,
        'months': ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'],
        'summary_data': summary_data,
    }
    return render(request, 'core/budget_dashboard.html', context)


@login_required
def budget_deviations_chart_data(request):
    """ API de dados para o gráfico de Maiores Desvios Orçamentários. """
    active_company_id = request.session.get('active_company_id')
    company = get_object_or_404(Company, pk=active_company_id, users=request.user)

    today = date.today()
    start_date_str = request.GET.get('start_date', today.replace(day=1).strftime('%Y-%m-%d'))
    end_date_str = request.GET.get('end_date', (today.replace(day=calendar.monthrange(today.year, today.month)[1])).strftime('%Y-%m-%d'))
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    # Pega todas as contas de despesa "folha" (que não têm filhas)
    leaf_expense_accounts = ChartOfAccounts.objects.filter(company=company, account_type='D', sub_accounts__isnull=True)

    deviations = []
    dias_no_ano = Decimal(366 if calendar.isleap(start_date.year) else 365)
    dias_no_periodo = Decimal((end_date - start_date).days + 1)

    for account in leaf_expense_accounts:
        try:
            budget = Budget.objects.get(account=account, year=start_date.year)
            orcado_periodo = (budget.annual_amount / dias_no_ano) * dias_no_periodo
        except Budget.DoesNotExist:
            orcado_periodo = Decimal(0)

        realizado = Transaction.objects.filter(
            account=account, date__range=[start_date, end_date]
        ).aggregate(total=Coalesce(Sum('amount'), Value(Decimal(0))))['total']

        if orcado_periodo > 0 or realizado > 0:
            desvio = realizado - orcado_periodo
            deviations.append({'name': account.name, 'desvio': float(desvio)})

    # Ordena pelos maiores desvios (positivos ou negativos)
    deviations.sort(key=lambda x: abs(x['desvio']), reverse=True)

    # Pega os top 10 maiores desvios
    top_deviations = deviations[:10]

    labels = [item['name'] for item in top_deviations]
    data = [item['desvio'] for item in top_deviations]
    colors = ['#dc3545' if v > 0 else '#198754' for v in data] # Vermelho para estouro, Verde para economia

    return JsonResponse({'labels': labels, 'data': data, 'colors': colors})


@login_required
def budget_vs_actual_timeline_data(request):
    """ API de dados para o gráfico de Linha Dupla (Orçado vs. Realizado). """
    active_company_id = request.session.get('active_company_id')
    company = get_object_or_404(Company, pk=active_company_id, users=request.user)

    # Calcula o orçamento total anual para despesas
    orcamento_anual_total = Budget.objects.filter(
        account__company=company, year=datetime.now().year, account__account_type='R'
    ).aggregate(total=Coalesce(Sum('annual_amount'), Value(Decimal(0))))['total']

    orcado_mensal = orcamento_anual_total

    labels = []
    budget_data = []
    actual_data = []

    # Itera pelos últimos 12 meses
    for i in range(12):
        target_date = datetime.now() - relativedelta(months=i)
        labels.append(target_date.strftime("%b/%Y"))
        budget_data.append(float(orcado_mensal))

        realizado_mes = Transaction.objects.filter(
            company=company, account__account_type='D', 
            date__year=target_date.year, date__month=target_date.month
        ).aggregate(total=Coalesce(Sum('amount'), Value(Decimal(0))))['total']
        actual_data.append(float(realizado_mes))

    labels.reverse()
    budget_data.reverse()
    actual_data.reverse()

    return JsonResponse({'labels': labels, 'budget_data': budget_data, 'actual_data': actual_data})


@login_required
def budget_edit_view(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        messages.error(request, "Por favor, selecione uma empresa primeiro.")
        return redirect('core:company_list')
    active_company = get_object_or_404(Company, pk=active_company_id, users=request.user)

    current_year = datetime.now().year

    # Garante que existe um objeto de orçamento para cada conta da empresa no ano atual
    accounts_qs = ChartOfAccounts.objects.filter(company=active_company)
    for acc in accounts_qs:
        Budget.objects.get_or_create(
            company=active_company,
            account=acc, 
            year=current_year,
            defaults={'annual_amount': 0}
        )

    # O queryset para o formset, filtrado e ordenado
    queryset = Budget.objects.filter(
        company=active_company, 
        year=current_year
    ).order_by('account__code')

    BudgetFormSet = modelformset_factory(Budget, form=BudgetForm, extra=0)

    if request.method == 'POST':
        formset = BudgetFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Orçamento salvo com sucesso!")
            return redirect('core:budget_edit')
    else:
        formset = BudgetFormSet(queryset=queryset)

    # Para exibir no template, precisamos dos objetos de conta na ordem correta
    # para mostrar a hierarquia. O formset já está ordenado, então podemos iterar sobre ele.
    context = {
        'formset': formset,
        'year': current_year,
    }
    return render(request, 'core/budget_edit.html', context)


@login_required
def import_transactions(request):
    """
    View para importar lançamentos via arquivo CSV.
    """
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        messages.error(request, "Por favor, selecione uma empresa primeiro.")
        return redirect('core:company_list')
    active_company = get_object_or_404(Company, pk=active_company_id, users=request.user)

    if request.method == 'POST':
        form = CSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'Este não é um arquivo CSV válido.')
                return redirect('core:import_transactions')

            # Lógica robusta de leitura e decodificação do arquivo
            try:
                data_set = csv_file.read().decode('utf-8-sig')
            except UnicodeDecodeError:
                csv_file.seek(0)
                data_set = csv_file.read().decode('latin-1')
            
            io_string = io.StringIO(data_set)
            
            # Lógica para detectar o delimitador (vírgula ou ponto e vírgula)
            try:
                dialect = csv.Sniffer().sniff(io_string.readline(), delimiters=';,')
                io_string.seek(0)
                reader = csv.DictReader(io_string, dialect=dialect)
            except csv.Error:
                messages.error(request, "Não foi possível determinar o formato do arquivo CSV.")
                return redirect('core:import_transactions')

            success_count = 0
            error_count = 0
            
            for i, row in enumerate(reader, 1):
                try:
                    transaction_date = datetime.strptime(row['data'], '%d/%m/%Y').date()
                    account_code = row['codigo_conta']
                    account = ChartOfAccounts.objects.get(company=active_company, code=account_code)
                    amount_str = row['valor'].replace('.', '').replace(',', '.')
                    amount = Decimal(amount_str)

                    Transaction.objects.create(
                        company=active_company,
                        account=account,
                        date=transaction_date,
                        amount=abs(amount),
                        description=row.get('descricao', '')
                    )
                    success_count += 1
                except ChartOfAccounts.DoesNotExist:
                    messages.warning(request, f"Linha {i}: A conta com código '{account_code}' não existe. A linha foi ignorada.")
                    error_count += 1
                except (ValueError, TypeError, InvalidOperation, KeyError) as e:
                    messages.warning(request, f"Linha {i}: Formato de data, valor ou coluna inválido ({e}). A linha foi ignorada.")
                    error_count += 1
            
            if success_count > 0:
                messages.success(request, f"{success_count} lançamentos foram importados com sucesso.")
            if error_count > 0:
                messages.error(request, f"Falha ao importar {error_count} linhas.")
            
            return redirect('core:transaction_list')
    else:
        form = CSVImportForm()
        
    context = {'form': form}
    return render(request, 'core/import_transactions.html', context)


@login_required
def download_transaction_template(request):
    """
    Gera e oferece para download um arquivo CSV modelo para importação de lançamentos,
    pré-preenchido com as contas da empresa ativa.
    """
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        messages.error(request, "Por favor, selecione uma empresa primeiro.")
        return redirect('core:company_list')
    active_company = get_object_or_404(Company, pk=active_company_id, users=request.user)

    # Usamos um buffer de texto em memória para criar o CSV de forma segura
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    
    # Escreve o cabeçalho
    writer.writerow(['data', 'codigo_conta', 'nome_conta', 'valor', 'descricao'])

    # Busca apenas as contas "folha" (que não têm filhas)
    accounts = ChartOfAccounts.objects.filter(
        company=active_company, 
        sub_accounts__isnull=True
    ).order_by('code')

    # Se não encontrar contas, adiciona uma linha de exemplo
    if not accounts.exists():
        writer.writerow(['(Ex: 31/12/2025)', '(Ex: 2.01.01.001)', '(Ex: Salários CLT)', '(Ex: -5000,00)', '(Ex: Pagamento de salários)'])
    else:
        # Se encontrar, preenche com os dados reais
        for account in accounts:
            writer.writerow(['', account.code, account.name, '', ''])
    
    # Pega o conteúdo do buffer
    csv_content = output.getvalue()

    # Cria a resposta HTTP final, usando 'utf-8-sig' para máxima compatibilidade com Excel
    response = HttpResponse(csv_content, content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="modelo_lancamentos_{active_company.name}.csv"'

    return response


# Em core/views.py
@login_required
def expense_percentage_chart_data(request):
    """Retorna composição percentual das despesas por grandes grupos.

    Corrigido: antes usava variáveis não definidas (start_date/end_date) e account_type 'E'.
    Agora usa 'D' (despesa), trata divisão por zero e sempre retorna 200.
    """
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return JsonResponse({'labels': [], 'data': [], 'error': 'No active company'}, status=400)
    company = get_object_or_404(Company, pk=active_company_id, users=request.user)

    today = date.today()
    start_date_str = request.GET.get('start_date', today.replace(day=1).strftime('%Y-%m-%d'))
    end_date_str = request.GET.get('end_date', (today.replace(day=calendar.monthrange(today.year, today.month)[1])).strftime('%Y-%m-%d'))

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'labels': [], 'data': [], 'error': 'Invalid date format'}, status=400)

    # Total de despesas no período
    total_realizado = Transaction.objects.filter(
        company=company, account__account_type='D', date__range=[start_date, end_date]
    ).aggregate(total=Coalesce(Sum('amount'), Value(Decimal('0.00'))))['total']

    def pct(code_prefix: str) -> Decimal:
        total = Transaction.objects.filter(
            company=company, account__account_type='D', date__range=[start_date, end_date], account__code__startswith=code_prefix
        ).aggregate(total=Coalesce(Sum('amount'), Value(Decimal('0.00'))))['total']
        if total_realizado and total_realizado > 0:
            return (total / total_realizado) * 100
        return Decimal('0')

    percentual_folha = pct('2.01.01')
    percentual_servicos_terceiros = pct('2.01.03')
    percentual_materiais = pct('2.01.02')
    percentual_apoio_gestao = pct('2.01.04')
    percentual_outras_despesas = pct('2.01.05')
    percentual_despesas_administrativas = pct('2.01.06')

    labels = ['Folha', 'Serviços Terceiros', 'Materiais', 'Apoio à Gestão', 'Outras Despesas', 'Desp. Admin.']
    data = [
        float(round(percentual_folha, 2)),
        float(round(percentual_servicos_terceiros, 2)),
        float(round(percentual_materiais, 2)),
        float(round(percentual_apoio_gestao, 2)),
        float(round(percentual_outras_despesas, 2)),
        float(round(percentual_despesas_administrativas, 2)),
    ]

    return JsonResponse({'labels': labels, 'data': data, 'total_realizado': float(total_realizado)})
