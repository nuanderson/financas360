from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
import csv
import io

from ..models import Company, ChartOfAccounts
from ..forms import ChartOfAccountsForm, CSVImportForm
from ..permissions import (
    RoleRequiredMixin, role_required,
    ADMIN, GESTOR, MANAGERS, NON_PLANTOES,
)


class AccountUpdateView(RoleRequiredMixin, LoginRequiredMixin, UpdateView):
    """Editar conta — somente Admin/Gestor."""
    model          = ChartOfAccounts
    form_class     = ChartOfAccountsForm
    template_name  = 'core/account_update.html'
    pk_url_kwarg   = 'account_id'
    allowed_roles  = MANAGERS

    def get_queryset(self):
        company_id = self.kwargs.get('company_id')
        company = get_object_or_404(Company, pk=company_id, users=self.request.user)
        return ChartOfAccounts.objects.filter(company=company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.get_object().company
        return kwargs

    def get_success_url(self):
        company_id = self.kwargs.get('company_id')
        return reverse_lazy('core:chart_of_accounts_list', kwargs={'company_id': company_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['company'] = self.get_object().company
        return context


class AccountDeleteView(RoleRequiredMixin, LoginRequiredMixin, DeleteView):
    """Excluir conta — somente Admin/Gestor."""
    model         = ChartOfAccounts
    template_name = 'core/account_confirm_delete.html'
    pk_url_kwarg  = 'account_id'
    allowed_roles = MANAGERS

    def get_queryset(self):
        company_id = self.kwargs.get('company_id')
        company = get_object_or_404(Company, pk=company_id, users=self.request.user)
        return ChartOfAccounts.objects.filter(company=company)

    def get_success_url(self):
        company_id = self.kwargs.get('company_id')
        return reverse_lazy('core:chart_of_accounts_list', kwargs={'company_id': company_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['company'] = self.get_object().company
        return context


@login_required
def chart_of_accounts_list(request, company_id):
    from ..permissions import has_role
    company   = get_object_or_404(Company, pk=company_id, users=request.user)
    can_write = has_role(request.user, ADMIN, GESTOR)

    if request.method == 'POST':
        if not can_write:
            messages.error(request, "Você não tem permissão para criar contas.")
            return redirect('core:chart_of_accounts_list', company_id=company.id)
        form = ChartOfAccountsForm(request.POST, company=company)
        if form.is_valid():
            new_account = form.save(commit=False)
            new_account.company = company
            new_account.save()
            return redirect('core:chart_of_accounts_list', company_id=company.id)
    else:
        form = ChartOfAccountsForm(company=company)

    accounts = (ChartOfAccounts.objects.filter(company=company)
                .select_related('parent_account').order_by('code'))

    context = {
        'company':   company,
        'accounts':  accounts,
        'form':      form,
        'can_write': can_write,
    }
    return render(request, 'core/chart_of_accounts_list.html', context)


@login_required
@role_required(ADMIN, GESTOR)
def import_chart_of_accounts(request, company_id):
    company = get_object_or_404(Company, pk=company_id, users=request.user)

    if request.method == 'POST':
        form = CSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']

            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'Este não é um arquivo CSV válido.')
                return redirect('core:import_chart_of_accounts', company_id=company.id)

            try:
                data_set = csv_file.read().decode('utf-8-sig')
            except UnicodeDecodeError:
                csv_file.seek(0)
                data_set = csv_file.read().decode('latin-1')

            io_string = io.StringIO(data_set)

            try:
                dialect = csv.Sniffer().sniff(io_string.readline(), delimiters=';,')
                io_string.seek(0)
                reader = csv.DictReader(io_string, dialect=dialect)
                if not all(key in reader.fieldnames for key in ['code', 'name', 'account_type']):
                    messages.error(request, 'Cabeçalhos inválidos. Necessário: code, name, account_type')
                    return redirect('core:import_chart_of_accounts', company_id=company.id)

                created = updated = 0
                for row in reader:
                    obj, was_created = ChartOfAccounts.objects.update_or_create(
                        company=company,
                        code=row['code'].strip(),
                        defaults={
                            'name':         row['name'].strip(),
                            'account_type': row['account_type'].strip().upper(),
                        }
                    )
                    if was_created:
                        created += 1
                    else:
                        updated += 1

                messages.success(request,
                    f"Importação concluída: {created} criadas, {updated} atualizadas.")
            except Exception as e:
                messages.error(request, f"Erro na importação: {e}")

            return redirect('core:chart_of_accounts_list', company_id=company.id)
    else:
        form = CSVImportForm()

    return render(request, 'core/import_chart_of_accounts.html', {
        'company': company, 'form': form
    })
