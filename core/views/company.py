from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.contrib import messages

from datetime import date

from ..models import Company
from ..forms import CompanyForm
from ..permissions import RoleRequiredMixin, has_role, ADMIN
from ..permissions import get_role


class CompanyCreateView(RoleRequiredMixin, LoginRequiredMixin, CreateView):
    model = Company
    form_class = CompanyForm
    template_name = 'core/company_form.html'
    success_url = reverse_lazy('core:company_list')
    allowed_roles = (ADMIN,)

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.users.add(self.request.user)
        messages.success(self.request, "Empresa criada com sucesso!")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Adicionar Nova Empresa'
        return context


class CompanyUpdateView(RoleRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Company
    form_class = CompanyForm
    template_name = 'core/company_form.html'
    success_url = reverse_lazy('core:company_list')
    allowed_roles = (ADMIN,)

    def get_queryset(self):
        return Company.objects.all()

    def form_valid(self, form):
        response = super().form_valid(form)
        # Atualiza usuários da empresa (somente admin)
        if has_role(self.request.user, ADMIN):
            selected_ids = self.request.POST.getlist('company_users')
            # Garante que o próprio admin sempre fica na empresa
            selected_ids_set = set(int(i) for i in selected_ids if i.isdigit())
            selected_ids_set.add(self.request.user.pk)
            self.object.users.set(selected_ids_set)
        messages.success(self.request, "Empresa atualizada com sucesso!")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Editar Empresa'
        context['can_manage_users'] = has_role(self.request.user, ADMIN)
        context['all_users'] = (User.objects
                                .select_related('profile')
                                .order_by('username'))
        context['company_user_ids'] = set(
            self.object.users.values_list('pk', flat=True)
        )
        return context


class CompanyDeleteView(RoleRequiredMixin, LoginRequiredMixin, DeleteView):
    model = Company
    template_name = 'core/company_confirm_delete.html'
    success_url = reverse_lazy('core:company_list')
    allowed_roles = (ADMIN,)

    def get_queryset(self):
        return Company.objects.all()

    def form_valid(self, form):
        messages.success(self.request, f"A empresa '{self.object.name}' foi excluída com sucesso.")
        return super().form_valid(form)


@login_required
def company_list(request):
    companies = Company.objects.filter(users=request.user)
    return render(request, 'core/company_list.html', {'companies': companies})


@login_required
def set_active_company(request, company_id):
    company = get_object_or_404(Company, pk=company_id, users=request.user)
    request.session['active_company_id'] = company.id
    return redirect('core:chart_of_accounts_list', company_id=company.id)


@login_required
def select_company(request, company_id):
    company = get_object_or_404(Company, pk=company_id, users=request.user)
    request.session['company_id'] = company.id
    request.session['active_company_id'] = company.id
    return redirect('core:dashboard', company_id=company.id)


@login_required
def home_redirect(request):
    active_company_id = request.session.get('active_company_id')
    active_company = None
    if active_company_id:
        active_company = Company.objects.filter(pk=active_company_id, users=request.user).first()

    role = get_role(request.user)

    return render(request, 'core/home.html', {
        'active_company': active_company,
        'role': role,
        'today': date.today(),
    })
