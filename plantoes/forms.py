from django import forms
from .models import Especialidade, Turno, UnidadeAssistencia, OrcamentoPlantao, LancamentoPlantao

class EspecialidadeForm(forms.ModelForm):
    class Meta:
        model = Especialidade
        fields = ['name']
        labels = {'name': 'Nome da Especialidade'}

class TurnoForm(forms.ModelForm):
    class Meta:
        model = Turno
        fields = ['name']
        labels = {'name': 'Nome do Turno (ex: Dia, Noite)'}

class UnidadeAssistenciaForm(forms.ModelForm):
    class Meta:
        model = UnidadeAssistencia
        fields = ['name']
        labels = {'name': 'Nome da Unidade de Assistência'}


class OrcamentoPlantaoForm(forms.ModelForm):
    class Meta:
        model = OrcamentoPlantao
        fields = ['especialidade', 'turno', 'unidade_assistencia', 'quantidade', 'tipo_plantao', 'valor_plantao']

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['especialidade'].queryset = Especialidade.objects.filter(company=company)
            self.fields['turno'].queryset = Turno.objects.filter(company=company)
            self.fields['unidade_assistencia'].queryset = UnidadeAssistencia.objects.filter(company=company)


class LancamentoPlantaoForm(forms.ModelForm):
    class Meta:
        model = LancamentoPlantao
        # A view vai cuidar de associar o 'orcamento' e a 'date'
        fields = ['valor_realizado', 'observacoes']
        widgets = {
            'valor_realizado': forms.NumberInput(attrs={'class': 'form-control form-control-sm text-end'}),
            'observacoes': forms.TextInput(attrs={'class': 'form-control form-control-sm'})
        }