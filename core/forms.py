from django import forms
from .models import ChartOfAccounts, Transaction, Company

class ChartOfAccountsForm(forms.ModelForm):
    class Meta:
        model = ChartOfAccounts
        # Listamos os campos que o usuário poderá preencher.
        # A 'company' será definida automaticamente na view.
        fields = ['code', 'name', 'account_type', 'parent_account']

    def __init__(self, *args, **kwargs):
        # Pegamos a 'company' que será passada pela view.
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        # Filtramos o campo 'parent_account' para mostrar apenas
        # as contas da empresa que está sendo editada.
        if company:
            self.fields['parent_account'].queryset = ChartOfAccounts.objects.filter(company=company)

class TransactionForm(forms.ModelForm):
    # Usamos um DateInput para que o navegador mostre um seletor de calendário
    date = forms.DateField(
        widget=forms.DateInput(
            attrs={'type': 'date'},
            format='%Y-%m-%d'  # <--- Adicione esta linha
        ),
        label="Data"
    )

    class Meta:
        model = Transaction
        # Campos que o usuário irá preencher
        fields = ['date', 'account', 'amount', 'description']
        
    def __init__(self, *args, **kwargs):
        # Pegamos a 'company' que será passada pela view
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        # Filtramos o campo 'account' para mostrar apenas as contas
        # da empresa ativa. Não queremos que o usuário lance na conta de outro cliente.
        if company:
            self.fields['account'].queryset = ChartOfAccounts.objects.filter(company=company)

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        # O usuário só precisa informar o nome. A associação com o usuário será automática.
        fields = ['name']