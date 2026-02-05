from django.urls import path
from . import views

app_name = 'plantoes'

urlpatterns = [
    # Página principal de configurações
    path('configuracoes/', views.plantoes_settings, name='plantoes_settings'),

    # CRUD para Especialidade
    path('especialidades/nova/', views.EspecialidadeCreateView.as_view(), name='especialidade_create'),
    path('especialidades/<int:pk>/editar/', views.EspecialidadeUpdateView.as_view(), name='especialidade_update'),
    path('especialidades/<int:pk>/excluir/', views.EspecialidadeDeleteView.as_view(), name='especialidade_delete'),

    # CRUD para Turno
    path('turnos/novo/', views.TurnoCreateView.as_view(), name='turno_create'),
    path('turnos/<int:pk>/editar/', views.TurnoUpdateView.as_view(), name='turno_update'),
    path('turnos/<int:pk>/excluir/', views.TurnoDeleteView.as_view(), name='turno_delete'),

    # CRUD para Unidade de Assistência
    path('unidades/nova/', views.UnidadeAssistenciaCreateView.as_view(), name='unidade_create'),
    path('unidades/<int:pk>/editar/', views.UnidadeAssistenciaUpdateView.as_view(), name='unidade_update'),
    path('unidades/<int:pk>/excluir/', views.UnidadeAssistenciaDeleteView.as_view(), name='unidade_delete'),

    # CRUD para Orçamento Mensal de Plantão
    path('orcamento-mensal/', views.orcamento_mensal_view, name='orcamento_mensal'),

    # CRUD para Lançamento de Plantão
    path('lancamentos/', views.LancamentoPlantaoListView.as_view(), name='lancamento_list'),
    path('lancamentos/novo/', views.LancamentoPlantaoCreateView.as_view(), name='lancamento_create'),
    path('lancamentos/<int:pk>/editar/', views.LancamentoPlantaoUpdateView.as_view(), name='lancamento_update'),
    path('lancamentos/<int:pk>/excluir/', views.LancamentoPlantaoDeleteView.as_view(), name='lancamento_delete'),

    # Relatórios de Plantões
    path('quadro-de-plantoes/', views.plantoes_report_view, name='plantoes_report'),

    # EQUIPE DE TRANSPORTE
    path('transporte/', views.transporte_list_view, name='transporte_list'),
    path('transporte/novo/', views.TransporteCreateView.as_view(), name='transporte_create'),
    path('transporte/<int:pk>/editar/', views.TransporteUpdateView.as_view(), name='transporte_update'),
    path('transporte/<int:pk>/excluir/', views.TransporteDeleteView.as_view(), name='transporte_delete'),

    # URGÊNCIA E EMERGÊNCIA - CONFIGURAÇÕES
    path('urgencia/configuracoes/', views.urgencia_settings_view, name='urgencia_settings'),
    
    # Setores
    path('urgencia/setor/novo/', views.UrgenciaSetorCreateView.as_view(), name='urgencia_setor_create'),
    path('urgencia/setor/<int:pk>/editar/', views.UrgenciaSetorUpdateView.as_view(), name='urgencia_setor_update'),
    path('urgencia/setor/<int:pk>/excluir/', views.UrgenciaSetorDeleteView.as_view(), name='urgencia_setor_delete'),

    # Configurações (Gabaritos)
    path('urgencia/gabarito/novo/', views.UrgenciaConfigCreateView.as_view(), name='urgencia_config_create'),
    path('urgencia/gabarito/<int:pk>/editar/', views.UrgenciaConfigUpdateView.as_view(), name='urgencia_config_update'),
    path('urgencia/gabarito/<int:pk>/excluir/', views.UrgenciaConfigDeleteView.as_view(), name='urgencia_config_delete'),

    # URGÊNCIA - FOLHA MENSAL
    path('urgencia/folha/', views.urgencia_folha_view, name='urgencia_folha'),
]