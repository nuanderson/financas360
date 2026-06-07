from django import forms
from datetime import datetime
from .models import (
    TransporteLancamento,
    UrgenciaConfiguracao, UrgenciaSetor, UrgenciaLancamento,
    CirurgiaConfiguracao, CirurgiaLancamento, CirurgiaSetor,
    NefrologiaConfiguracao, NefrologiaLancamento,
    BucomaxiloConfiguracao, BucomaxiloLancamento,
    ResidenciaConfiguracao, ResidenciaLancamento,
    CoordenacaoConfiguracao, CoordenacaoLancamento,
    AmbulatorioConfiguracao, AmbulatorioLancamento,
    UltrassonografiaConfiguracao, UltrassonografiaLancamento,
    EndoscopiaConfiguracao, EndoscopiaLancamento,
    AnestesiologiaConfiguracao, AnestesiologiaLancamento,
    ComissaoConfiguracao, ComissaoLancamento,
    CooperativaConfiguracao, CooperativaLancamento,
)


# ==========================================
# TRANSPORTE
# ==========================================

class TransporteForm(forms.ModelForm):
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
        data_str = self.cleaned_data['competencia']
        if not data_str:
            raise forms.ValidationError("A data é obrigatória.")
        try:
            return datetime.strptime(f"{data_str}-01", "%Y-%m-%d").date()
        except ValueError:
            raise forms.ValidationError("Formato de data inválido.")


# ==========================================
# URGÊNCIA E EMERGÊNCIA
# ==========================================

class UrgenciaSetorForm(forms.ModelForm):
    class Meta:
        model = UrgenciaSetor
        fields = ['name']
        labels = {'name': 'Nome do Setor (ex: Eixo Vermelho, UTI)'}


class UrgenciaConfiguracaoForm(forms.ModelForm):
    class Meta:
        model = UrgenciaConfiguracao
        fields = ['setor', 'cargo', 'qtd_dia', 'valor_plantao_dia', 'qtd_noite', 'valor_plantao_noite']
        widgets = {
            'setor': forms.Select(attrs={'class': 'form-select'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Clínico Geral'}),
            'qtd_dia': forms.NumberInput(attrs={'class': 'form-control'}),
            'valor_plantao_dia': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'qtd_noite': forms.NumberInput(attrs={'class': 'form-control'}),
            'valor_plantao_noite': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['setor'].queryset = UrgenciaSetor.objects.filter(company=company)


class UrgenciaLancamentoForm(forms.ModelForm):
    class Meta:
        model = UrgenciaLancamento
        fields = ['dias_mes', 'valor_pega_plantao', 'valor_efetivo', 'observacoes']
        widgets = {
            'dias_mes': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'style': 'width: 70px;'}),
            'valor_pega_plantao': forms.NumberInput(attrs={'class': 'form-control form-control-sm text-end', 'step': '0.01'}),
            'valor_efetivo': forms.NumberInput(attrs={'class': 'form-control form-control-sm text-end', 'step': '0.01'}),
            'observacoes': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
        }


# ==========================================
# CIRURGIA GERAL
# ==========================================

class CirurgiaSetorForm(forms.ModelForm):
    class Meta:
        model = CirurgiaSetor
        fields = ['name']
        labels = {'name': 'Nome do Setor (ex: Cirurgia Geral Eletiva)'}


class CirurgiaConfiguracaoForm(forms.ModelForm):
    class Meta:
        model = CirurgiaConfiguracao
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


# ==========================================
# NEFROLOGIA
# ==========================================

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


# ==========================================
# BUCOMAXILO
# ==========================================

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
        fields = ['dias_trabalhados', 'valor_pagar', 'observacoes']
        widgets = {
            'dias_trabalhados': forms.NumberInput(attrs={'class': 'form-control text-center', 'style': 'width: 80px;'}),
            'valor_pagar': forms.NumberInput(attrs={'class': 'form-control text-end fw-bold text-success', 'step': '0.01'}),
            'observacoes': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
        }


# ==========================================
# RESIDÊNCIA (AULAS COREME)
# ==========================================

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


# ==========================================
# COORDENAÇÕES
# ==========================================

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


# ==========================================
# AMBULATÓRIO
# ==========================================

class AmbulatorioConfigForm(forms.ModelForm):
    class Meta:
        model = AmbulatorioConfiguracao
        fields = ['nome_medico', 'especialidade', 'vinculo', 'ch_mensal', 'valor_mensal']
        widgets = {
            'nome_medico': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
            'especialidade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Clínica Médica, Ortopedia'}),
            'vinculo': forms.Select(attrs={'class': 'form-select'}),
            'ch_mensal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'placeholder': 'Ex: 40'}),
            'valor_mensal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class AmbulatorioLancamentoForm(forms.ModelForm):
    class Meta:
        model = AmbulatorioLancamento
        fields = ['valor_pagar', 'observacoes']
        widgets = {
            'valor_pagar': forms.NumberInput(attrs={'class': 'form-control text-end fw-bold text-success', 'step': '0.01'}),
            'observacoes': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
        }


# ==========================================
# ULTRASSONOGRAFIA
# ==========================================

class UltrassonografiaConfigForm(forms.ModelForm):
    class Meta:
        model = UltrassonografiaConfiguracao
        fields = ['cargo', 'qtd_dia', 'valor_plantao_dia', 'qtd_noite', 'valor_plantao_noite']
        widgets = {
            'cargo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Plantonista Diurno'}),
            'qtd_dia': forms.NumberInput(attrs={'class': 'form-control'}),
            'valor_plantao_dia': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'qtd_noite': forms.NumberInput(attrs={'class': 'form-control'}),
            'valor_plantao_noite': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class UltrassonografiaLancamentoForm(forms.ModelForm):
    class Meta:
        model = UltrassonografiaLancamento
        fields = ['dias_mes', 'valor_pega_plantao', 'valor_efetivo', 'observacoes']
        widgets = {
            'dias_mes': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'style': 'width: 70px;'}),
            'valor_pega_plantao': forms.NumberInput(attrs={'class': 'form-control form-control-sm text-end', 'step': '0.01'}),
            'valor_efetivo': forms.NumberInput(attrs={'class': 'form-control form-control-sm text-end', 'step': '0.01'}),
            'observacoes': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
        }


# ==========================================
# ENDOSCOPIA E OUTROS EXAMES
# ==========================================

class EndoscopiaConfigForm(forms.ModelForm):
    class Meta:
        model = EndoscopiaConfiguracao
        fields = ['nome_procedimento', 'valor_unitario', 'meta_mensal_qtd']
        widgets = {
            'nome_procedimento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Endoscopia Digestiva Alta'}),
            'valor_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'meta_mensal_qtd': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Média mensal esperada'}),
        }


class EndoscopiaLancamentoForm(forms.ModelForm):
    class Meta:
        model = EndoscopiaLancamento
        fields = ['qtd_realizada', 'observacoes']
        widgets = {
            'qtd_realizada': forms.NumberInput(attrs={'class': 'form-control text-center fw-bold text-primary'}),
            'observacoes': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
        }


# ==========================================
# ANESTESIOLOGIA
# ==========================================

class AnestesiologiaConfigForm(forms.ModelForm):
    class Meta:
        model = AnestesiologiaConfiguracao
        fields = ['tipo_servico', 'qtd_dia', 'valor_plantao_dia', 'qtd_noite', 'valor_plantao_noite']
        widgets = {
            'tipo_servico': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: C/D Plantão, S/D Plantão, Eletivas'}),
            'qtd_dia': forms.NumberInput(attrs={'class': 'form-control'}),
            'valor_plantao_dia': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'qtd_noite': forms.NumberInput(attrs={'class': 'form-control'}),
            'valor_plantao_noite': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class AnestesiologiaLancamentoForm(forms.ModelForm):
    class Meta:
        model = AnestesiologiaLancamento
        fields = ['dias_mes', 'valor_pega_plantao', 'valor_efetivo', 'observacoes']
        widgets = {
            'dias_mes': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'style': 'width: 70px;'}),
            'valor_pega_plantao': forms.NumberInput(attrs={'class': 'form-control form-control-sm text-end', 'step': '0.01'}),
            'valor_efetivo': forms.NumberInput(attrs={'class': 'form-control form-control-sm text-end', 'step': '0.01'}),
            'observacoes': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
        }


# ==========================================
# COMISSÕES
# ==========================================

class ComissaoConfigForm(forms.ModelForm):
    class Meta:
        model = ComissaoConfiguracao
        fields = ['nome_comissao', 'descricao', 'valor_mensal']
        widgets = {
            'nome_comissao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Comissão de Ética Médica'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descrição opcional'}),
            'valor_mensal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class ComissaoLancamentoForm(forms.ModelForm):
    class Meta:
        model = ComissaoLancamento
        fields = ['valor_pagar', 'observacoes']
        widgets = {
            'valor_pagar': forms.NumberInput(attrs={'class': 'form-control text-end fw-bold text-success', 'step': '0.01'}),
            'observacoes': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
        }


# ==========================================
# COOPERATIVAS
# ==========================================

class CooperativaConfigForm(forms.ModelForm):
    class Meta:
        model = CooperativaConfiguracao
        fields = ['nome_cooperativa', 'descricao', 'valor_mensal']
        widgets = {
            'nome_cooperativa': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: CIPERD, BARBOSA'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Serviço prestado'}),
            'valor_mensal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class CooperativaLancamentoForm(forms.ModelForm):
    class Meta:
        model = CooperativaLancamento
        fields = ['valor_pagar', 'observacoes']
        widgets = {
            'valor_pagar': forms.NumberInput(attrs={'class': 'form-control text-end fw-bold text-success', 'step': '0.01'}),
            'observacoes': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
        }
