from django.contrib import admin
from .models import Especialidade, Turno, UnidadeAssistencia, OrcamentoPlantao, LancamentoPlantao

@admin.register(Especialidade)
class EspecialidadeAdmin(admin.ModelAdmin):
    list_display = ('name', 'company')
    list_filter = ('company',)

@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ('name', 'company')
    list_filter = ('company',)

@admin.register(UnidadeAssistencia)
class UnidadeAssistenciaAdmin(admin.ModelAdmin):
    list_display = ('name', 'company')
    list_filter = ('company',)

@admin.register(OrcamentoPlantao)
class OrcamentoPlantaoAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'quantidade', 'tipo_plantao', 'valor_plantao', 'company')
    list_filter = ('company', 'especialidade', 'turno')

@admin.register(LancamentoPlantao)
class LancamentoPlantaoAdmin(admin.ModelAdmin):
    list_display = ('orcamento', 'date', 'valor_realizado')
    list_filter = ('orcamento__company', 'date')