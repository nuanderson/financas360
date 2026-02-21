from django.contrib import admin
from .models import (
    TransporteLancamento,
    UrgenciaSetor, UrgenciaConfiguracao, UrgenciaLancamento,
    CirurgiaSetor, CirurgiaConfiguracao, CirurgiaLancamento,
    NefrologiaConfiguracao, NefrologiaLancamento,
    BucomaxiloConfiguracao, BucomaxiloLancamento,
    ResidenciaConfiguracao, ResidenciaLancamento,
    CoordenacaoConfiguracao, CoordenacaoLancamento
)

# ==========================================
# TRANSPORTE
# ==========================================
@admin.register(TransporteLancamento)
class TransporteLancamentoAdmin(admin.ModelAdmin):
    list_display = ('company', 'competencia', 'descricao', 'quantidade_viagens', 'valor_viagem', 'total')
    list_filter = ('company', 'competencia')
    search_fields = ('descricao',)

# ==========================================
# URGÊNCIA E EMERGÊNCIA
# ==========================================
@admin.register(UrgenciaSetor)
class UrgenciaSetorAdmin(admin.ModelAdmin):
    list_display = ('name', 'company')
    list_filter = ('company',)
    search_fields = ('name',)

@admin.register(UrgenciaConfiguracao)
class UrgenciaConfiguracaoAdmin(admin.ModelAdmin):
    list_display = ('setor', 'cargo', 'qtd_dia', 'valor_plantao_dia', 'qtd_noite', 'valor_plantao_noite')
    list_filter = ('setor__company', 'setor')
    search_fields = ('cargo',)

@admin.register(UrgenciaLancamento)
class UrgenciaLancamentoAdmin(admin.ModelAdmin):
    list_display = ('competencia', 'company', 'setor_nome', 'cargo_nome', 'total_realizado')
    list_filter = ('company', 'competencia', 'setor_nome')
    search_fields = ('cargo_nome', 'setor_nome')

# ==========================================
# CIRURGIA GERAL
# ==========================================
@admin.register(CirurgiaSetor)
class CirurgiaSetorAdmin(admin.ModelAdmin):
    list_display = ('name', 'company')
    list_filter = ('company',)
    search_fields = ('name',)

@admin.register(CirurgiaConfiguracao)
class CirurgiaConfiguracaoAdmin(admin.ModelAdmin):
    list_display = ('setor', 'cargo', 'qtd_dia', 'valor_plantao_dia', 'qtd_noite', 'valor_plantao_noite')
    list_filter = ('setor__company', 'setor')
    search_fields = ('cargo',)

@admin.register(CirurgiaLancamento)
class CirurgiaLancamentoAdmin(admin.ModelAdmin):
    list_display = ('competencia', 'company', 'setor_nome', 'cargo_nome', 'total_realizado')
    list_filter = ('company', 'competencia', 'setor_nome')
    search_fields = ('cargo_nome', 'setor_nome')

# ==========================================
# NEFROLOGIA
# ==========================================
@admin.register(NefrologiaConfiguracao)
class NefrologiaConfiguracaoAdmin(admin.ModelAdmin):
    list_display = ('nome_procedimento', 'company', 'valor_unitario', 'meta_mensal_qtd')
    list_filter = ('company',)
    search_fields = ('nome_procedimento',)

@admin.register(NefrologiaLancamento)
class NefrologiaLancamentoAdmin(admin.ModelAdmin):
    list_display = ('competencia', 'company', 'nome_procedimento', 'qtd_realizada', 'total_realizado')
    list_filter = ('company', 'competencia')
    search_fields = ('nome_procedimento',)

# ==========================================
# BUCOMAXILO
# ==========================================
@admin.register(BucomaxiloConfiguracao)
class BucomaxiloConfiguracaoAdmin(admin.ModelAdmin):
    list_display = ('nome_profissional', 'company', 'descricao_servico', 'valor_mensal')
    list_filter = ('company',)
    search_fields = ('nome_profissional', 'descricao_servico')

@admin.register(BucomaxiloLancamento)
class BucomaxiloLancamentoAdmin(admin.ModelAdmin):
    list_display = ('competencia', 'company', 'nome_profissional', 'valor_pagar')
    list_filter = ('company', 'competencia')
    search_fields = ('nome_profissional', 'descricao_servico')

# ==========================================
# RESIDÊNCIA
# ==========================================
@admin.register(ResidenciaConfiguracao)
class ResidenciaConfiguracaoAdmin(admin.ModelAdmin):
    list_display = ('nome_medico', 'company', 'valor_aula', 'meta_aulas')
    list_filter = ('company',)
    search_fields = ('nome_medico',)

@admin.register(ResidenciaLancamento)
class ResidenciaLancamentoAdmin(admin.ModelAdmin):
    list_display = ('competencia', 'company', 'nome_medico', 'qtd_aulas', 'total_realizado')
    list_filter = ('company', 'competencia')
    search_fields = ('nome_medico',)

# ==========================================
# COORDENAÇÃO
# ==========================================
@admin.register(CoordenacaoConfiguracao)
class CoordenacaoConfiguracaoAdmin(admin.ModelAdmin):
    list_display = ('nome_funcionario', 'company', 'matricula', 'setor', 'valor_mensal')
    list_filter = ('company', 'setor')
    search_fields = ('nome_funcionario', 'matricula')

@admin.register(CoordenacaoLancamento)
class CoordenacaoLancamentoAdmin(admin.ModelAdmin):
    list_display = ('competencia', 'company', 'nome_funcionario', 'setor', 'valor_pagar')
    list_filter = ('company', 'competencia', 'setor')
    search_fields = ('nome_funcionario', 'matricula')