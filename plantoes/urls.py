from django.urls import path
from . import views

app_name = 'plantoes'

urlpatterns = [
    
    # EQUIPE DE TRANSPORTE
    path('transporte/', views.transporte_list_view, name='transporte_list'),
    path('transporte/novo/', views.TransporteCreateView.as_view(), name='transporte_create'),
    path('transporte/<int:pk>/editar/', views.TransporteUpdateView.as_view(), name='transporte_update'),
    path('transporte/<int:pk>/excluir/', views.TransporteDeleteView.as_view(), name='transporte_delete'),

    # ==========================================
    # URGÊNCIA E EMERGÊNCIA
    # ==========================================
    # Matriz (Listagem)
    path('urgencia/configuracoes/', views.urgencia_settings_view, name='urgencia_settings'),
    
    # CRUD Configuração (Agora é o cadastro principal)
    path('urgencia/novo/', views.UrgenciaConfigCreateView.as_view(), name='urgencia_config_create'),
    path('urgencia/<int:pk>/editar/', views.UrgenciaConfigUpdateView.as_view(), name='urgencia_config_update'),
    path('urgencia/<int:pk>/excluir/', views.UrgenciaConfigDeleteView.as_view(), name='urgencia_config_delete'),

    path('urgencia/setor/novo/', views.UrgenciaSetorCreateView.as_view(), name='urgencia_setor_create'),
    path('urgencia/setor/<int:pk>/editar/', views.UrgenciaSetorUpdateView.as_view(), name='urgencia_setor_update'),
    path('urgencia/setor/<int:pk>/excluir/', views.UrgenciaSetorDeleteView.as_view(), name='urgencia_setor_delete'),

    # Configurações (Gabaritos)
    path('urgencia/gabarito/novo/', views.UrgenciaConfigCreateView.as_view(), name='urgencia_config_create'),
    path('urgencia/gabarito/<int:pk>/editar/', views.UrgenciaConfigUpdateView.as_view(), name='urgencia_config_update'),
    path('urgencia/gabarito/<int:pk>/excluir/', views.UrgenciaConfigDeleteView.as_view(), name='urgencia_config_delete'),

    # URGÊNCIA - FOLHA MENSAL
    path('urgencia/folha/', views.urgencia_folha_view, name='urgencia_folha'),

    # ==========================================
    # CIRURGIA GERAL
    # ==========================================
    
    # 1. Configurações (Matriz)
    path('cirurgia/configuracoes/', views.cirurgia_settings_view, name='cirurgia_settings'),
    
    # Setores
    path('cirurgia/setor/novo/', views.CirurgiaSetorCreateView.as_view(), name='cirurgia_setor_create'),
    path('cirurgia/setor/<int:pk>/editar/', views.CirurgiaSetorUpdateView.as_view(), name='cirurgia_setor_update'),
    path('cirurgia/setor/<int:pk>/excluir/', views.CirurgiaSetorDeleteView.as_view(), name='cirurgia_setor_delete'),

    # Cargos/Gabarito
    path('cirurgia/gabarito/novo/', views.CirurgiaConfigCreateView.as_view(), name='cirurgia_config_create'),
    path('cirurgia/gabarito/<int:pk>/editar/', views.CirurgiaConfigUpdateView.as_view(), name='cirurgia_config_update'),
    path('cirurgia/gabarito/<int:pk>/excluir/', views.CirurgiaConfigDeleteView.as_view(), name='cirurgia_config_delete'),

    # 2. Folha Mensal
    path('cirurgia/folha/', views.cirurgia_folha_view, name='cirurgia_folha'),

    # ==========================================
    # NEFROLOGIA
    # ==========================================
    
    # Configurações
    path('nefrologia/configuracoes/', views.nefrologia_settings_view, name='nefrologia_settings'),
    path('nefrologia/novo/', views.NefrologiaConfigCreateView.as_view(), name='nefrologia_config_create'),
    path('nefrologia/<int:pk>/editar/', views.NefrologiaConfigUpdateView.as_view(), name='nefrologia_config_update'),
    path('nefrologia/<int:pk>/excluir/', views.NefrologiaConfigDeleteView.as_view(), name='nefrologia_config_delete'),

    # Folha Mensal
    path('nefrologia/folha/', views.nefrologia_folha_view, name='nefrologia_folha'),

    # ==========================================
    # BUCOMAXILO
    # ==========================================
    path('bucomaxilo/configuracoes/', views.bucomaxilo_settings_view, name='bucomaxilo_settings'),
    path('bucomaxilo/novo/', views.BucomaxiloConfigCreateView.as_view(), name='bucomaxilo_config_create'),
    path('bucomaxilo/<int:pk>/editar/', views.BucomaxiloConfigUpdateView.as_view(), name='bucomaxilo_config_update'),
    path('bucomaxilo/<int:pk>/excluir/', views.BucomaxiloConfigDeleteView.as_view(), name='bucomaxilo_config_delete'),
    
    path('bucomaxilo/folha/', views.bucomaxilo_folha_view, name='bucomaxilo_folha'),

    # ==========================================
    # RESIDÊNCIA (AULAS)
    # ==========================================
    path('residencia/configuracoes/', views.residencia_settings_view, name='residencia_settings'),
    path('residencia/novo/', views.ResidenciaConfigCreateView.as_view(), name='residencia_config_create'),
    path('residencia/<int:pk>/editar/', views.ResidenciaConfigUpdateView.as_view(), name='residencia_config_update'),
    path('residencia/<int:pk>/excluir/', views.ResidenciaConfigDeleteView.as_view(), name='residencia_config_delete'),
    
    path('residencia/folha/', views.residencia_folha_view, name='residencia_folha'),

    # ==========================================
    # COORDENAÇÕES
    # ==========================================
    path('coordenacao/configuracoes/', views.coordenacao_settings_view, name='coordenacao_settings'),
    path('coordenacao/novo/', views.CoordenacaoConfigCreateView.as_view(), name='coordenacao_config_create'),
    path('coordenacao/<int:pk>/editar/', views.CoordenacaoConfigUpdateView.as_view(), name='coordenacao_config_update'),
    path('coordenacao/<int:pk>/excluir/', views.CoordenacaoConfigDeleteView.as_view(), name='coordenacao_config_delete'),
    
    path('coordenacao/folha/', views.coordenacao_folha_view, name='coordenacao_folha'),

    # ==========================================
    # AMBULATÓRIO
    # ==========================================
    path('ambulatorio/configuracoes/', views.ambulatorio_settings_view, name='ambulatorio_settings'),
    path('ambulatorio/novo/', views.AmbulatorioConfigCreateView.as_view(), name='ambulatorio_config_create'),
    path('ambulatorio/<int:pk>/editar/', views.AmbulatorioConfigUpdateView.as_view(), name='ambulatorio_config_update'),
    path('ambulatorio/<int:pk>/excluir/', views.AmbulatorioConfigDeleteView.as_view(), name='ambulatorio_config_delete'),
    path('ambulatorio/folha/', views.ambulatorio_folha_view, name='ambulatorio_folha'),

    # ==========================================
    # ULTRASSONOGRAFIA
    # ==========================================
    path('ultrassonografia/configuracoes/', views.ultrassonografia_settings_view, name='ultrassonografia_settings'),
    path('ultrassonografia/novo/', views.UltrassonografiaConfigCreateView.as_view(), name='ultrassonografia_config_create'),
    path('ultrassonografia/<int:pk>/editar/', views.UltrassonografiaConfigUpdateView.as_view(), name='ultrassonografia_config_update'),
    path('ultrassonografia/<int:pk>/excluir/', views.UltrassonografiaConfigDeleteView.as_view(), name='ultrassonografia_config_delete'),
    path('ultrassonografia/folha/', views.ultrassonografia_folha_view, name='ultrassonografia_folha'),

    # ==========================================
    # ENDOSCOPIA
    # ==========================================
    path('endoscopia/configuracoes/', views.endoscopia_settings_view, name='endoscopia_settings'),
    path('endoscopia/novo/', views.EndoscopiaConfigCreateView.as_view(), name='endoscopia_config_create'),
    path('endoscopia/<int:pk>/editar/', views.EndoscopiaConfigUpdateView.as_view(), name='endoscopia_config_update'),
    path('endoscopia/<int:pk>/excluir/', views.EndoscopiaConfigDeleteView.as_view(), name='endoscopia_config_delete'),
    path('endoscopia/folha/', views.endoscopia_folha_view, name='endoscopia_folha'),

    # ==========================================
    # ANESTESIOLOGIA
    # ==========================================
    path('anestesiologia/configuracoes/', views.anestesiologia_settings_view, name='anestesiologia_settings'),
    path('anestesiologia/novo/', views.AnestesiologiaConfigCreateView.as_view(), name='anestesiologia_config_create'),
    path('anestesiologia/<int:pk>/editar/', views.AnestesiologiaConfigUpdateView.as_view(), name='anestesiologia_config_update'),
    path('anestesiologia/<int:pk>/excluir/', views.AnestesiologiaConfigDeleteView.as_view(), name='anestesiologia_config_delete'),
    path('anestesiologia/folha/', views.anestesiologia_folha_view, name='anestesiologia_folha'),

    # ==========================================
    # COMISSÕES
    # ==========================================
    path('comissoes/configuracoes/', views.comissao_settings_view, name='comissao_settings'),
    path('comissoes/novo/', views.ComissaoConfigCreateView.as_view(), name='comissao_config_create'),
    path('comissoes/<int:pk>/editar/', views.ComissaoConfigUpdateView.as_view(), name='comissao_config_update'),
    path('comissoes/<int:pk>/excluir/', views.ComissaoConfigDeleteView.as_view(), name='comissao_config_delete'),
    path('comissoes/folha/', views.comissao_folha_view, name='comissao_folha'),

    # ==========================================
    # COOPERATIVAS
    # ==========================================
    path('cooperativas/configuracoes/', views.cooperativa_settings_view, name='cooperativa_settings'),
    path('cooperativas/novo/', views.CooperativaConfigCreateView.as_view(), name='cooperativa_config_create'),
    path('cooperativas/<int:pk>/editar/', views.CooperativaConfigUpdateView.as_view(), name='cooperativa_config_update'),
    path('cooperativas/<int:pk>/excluir/', views.CooperativaConfigDeleteView.as_view(), name='cooperativa_config_delete'),
    path('cooperativas/folha/', views.cooperativa_folha_view, name='cooperativa_folha'),

    # DASHBOARD (CONSOLIDAÇÃO)
    path('', views.plantoes_dashboard_view, name='dashboard'),

    # Relatório Anual
    path('relatorio-anual/', views.plantoes_annual_report_view, name='annual_report'),
]