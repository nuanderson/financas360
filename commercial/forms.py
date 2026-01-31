from django import forms
from .models import Customer, Supplier, Service, Sale, BankAccount, MonthlyGoal
from core.models import ChartOfAccounts as Account
from core.models import Transaction

# --- FORMULÁRIO DE CLIENTE ---
class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'cpf', 'phone', 'email', 'birth_date', 'address', 'notes']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

# --- FORMULÁRIO DE FORNECEDOR ---
class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['trade_name', 'corporate_name', 'tax_id', 'contact_info', 'default_account']
        widgets = {
            'trade_name': forms.TextInput(attrs={'class': 'form-control'}),
            'corporate_name': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_info': forms.TextInput(attrs={'class': 'form-control'}),
            'default_account': forms.Select(attrs={'class': 'form-select select2-widget'}),
        }

    def __init__(self, *args, **kwargs):
        company_id = kwargs.pop('company_id', None)
        super().__init__(*args, **kwargs)
        if company_id:
            # Filtra apenas contas dessa empresa e que sejam de DESPESA ('D')
            self.fields['default_account'].queryset = self.fields['default_account'].queryset.filter(
                company_id=company_id, 
                account_type='D'
            )

# --- FORMULÁRIO DE SERVIÇO ---
class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'default_price', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'default_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

# --- FORMULÁRIO DE VENDA (ATUALIZADO) ---
class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale

        fields = [
            'customer', 'service', 'sale_date', 
            'total_amount', 'entry_amount', 'installment_count', 
            'payment_method', 
            'category',       # Plano de Contas
            'bank_account',   # Banco/Caixa
            'status', 'notes'
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select select2-widget'}),
            'service': forms.Select(attrs={'class': 'form-select select2-widget'}),
            
            # CATEGORIA (Plano de Contas) - Select2 para facilitar busca
            'category': forms.Select(attrs={'class': 'form-select select2-widget'}),
            
            # CONTA BANCÁRIA - Dropdown simples com destaque
            'bank_account': forms.Select(attrs={'class': 'form-select fw-bold bg-light'}),
            
            'sale_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'entry_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'installment_count': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select fw-bold'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        company_id = kwargs.pop('company_id', None)
        super().__init__(*args, **kwargs)
        
        if company_id:
            # 1. Filtros básicos
            self.fields['customer'].queryset = self.fields['customer'].queryset.filter(company_id=company_id)
            self.fields['service'].queryset = self.fields['service'].queryset.filter(company_id=company_id)
            
            # 2. Categoria: Mostra contas de RECEITA ('R') do Plano de Contas
            self.fields['category'].queryset = Account.objects.filter(
                company_id=company_id, 
                account_type='R' 
            )
            self.fields['category'].label = "Categoria (Plano de Contas)"
            
            # 3. Conta Bancária: Mostra apenas os bancos cadastrados
            self.fields['bank_account'].queryset = BankAccount.objects.filter(company_id=company_id)
            self.fields['bank_account'].label = "Destino (Banco/Caixa)"


# --- FORMULÁRIO DE CONTA BANCÁRIA ---
class BankAccountForm(forms.ModelForm):
    class Meta:
        model = BankAccount
        fields = ['name', 'initial_balance']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Banco Cora, Cofre, Rede'}),
            'initial_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

# --- FORMULÁRIO DE DESPESA (CONTAS A PAGAR) ---
class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            'description', 'supplier', 'account', 
            'amount', 'due_date', 'bank_account', 'notes' # notes não existe nativo no Transaction, vamos usar description ou criar um campo extra se precisar. 
            # Se Transaction não tem 'notes', usamos apenas description.
        ]
        # Ajuste conforme os campos reais do seu Transaction model no core
        fields = ['description', 'supplier', 'account', 'amount', 'due_date', 'bank_account']
        
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Conta de Luz, Compra de Material'}),
            'supplier': forms.Select(attrs={'class': 'form-select select2-widget'}),
            'account': forms.Select(attrs={'class': 'form-select select2-widget'}), # Categoria
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'bank_account': forms.Select(attrs={'class': 'form-select'}), # De onde vai sair o dinheiro
        }

    def __init__(self, *args, **kwargs):
        company_id = kwargs.pop('company_id', None)
        super().__init__(*args, **kwargs)
        if company_id:
            # Filtros básicos
            self.fields['supplier'].queryset = self.fields['supplier'].queryset.filter(company_id=company_id)
            self.fields['bank_account'].queryset = BankAccount.objects.filter(company_id=company_id)
            
            # FILTRO CRUCIAL: Mostrar apenas contas de DESPESA ('D')
            self.fields['account'].queryset = Account.objects.filter(
                company_id=company_id, 
                account_type='D'
            )
            self.fields['account'].label = "Categoria de Despesa"
            self.fields['bank_account'].label = "Pagar com (Banco/Caixa)"

# --- FORMULÁRIO DE META MENSAL ---         

class MonthlyGoalForm(forms.ModelForm):

    month = forms.DateField(
        label="Mês de Referência",
        widget=forms.DateInput(attrs={'type': 'month', 'class': 'form-control'}),
        input_formats=['%Y-%m', '%Y-%m-%d']
    )
    class Meta:
        model = MonthlyGoal
        fields = ['account', 'month', 'target_amount']
        widgets = {
            'account': forms.Select(attrs={'class': 'form-select select2-widget'}),
            'month': forms.DateInput(attrs={'type': 'month', 'class': 'form-control'}), # Input tipo Mês!
            'target_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        company_id = kwargs.pop('company_id', None)
        super().__init__(*args, **kwargs)
        if company_id:
            # Mostra todas as contas (Receitas e Despesas)
            self.fields['account'].queryset = Account.objects.filter(company_id=company_id)