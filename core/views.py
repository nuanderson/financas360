from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Company, ChartOfAccounts
from .forms import ChartOfAccountsForm

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
def account_update(request, company_id, account_id):
    # Checagem de segurança dupla: garante que a empresa pertence ao usuário
    # E que a conta pertence à empresa.
    company = get_object_or_404(Company, pk=company_id, users=request.user)
    account = get_object_or_404(ChartOfAccounts, pk=account_id, company=company)

    if request.method == 'POST':
        # 'instance=account' preenche o formulário com os dados do objeto existente
        form = ChartOfAccountsForm(request.POST, instance=account, company=company)
        if form.is_valid():
            form.save()
            # Redireciona para a lista de contas após a edição
            return redirect('core:chart_of_accounts_list', company_id=company.id)
    else:
        # Se for um GET, apenas exibe o formulário preenchido com os dados da conta
        form = ChartOfAccountsForm(instance=account, company=company)

    context = {
        'form': form,
        'company': company,
        'account': account, # Passamos a conta para usar o nome no título, por exemplo
    }
    return render(request, 'core/account_update.html', context)

@login_required
def account_delete(request, company_id, account_id):
    company = get_object_or_404(Company, pk=company_id, users=request.user)
    account = get_object_or_404(ChartOfAccounts, pk=account_id, company=company)

    if request.method == 'POST':
        # Se o formulário de confirmação foi enviado, apaga o objeto
        account.delete()
        # E redireciona para a lista
        return redirect('core:chart_of_accounts_list', company_id=company.id)

    # Se for um GET, apenas mostra a página de confirmação
    context = {
        'account': account,
        'company': company,
    }
    return render(request, 'core/account_confirm_delete.html', context)

@login_required
def set_active_company(request, company_id):
    # Checagem de segurança para garantir que o usuário tem acesso a esta empresa
    company = get_object_or_404(Company, pk=company_id, users=request.user)

    # Aqui está a mágica: guardamos o ID da empresa na sessão do usuário
    request.session['active_company_id'] = company.id

    # Redirecionamos o usuário para a página do plano de contas da empresa recém-ativada
    return redirect('core:chart_of_accounts_list', company_id=company.id)