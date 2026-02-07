from django import forms
from datetime import datetime
from .models import Especialidade, Turno, UnidadeAssistencia, OrcamentoMensalPlantao, LancamentoPlantao, TransporteLancamento, UrgenciaConfiguracao, UrgenciaSetor, UrgenciaLancamento, CirurgiaConfiguracao, CirurgiaLancamento, CirurgiaSetor, NefrologiaConfiguracao, NefrologiaLancamento, BucomaxiloConfiguracao, BucomaxiloLancamento, ResidenciaConfiguracao, ResidenciaLancamento, CoordenacaoConfiguracao, CoordenacaoLancamento

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



class TransporteForm(forms.ModelForm):
    # TRUQUE: Definimos como CharField para aceitar a string "2025-01" sem erro imediato
    competencia = forms.CharField(
        widget=forms.TextInput(attrs={'type': 'month', 'class': 'form-control'}),
        label="Mês de Referência"
    )

    class Meta:
        model = TransporteLancamento
        fields = ['competencia', 'descricao', 'quantidade_viagens', 'valor_viagem']
        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Ambulância UTI'}),
            'quantidade_viagens': forms.NumberInput(attrs={'class': 'form-control'}),
            'valor_viagem': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def clean_competencia(self):
        """
        Recebe a string 'YYYY-MM' do input type='month' e transforma em data 'YYYY-MM-01'
        """
        data_str = self.cleaned_data['competencia']
        
        if not data_str:
            raise forms.ValidationError("A data é obrigatória.")

        try:
            # Pega "2025-01", adiciona "-01" e converte para data real
            data_formatada = datetime.strptime(f"{data_str}-01", "%Y-%m-%d").date()
            return data_formatada
        except ValueError:
            raise forms.ValidationError("Formato de data inválido.")


class UrgenciaSetorForm(forms.ModelForm):
    class Meta:
        model = UrgenciaSetor
        fields = ['name']
        labels = {'name': 'Nome do Setor (ex: Eixo Vermelho)'}

class UrgenciaConfiguracaoForm(forms.ModelForm):
    class Meta:
        model = UrgenciaConfiguracao
        fields = ['setor', 'cargo', 'qtd_dia', 'valor_plantao_dia', 'qtd_noite', 'valor_plantao_noite']
        widgets = {
            'setor': forms.Select(attrs={'class': 'form-select'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Clínico Geral, Pediatra'}),
            
            # Agrupamento Visual (Dia)
            'qtd_dia': forms.NumberInput(attrs={'class': 'form-control'}),
            'valor_plantao_dia': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            
            # Agrupamento Visual (Noite)
            'qtd_noite': forms.NumberInput(attrs={'class': 'form-control'}),
            'valor_plantao_noite': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            
            'dias_base_mensal': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Padrão: 30'}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            # Filtra apenas setores da empresa ativa
            self.fields['setor'].queryset = UrgenciaSetor.objects.filter(company=company)


class UrgenciaLancamentoForm(forms.ModelForm):
    class Meta:
        model = UrgenciaLancamento
        fields = ['dias_mes', 'valor_pega_plantao', 'valor_efetivo', 'observacoes']
        widgets = {
            'dias_mes': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'style': 'width: 70px;'}),
            'valor_pega_plantao': forms.NumberInput(attrs={'class': 'form-control form-control-sm text-end', 'step': '0.01'}),
            'valor_efetivo': forms.NumberInput(attrs={'class': 'form-control form-control-sm text-end', 'step': '0.01'}),
            'observacoes': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Obs...'}),
        }

# --- FORMS CIRURGIA GERAL ---

class CirurgiaSetorForm(forms.ModelForm):
    class Meta:
        model = CirurgiaSetor
        fields = ['name']
        labels = {'name': 'Nome do Setor (ex: Cirurgia Geral Eletiva)'}

class CirurgiaConfiguracaoForm(forms.ModelForm):
    class Meta:
        model = CirurgiaConfiguracao
        # Lembre-se: removemos dias_base_mensal
        fields = ['setor', 'cargo', 'qtd_dia', 'valor_plantao_dia', 'qtd_noite', 'valor_plantao_noite']
        widgets = {
            'setor': forms.Select(attrs={'class': 'form-select'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Cirurgião, Anestesista'}),
            
            'qtd_dia': forms.NumberInput(attrs={'class': 'form-control'}),
            'valor_plantao_dia': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            
            'qtd_noite': forms.NumberInput(attrs={'class': 'form-control'}),
            'valor_plantao_noite': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['setor'].queryset = CirurgiaSetor.objects.filter(company=company)

class CirurgiaLancamentoForm(forms.ModelForm):
    class Meta:
        model = CirurgiaLancamento
        fields = ['dias_mes', 'valor_pega_plantao', 'valor_efetivo', 'observacoes']
        widgets = {
            'dias_mes': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'style': 'width: 70px;'}),
            'valor_pega_plantao': forms.NumberInput(attrs={'class': 'form-control form-control-sm text-end', 'step': '0.01'}),
            'valor_efetivo': forms.NumberInput(attrs={'class': 'form-control form-control-sm text-end', 'step': '0.01'}),
            'observacoes': forms.TextInput(attrs={'class': 'form-control form-control-sm'}), 
        }

# --- FORMS NEFROLOGIA ---

class NefrologiaConfigForm(forms.ModelForm):
    class Meta:
        model = NefrologiaConfiguracao
        fields = ['nome_procedimento', 'valor_unitario', 'meta_mensal_qtd']
        widgets = {
            'nome_procedimento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Hemodiálise Com CDL'}),
            'valor_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'meta_mensal_qtd': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Média esperada por mês'}),
        }

class NefrologiaLancamentoForm(forms.ModelForm):
    class Meta:
        model = NefrologiaLancamento
        fields = ['qtd_realizada', 'observacoes']
        widgets = {
            'qtd_realizada': forms.NumberInput(attrs={'class': 'form-control text-center fw-bold text-primary'}),
            'observacoes': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
        }

# Adicione os imports no topo:
from .models import (
    # ... outros ...
    BucomaxiloConfiguracao, BucomaxiloLancamento
)

# --- FORMS BUCOMAXILO ---

class BucomaxiloConfigForm(forms.ModelForm):
    class Meta:
        model = BucomaxiloConfiguracao
        fields = ['nome_profissional', 'descricao_servico', 'valor_mensal']
        widgets = {
            'nome_profissional': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Dr. Alan ou Clare Odonto'}),
            'descricao_servico': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Sobreaviso 24h'}),
            'valor_mensal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class BucomaxiloLancamentoForm(forms.ModelForm):
    class Meta:
        model = BucomaxiloLancamento
        # O usuário edita os dias trabalhados e o valor final
        fields = ['dias_trabalhados', 'valor_pagar', 'observacoes']
        widgets = {
            'dias_trabalhados': forms.NumberInput(attrs={'class': 'form-control text-center', 'style': 'width: 80px;'}),
            'valor_pagar': forms.NumberInput(attrs={'class': 'form-control text-end fw-bold text-success', 'step': '0.01'}),
            'observacoes': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
        }

# --- FORMS RESIDÊNCIA ---

class ResidenciaConfigForm(forms.ModelForm):
    class Meta:
        model = ResidenciaConfiguracao
        fields = ['nome_medico', 'valor_aula', 'meta_aulas']
        widgets = {
            'nome_medico': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Angelo Padua Reis'}),
            'valor_aula': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'meta_aulas': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Qtd média esperada'}),
        }

class ResidenciaLancamentoForm(forms.ModelForm):
    class Meta:
        model = ResidenciaLancamento
        fields = ['qtd_aulas', 'observacoes']
        widgets = {
            'qtd_aulas': forms.NumberInput(attrs={'class': 'form-control text-center fw-bold text-primary', 'style': 'width: 80px;'}),
            'observacoes': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
        }

# Imports no topo:
from .models import (
    # ... outros ...
    CoordenacaoConfiguracao, CoordenacaoLancamento
)

# --- FORMS COORDENAÇÃO ---

class CoordenacaoConfigForm(forms.ModelForm):
    class Meta:
        model = CoordenacaoConfiguracao
        fields = ['nome_funcionario', 'matricula', 'conselho', 'setor', 'valor_mensal']
        widgets = {
            'nome_funcionario': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome Completo'}),
            'matricula': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Diretor ou Nº Matrícula'}),
            'conselho': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: CRM 1234'}),
            'setor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: UTI, Administrativo'}),
            'valor_mensal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class CoordenacaoLancamentoForm(forms.ModelForm):
    class Meta:
        model = CoordenacaoLancamento
        fields = ['valor_pagar', 'observacoes']
        widgets = {
            'valor_pagar': forms.NumberInput(attrs={'class': 'form-control text-end fw-bold text-success', 'step': '0.01'}),
            'observacoes': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
        }