from django import forms
from .models import Especialidade, Turno, UnidadeAssistencia, OrcamentoMensalPlantao, LancamentoPlantao

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

class OrcamentoMensalPlantaoForm(forms.ModelForm):
    class Meta:
        model = OrcamentoMensalPlantao
        fields = ['valor_orcado']
        widgets = {
            'valor_orcado': forms.NumberInput(attrs={'class': 'form-control form-control-sm text-end'}),
        }

class LancamentoPlantaoForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label="Data do Plantão")

    class Meta:
        model = LancamentoPlantao
        fields = ['especialidade', 'turno', 'unidade_assistencia', 'date', 
                  'quantidade', 'tipo_plantao', 'valor_unitario', 'observacoes']
        widgets = {
            'especialidade': forms.Select(attrs={'class': 'form-select select2-widget'}),
            'turno': forms.Select(attrs={'class': 'form-select select2-widget'}),
            'unidade_assistencia': forms.Select(attrs={'class': 'form-select select2-widget'}),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['especialidade'].queryset = Especialidade.objects.filter(company=company)
            self.fields['turno'].queryset = Turno.objects.filter(company=company)
            self.fields['unidade_assistencia'].queryset = UnidadeAssistencia.objects.filter(company=company)