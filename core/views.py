from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import UpdateView, DeleteView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Company, ChartOfAccounts, Transaction
from .forms import ChartOfAccountsForm, TransactionForm, CompanyForm
from django.contrib import messages


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