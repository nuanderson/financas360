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

    def clean(self):
        # Pega todos os dados já "limpos" pelo Django
        cleaned_data = super().clean()
        code = cleaned_data.get("code")

        # Pega a instância da conta que está sendo editada (se for o caso)
        instance = self.instance

        # 1. Validação para bloquear códigos reservados
        if code in ['1', '2']:
            # Levanta um erro de validação que será mostrado para o usuário
            raise forms.ValidationError(
                f"O código '{code}' é reservado para as contas principais do sistema e não pode ser cadastrado."
            )

        # 2. Validação para bloquear códigos duplicados
        if code:
            # Precisamos saber para qual empresa estamos validando
            # Se for uma edição, pegamos a empresa da instância. Se for criação, não temos a empresa aqui ainda.
            # A melhor abordagem é garantir que a empresa seja passada para o form.
            # Vamos assumir que a 'company' está disponível (já fizemos isso na view)
            company = self.fields['parent_account'].queryset.first().company if self.fields['parent_account'].queryset.exists() else None

            if company:
                # Monta a consulta para ver se já existe uma conta com esse código na empresa
                queryset = ChartOfAccounts.objects.filter(
                    company=company,
                    code=code
                )

                # Se estamos editando uma conta, precisamos excluir ela mesma da busca
                if instance and instance.pk:
                    queryset = queryset.exclude(pk=instance.pk)

                # Se a consulta encontrar qualquer resultado, o código já existe.
                if queryset.exists():
                    raise forms.ValidationError(
                        f"O código '{code}' já está em uso no plano de contas desta empresa. Por favor, escolha outro."
                    )

        return cleaned_data

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