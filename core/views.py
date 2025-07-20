from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import UpdateView, DeleteView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Company, ChartOfAccounts, Transaction
from .forms import ChartOfAccountsForm, TransactionForm, CompanyForm, CSVImportForm
from django.contrib import messages
from django.db.models import Sum, Q, F, Value, DecimalField
from django.db.models.functions import Coalesce 
from datetime import datetime, date
from django.http import JsonResponse, HttpResponse
from dateutil.relativedelta import relativedelta
from django.template.loader import render_to_string
from weasyprint import HTML
import calendar
import csv
import io


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
    # Buscamos o ID da empresa ativa diretamente da sessão
    active_company_id = request.session.get('active_company_id')
    
    # Se não houver empresa na sessão, redirecionamos para a seleção
    if not active_company_id:
        messages.error(request, "Por favor, selecione uma empresa primeiro.")
        return redirect('core:company_list')

    # Com o ID em mãos, buscamos o objeto da empresa no banco
    # A checagem de segurança continua aqui para garantir que o usuário ainda tem acesso
    active_company = get_object_or_404(Company, pk=active_company_id, users=request.user)

    # Lógica para o formulário de adição
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

    # Busca os lançamentos da empresa ativa para listar
    transactions = Transaction.objects.filter(company=active_company).order_by('-date')

    context = {
        'transactions': transactions,
        'form': form,
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
def dashboard(request, company_id):
    # Checagem de segurança padrão
    company = get_object_or_404(Company, pk=company_id, users=request.user)

    today = date.today()
    # Pega as datas do GET ou define o mês atual como padrão
    start_date_str = request.GET.get('start_date', today.replace(day=1).strftime('%Y-%m-%d'))
    end_date_str = request.GET.get('end_date', (today.replace(day=calendar.monthrange(today.year, today.month)[1])).strftime('%Y-%m-%d'))

    # Converte as strings de data para objetos date
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    # Filtra os lançamentos da empresa para o PERÍODO SELECIONADO
    transactions = Transaction.objects.filter(
        company=company,
        date__range=[start_date, end_date]
    )

    # Os cálculos agora usam a base de transações já filtrada
    total_revenue = transactions.filter(account__account_type='R').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = transactions.filter(account__account_type='E').aggregate(Sum('amount'))['amount__sum'] or 0
    net_result = total_revenue - total_expenses

    context = {
        'company': company,
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'net_result': net_result,
        # Passa as datas para o template para preencher o formulário
        'start_date_str': start_date_str,
        'end_date_str': end_date_str,
    }
    return render(request, 'core/dashboard.html', context)

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
        account__account_type='E',
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

        expense = transactions.filter(account__account_type='E').aggregate(
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
    total = transactions.filter(account=account).aggregate(total=Coalesce(Sum('amount'), Value(0.0), output_field=DecimalField()))['total']

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