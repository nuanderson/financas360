from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Customer, Supplier, Service, Sale, BankAccount
from .forms import CustomerForm, SupplierForm, ServiceForm, SaleForm, BankAccountForm
from core.models import Company
import json

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