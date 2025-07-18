from django import forms
from .models import ChartOfAccounts

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

        