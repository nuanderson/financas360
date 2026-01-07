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
]