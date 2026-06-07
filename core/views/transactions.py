from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse
from decimal import Decimal, InvalidOperation
from datetime import datetime
import csv
import io
import json

from django.db.models import Sum, Value, DecimalField
from django.db.models.functions import Coalesce

from ..models import Company, ChartOfAccounts, Transaction
from ..forms import TransactionForm, TransactionFilterForm, CSVImportForm
from ..permissions import (
    RoleRequiredMixin, role_required, has_role,
    ADMIN, GESTOR, MANAGERS, NON_PLANTOES,
    ANALISTA_RECEITAS, ANALISTA_DESPESAS,
)


def _locked_type_for_user(user):
    """
    Retorna o tipo de conta restrito para analistas.
    'R' para Analista de Receitas, 'D' para Analista de Despesas, None para demais.
    """
    role = None
    try:
        role = user.profile.role
    except Exception:
        pass
    if role == ANALISTA_RECEITAS:
        return 'R'
    if role == ANALISTA_DESPESAS:
        return 'D'
    return None


class TransactionUpdateView(RoleRequiredMixin, LoginRequiredMixin, UpdateView):
    """Editar lançamento — somente Admin/Gestor."""
    model         = Transaction
    form_class    = TransactionForm
    template_name = 'core/transaction_form.html'
    allowed_roles = MANAGERS

    def get_queryset(self):
        active_company_id = self.request.session.get('active_company_id')
        if not active_company_id:
            return Transaction.objects.none()
        active_company = get_object_or_404(
            Company, pk=active_company_id, users=self.request.user)
        return Transaction.objects.filter(company=active_company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        active_company_id = self.request.session.get('active_company_id')
        if active_company_id:
            kwargs['company'] = get_object_or_404(Company, pk=active_company_id)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Editar Lançamento'
        return context

    def get_success_url(self):
        return reverse_lazy('core:transaction_list')

    def form_valid(self, form):
        if not form.instance.created_by:
            form.instance.created_by = self.request.user
        return super().form_valid(form)


class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    """
    Excluir lançamento.
    Admin/Gestor: podem deletar qualquer tipo.
    Analista Receitas: só pode deletar receitas.
    Analista Despesas: só pode deletar despesas.
    Outros: bloqueados.
    """
    model         = Transaction
    template_name = 'core/transaction_confirm_delete.html'

    def get_queryset(self):
        active_company_id = self.request.session.get('active_company_id')
        if not active_company_id:
            return Transaction.objects.none()
        active_company = get_object_or_404(
            Company, pk=active_company_id, users=self.request.user)
        return Transaction.objects.filter(company=active_company)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('core:login')
        obj = self.get_object()
        locked = _locked_type_for_user(request.user)
        if locked and obj.account.account_type != locked:
            messages.error(request,
                "Você não tem permissão para excluir este tipo de lançamento.")
            return redirect('core:transaction_list')
        if not has_role(request.user, ADMIN, GESTOR,
                        ANALISTA_RECEITAS, ANALISTA_DESPESAS):
            messages.error(request, "Você não tem permissão para excluir lançamentos.")
            return redirect('core:transaction_list')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, "Lançamento excluído com sucesso.")
        return reverse_lazy('core:transaction_list')


@login_required
def transaction_list(request):
    # Analista de Plantões não acessa
    if not has_role(request.user, ADMIN, GESTOR, ANALISTA_RECEITAS, ANALISTA_DESPESAS):
        messages.error(request, "Você não tem permissão para acessar os lançamentos.")
        return redirect('core:company_list')

    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        messages.error(request, "Por favor, selecione uma empresa primeiro.")
        return redirect('core:company_list')

    active_company = get_object_or_404(Company, pk=active_company_id, users=request.user)
    locked_type    = _locked_type_for_user(request.user)

    if request.method == 'POST':
        form = TransactionForm(request.POST, company=active_company,
                               locked_type=locked_type)
        if form.is_valid():
            # Garantia extra: mesmo que alguém contorne o form,
            # bloqueia salvar conta do tipo errado
            acct = form.cleaned_data.get('account')
            if locked_type and acct and acct.account_type != locked_type:
                messages.error(request,
                    "Você só pode lançar no tipo de conta permitido ao seu perfil.")
            else:
                new_transaction              = form.save(commit=False)
                new_transaction.company      = active_company
                new_transaction.created_by   = request.user
                new_transaction.save()
                messages.success(request, "Lançamento salvo com sucesso!")
            return redirect('core:transaction_list')
    else:
        form = TransactionForm(company=active_company, locked_type=locked_type)

    transactions_list = Transaction.objects.filter(
        company=active_company
    ).select_related('account', 'created_by').order_by('-date', '-pk')

    filter_form = TransactionFilterForm(request.GET, company=active_company)

    if filter_form.is_valid():
        start_date = filter_form.cleaned_data.get('start_date')
        end_date   = filter_form.cleaned_data.get('end_date')
        account    = filter_form.cleaned_data.get('account')
        acc_type   = filter_form.cleaned_data.get('account_type')
        status     = filter_form.cleaned_data.get('status')

        if start_date:
            transactions_list = transactions_list.filter(date__gte=start_date)
        if end_date:
            transactions_list = transactions_list.filter(date__lte=end_date)
        if account:
            transactions_list = transactions_list.filter(account=account)
        if acc_type:
            transactions_list = transactions_list.filter(account__account_type=acc_type)
        if status:
            transactions_list = transactions_list.filter(status=status)

    total_receitas = transactions_list.filter(
        account__account_type='R'
    ).aggregate(total=Coalesce(Sum('amount'), Value(0, output_field=DecimalField())))['total']

    total_despesas = transactions_list.filter(
        account__account_type__in=['D', 'E']
    ).aggregate(total=Coalesce(Sum('amount'), Value(0, output_field=DecimalField())))['total']

    saldo = total_receitas - total_despesas

    paginator    = Paginator(transactions_list, 25)
    page_number  = request.GET.get('page')
    transactions = paginator.get_page(page_number)

    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']

    all_accounts = ChartOfAccounts.objects.filter(
        company=active_company).values('pk', 'code', 'name', 'account_type')
    all_accounts_json_str = json.dumps(list(all_accounts))

    context = {
        'transactions':         transactions,
        'form':                 form,
        'filter_form':          filter_form,
        'all_accounts_json_str': all_accounts_json_str,
        'total_receitas':       total_receitas,
        'total_despesas':       total_despesas,
        'saldo':                saldo,
        'total_count':          paginator.count,
        'query_params':         query_params,
        'locked_type':          locked_type,
        'can_manage':           has_role(request.user, ADMIN, GESTOR),
    }
    return render(request, 'core/transaction_list.html', context)


@login_required
@role_required(ADMIN, GESTOR)
def import_transactions(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        messages.error(request, "Por favor, selecione uma empresa primeiro.")
        return redirect('core:company_list')
    active_company = get_object_or_404(Company, pk=active_company_id, users=request.user)

    if request.method == 'POST':
        form = CSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            try:
                data_set = csv_file.read().decode('utf-8-sig')
            except UnicodeDecodeError:
                csv_file.seek(0)
                data_set = csv_file.read().decode('latin-1')

            io_string = io.StringIO(data_set)
            reader    = csv.DictReader(io_string, delimiter=';')
            created   = 0
            errors    = []
            for i, row in enumerate(reader, start=2):
                try:
                    account = ChartOfAccounts.objects.get(
                        company=active_company, code=row.get('account_code', '').strip())
                    Transaction.objects.create(
                        company=active_company,
                        account=account,
                        date=datetime.strptime(row['date'].strip(), '%d/%m/%Y').date(),
                        amount=Decimal(row['amount'].strip().replace(',', '.')),
                        description=row.get('description', '').strip(),
                        created_by=request.user,
                    )
                    created += 1
                except Exception as e:
                    errors.append(f"Linha {i}: {e}")

            if errors:
                for err in errors[:5]:
                    messages.warning(request, err)
            messages.success(request, f"{created} lançamento(s) importado(s).")
            return redirect('core:transaction_list')
    else:
        form = CSVImportForm()

    return render(request, 'core/import_transactions.html', {
        'form': form, 'company': active_company
    })


@login_required
@role_required(ADMIN, GESTOR)
def download_transaction_template(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="modelo_lancamentos.csv"'
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['date', 'account_code', 'amount', 'description'])
    writer.writerow(['01/01/2026', '1.01.001', '1000,00', 'Exemplo de receita'])
    return response
