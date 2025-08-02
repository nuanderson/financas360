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

    # CRUD para Orçamento de Plantão
    path('orcamentos/', views.OrcamentoPlantaoListView.as_view(), name='orcamento_list'),
    path('orcamentos/novo/', views.OrcamentoPlantaoCreateView.as_view(), name='orcamento_create'),
    path('orcamentos/<int:pk>/editar/', views.OrcamentoPlantaoUpdateView.as_view(), name='orcamento_update'),
    path('orcamentos/<int:pk>/excluir/', views.OrcamentoPlantaoDeleteView.as_view(), name='orcamento_delete'),
    path('lancamentos/', views.lancamento_plantao_view, name='lancamento_create'),
    path('quadro/', views.plantoes_budget_dashboard, name='plantoes_dashboard'),
]