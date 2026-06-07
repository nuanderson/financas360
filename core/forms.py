from django import forms
from .models import ChartOfAccounts, Transaction, Company, Budget, NoteTag, Note

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
        #if code in ['1', '2']:
        #    # Levanta um erro de validação que será mostrado para o usuário
        #    raise forms.ValidationError(
        #        f"O código '{code}' é reservado para as contas principais do sistema e não pode ser cadastrado."
        #    )

        # 2. Validação para bloquear códigos duplicados
        if code:
            # Precisamos saber para qual empresa estamos validando
            # Se for uma edição, pegamos a empresa da instância. Se for criação, não temos a empresa aqui ainda.
            # A melhor abordagem é garantir que a empresa seja passada para o form.
            # Vamos assumir que a 'company' está disponível (já fizemos isso na view)
            first = self.fields['parent_account'].queryset.first()
            company = first.company if first is not None else None

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
    account_type_filter = forms.ChoiceField(
        choices=(('', 'Todos os tipos'), ('R', 'Receita'), ('D', 'Despesa')),
        required=False,
        label="Filtrar conta por tipo"
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        label="Data"
    )

    class Meta:
        model = Transaction
        fields = ['account_type_filter', 'date', 'account', 'amount', 'description', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 1}),
            'account': forms.Select(attrs={'class': 'select2-widget'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
        
    def __init__(self, *args, **kwargs):
        company            = kwargs.pop('company', None)
        # locked_type: 'R' → só receitas; 'D' → só despesas; None → todos
        locked_type        = kwargs.pop('locked_type', None)
        super().__init__(*args, **kwargs)

        qs = ChartOfAccounts.objects.none()
        if company:
            qs = ChartOfAccounts.objects.filter(company=company)
            if locked_type:
                qs = qs.filter(account_type=locked_type)
        self.fields['account'].queryset = qs

        # Se o tipo está travado, oculta o filtro de tipo do formulário
        if locked_type:
            self.fields['account_type_filter'].widget = \
                __import__('django.forms', fromlist=['HiddenInput']).HiddenInput()
            self.fields['account_type_filter'].initial = locked_type
            self.locked_type = locked_type
        else:
            self.locked_type = None

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'management_type']
        labels = {
            'name': 'Nome da Empresa',
            'management_type': 'Tipo de Gestão',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'management_type': forms.Select(attrs={'class': 'form-select'}),
        }

class CSVImportForm(forms.Form):
    csv_file = forms.FileField(label="Arquivo CSV")


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['amount']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-end',
                'step': '0.01',
                'min': '0',
            }),
        }


class TransactionFilterForm(forms.Form):
    start_date = forms.DateField(
        label="Data Início", required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    end_date = forms.DateField(
        label="Data Fim", required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    account_type = forms.ChoiceField(
        label="Tipo",
        choices=(('', 'Todos'), ('R', 'Receita'), ('D', 'Despesa')),
        required=False
    )
    status = forms.ChoiceField(
        label="Status",
        choices=(('', 'Todos'), ('PAID', 'Realizado'), ('PENDING', 'Pendente')),
        required=False
    )
    account = forms.ModelChoiceField(
        label="Conta",
        queryset=ChartOfAccounts.objects.none(),
        required=False,
        empty_label="Todas as contas"
    )

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['account'].queryset = ChartOfAccounts.objects.filter(company=company).order_by('code')


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['title', 'content', 'color', 'reminder_date', 'tag', 'is_global', 'is_public']
        widgets = {
            'reminder_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'color': forms.Select(attrs={'class': 'form-select'}),
            'tag': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['tag'].queryset = NoteTag.objects.filter(company=company)
        else:
            self.fields['tag'].queryset = NoteTag.objects.none()


class NoteTagForm(forms.ModelForm):
    class Meta:
        model = NoteTag
        fields = ['name']