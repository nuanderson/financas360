import locale
import calendar
from django.core.mail import send_mail
from decimal import Decimal
from django.db.models import Sum, F, Avg, FloatField, DecimalField
from django.db.models.functions import Cast
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.contrib import messages
from django.forms import modelformset_factory, formset_factory
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from django.conf import settings
from decimal import Decimal

from .models import (
    TransporteLancamento,
    UrgenciaSetor, UrgenciaConfiguracao, UrgenciaLancamento,
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
from .forms import (
    TransporteForm,
    UrgenciaSetorForm, UrgenciaConfiguracaoForm, UrgenciaLancamentoForm,
    CirurgiaConfiguracaoForm, CirurgiaSetorForm, CirurgiaLancamentoForm,
    NefrologiaConfigForm, NefrologiaLancamentoForm,
    BucomaxiloConfigForm, BucomaxiloLancamentoForm,
    ResidenciaConfigForm, ResidenciaLancamentoForm,
    CoordenacaoConfigForm, CoordenacaoLancamentoForm,
    AmbulatorioConfigForm, AmbulatorioLancamentoForm,
    UltrassonografiaConfigForm, UltrassonografiaLancamentoForm,
    EndoscopiaConfigForm, EndoscopiaLancamentoForm,
    AnestesiologiaConfigForm, AnestesiologiaLancamentoForm,
    ComissaoConfigForm, ComissaoLancamentoForm,
    CooperativaConfigForm, CooperativaLancamentoForm,
)

from core.models import Company

@login_required
def transporte_list_view(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return redirect('core:company_list') 
    
    # 1. Listagem Geral
    lancamentos = TransporteLancamento.objects.filter(
        company_id=active_company_id
    ).order_by('-competencia')

    # 2. Dados de Data
    today = timezone.now().date()
    current_year = today.year
    last_year = current_year - 1
    
    # --- CÁLCULO DAS MÉDIAS (12 MESES) ---
    last_12_months_date = today.replace(day=1) - relativedelta(months=12)
    historico_recente = lancamentos.filter(competencia__gte=last_12_months_date)
    
    media_quantidade = 0
    media_valor_total = 0
    
    if historico_recente.exists():
        avg_qty = historico_recente.aggregate(media=Avg('quantidade_viagens'))['media']
        media_quantidade = round(avg_qty) if avg_qty else 0
        
        avg_val = historico_recente.annotate(
            total_linha=F('quantidade_viagens') * F('valor_viagem')
        ).aggregate(media=Avg('total_linha'))['media']
        media_valor_total = avg_val if avg_val else 0

    # --- NOVO: CÁLCULO DOS TOTAIS ANUAIS ---
    
    # Total Ano Atual (Ex: 2026)
    total_ano_atual = lancamentos.filter(competencia__year=current_year).annotate(
        total_linha=F('quantidade_viagens') * F('valor_viagem')
    ).aggregate(soma=Sum('total_linha'))['soma'] or 0

    # Total Ano Anterior (Ex: 2025)
    total_ano_anterior = lancamentos.filter(competencia__year=last_year).annotate(
        total_linha=F('quantidade_viagens') * F('valor_viagem')
    ).aggregate(soma=Sum('total_linha'))['soma'] or 0

    context = {
        'lancamentos': lancamentos,
        'media_quantidade': media_quantidade,
        'media_valor_total': media_valor_total,
        # Novas variáveis
        'total_ano_atual': total_ano_atual,
        'total_ano_anterior': total_ano_anterior,
        'current_year': current_year,
        'last_year': last_year,
    }
    return render(request, 'plantoes/transporte_list.html', context)

# CRUD Básico
class TransporteCreateView(LoginRequiredMixin, CreateView):
    model = TransporteLancamento
    form_class = TransporteForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:transporte_list')

    def form_valid(self, form):
        active_company_id = self.request.session.get('active_company_id')
        form.instance.company_id = active_company_id
        # Força dia 1 para padronizar competência
        form.instance.competencia = form.instance.competencia.replace(day=1)
        return super().form_valid(form)

class TransporteUpdateView(LoginRequiredMixin, UpdateView):
    model = TransporteLancamento
    form_class = TransporteForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:transporte_list')
    
    def get_queryset(self):
        # Segurança: só edita da empresa ativa
        return super().get_queryset().filter(company_id=self.request.session.get('active_company_id'))

class TransporteDeleteView(LoginRequiredMixin, DeleteView):
    model = TransporteLancamento
    template_name = 'plantoes/generic_confirm_delete.html'
    success_url = reverse_lazy('plantoes:transporte_list')

# --- CONFIGURAÇÕES DE URGÊNCIA (GABARITO) ---

# ==========================================
# LISTAGEM (MATRIZ)
# ==========================================
@login_required
def urgencia_settings_view(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return redirect('core:company_list')
    
    # Voltamos a buscar os SETORES (Igual no módulo de Cirurgia!)
    setores = UrgenciaSetor.objects.filter(
        company_id=active_company_id
    ).prefetch_related('configuracoes')
    
    context = {
        'setores': setores,
    }
    return render(request, 'plantoes/urgencia_settings.html', context)

# ==========================================
# CRUD SETOR DE URGÊNCIA
# ==========================================
class UrgenciaSetorCreateView(LoginRequiredMixin, CreateView):
    model = UrgenciaSetor
    form_class = UrgenciaSetorForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:urgencia_settings')

    def form_valid(self, form):
        form.instance.company_id = self.request.session.get('active_company_id')
        return super().form_valid(form)

class UrgenciaSetorUpdateView(LoginRequiredMixin, UpdateView):
    model = UrgenciaSetor
    form_class = UrgenciaSetorForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:urgencia_settings')
    
    def get_queryset(self):
        return super().get_queryset().filter(company_id=self.request.session.get('active_company_id'))

class UrgenciaSetorDeleteView(LoginRequiredMixin, DeleteView):
    model = UrgenciaSetor
    template_name = 'plantoes/generic_confirm_delete.html'
    success_url = reverse_lazy('plantoes:urgencia_settings')
    
    def get_queryset(self):
        return super().get_queryset().filter(company_id=self.request.session.get('active_company_id'))

# ==========================================
# CRUD CONFIGURAÇÃO (GABARITO)
# ==========================================

class UrgenciaConfigCreateView(LoginRequiredMixin, CreateView):
    model = UrgenciaConfiguracao
    form_class = UrgenciaConfiguracaoForm
    template_name = 'plantoes/urgencia_config_form.html'
    success_url = reverse_lazy('plantoes:urgencia_settings')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = get_object_or_404(Company, pk=self.request.session.get('active_company_id'))
        return kwargs

class UrgenciaConfigUpdateView(LoginRequiredMixin, UpdateView):
    model = UrgenciaConfiguracao
    form_class = UrgenciaConfiguracaoForm
    template_name = 'plantoes/urgencia_config_form.html'
    success_url = reverse_lazy('plantoes:urgencia_settings')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = get_object_or_404(Company, pk=self.request.session.get('active_company_id'))
        return kwargs

class UrgenciaConfigDeleteView(LoginRequiredMixin, DeleteView):
    model = UrgenciaConfiguracao
    template_name = 'plantoes/generic_confirm_delete.html'
    success_url = reverse_lazy('plantoes:urgencia_settings')
    
    def get_queryset(self):
        # CORREÇÃO AQUI: setor__company_id
        return super().get_queryset().filter(setor__company_id=self.request.session.get('active_company_id'))

# LANÇAMENTO MENSAL (FOLHA DE URGÊNCIA)

@login_required
def urgencia_folha_view(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return redirect('core:company_list')

    # 1. Filtro de Data
    today = timezone.now().date()
    month_str = request.GET.get('month', today.strftime('%Y-%m')) 
    try:
        competencia = datetime.strptime(f"{month_str}-01", "%Y-%m-%d").date()
    except ValueError:
        competencia = today.replace(day=1)

    # 2. Calcula dias do mês (Ex: Fev 2026 = 28 dias)
    _, dias_no_mes_atual = calendar.monthrange(competencia.year, competencia.month)

    queryset = UrgenciaLancamento.objects.filter(
        company_id=active_company_id,
        competencia=competencia
    ).order_by('setor_nome', 'cargo_nome')

    # --- AÇÃO: LIMPAR ---
    if request.method == 'POST' and 'limpar_folha' in request.POST:
        queryset.delete()
        messages.warning(request, "Folha limpa com sucesso!")
        return redirect(f"{request.path}?month={month_str}")

    # --- AÇÃO: GERAR FOLHA (Criação) ---
    if request.method == 'POST' and 'gerar_folha' in request.POST:
        configs = UrgenciaConfiguracao.objects.filter(setor__company_id=active_company_id)
        existentes = set((l.setor_nome, l.cargo_nome) for l in queryset)
        
        if not configs.exists():
            messages.error(request, "Nenhuma configuração encontrada.")
        else:
            novos = []
            for cfg in configs:
                if (cfg.setor.name, cfg.cargo) not in existentes:
                    novos.append(UrgenciaLancamento(
                        company_id=active_company_id,
                        competencia=competencia,
                        setor_nome=cfg.setor.name,
                        cargo_nome=cfg.cargo,
                        # AQUI ESTAVA O ERRO! Ajustado para os nomes novos
                        qtd_dia=cfg.qtd_dia,
                        qtd_noite=cfg.qtd_noite,
                        valor_plantao_dia=cfg.valor_plantao_dia,
                        valor_plantao_noite=cfg.valor_plantao_noite,
                        dias_mes=dias_no_mes_atual,
                        valor_pega_plantao=0,
                        valor_efetivo=0
                    ))
            if novos:
                UrgenciaLancamento.objects.bulk_create(novos)
                messages.success(request, "Folha gerada com sucesso!")
            return redirect(f"{request.path}?month={month_str}")

    # --- AÇÃO: SINCRONIZAR (Correção dos Dias Vazios) ---
    if request.method == 'POST' and 'atualizar_valores' in request.POST:
        configs = UrgenciaConfiguracao.objects.filter(setor__company_id=active_company_id)
        config_map = {(c.setor.name, c.cargo): c for c in configs}
        
        # 1. Atualiza itens existentes
        for item in queryset:
            key = (item.setor_nome, item.cargo_nome)
            item.dias_mes = dias_no_mes_atual 
            
            if key in config_map:
                cfg = config_map[key]
                # AQUI ESTAVA O ERRO TAMBÉM! Ajustado para os nomes novos
                item.qtd_dia = cfg.qtd_dia
                item.qtd_noite = cfg.qtd_noite
                item.valor_plantao_dia = cfg.valor_plantao_dia
                item.valor_plantao_noite = cfg.valor_plantao_noite
            item.save()
        
        # 2. Adiciona novos (se houver)
        existentes_agora = set((l.setor_nome, l.cargo_nome) for l in queryset)
        novos = []
        for cfg in configs:
            if (cfg.setor.name, cfg.cargo) not in existentes_agora:
                novos.append(UrgenciaLancamento(
                    company_id=active_company_id,
                    competencia=competencia,
                    setor_nome=cfg.setor.name,
                    cargo_nome=cfg.cargo,
                    qtd_dia=cfg.qtd_dia,
                    qtd_noite=cfg.qtd_noite,
                    valor_plantao_dia=cfg.valor_plantao_dia,
                    valor_plantao_noite=cfg.valor_plantao_noite,
                    dias_mes=dias_no_mes_atual,
                    valor_pega_plantao=0, 
                    valor_efetivo=0
                ))
        if novos:
            UrgenciaLancamento.objects.bulk_create(novos)
            
        messages.success(request, "Sincronização concluída! Dias e valores atualizados.")
        return redirect(f"{request.path}?month={month_str}")

    # --- AÇÃO: SALVAR GRID ---
    LancamentoFormSet = modelformset_factory(UrgenciaLancamento, form=UrgenciaLancamentoForm, extra=0)
    
    if request.method == 'POST' and 'salvar_grid' in request.POST:
        formset = LancamentoFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Lançamentos e Observações salvos com sucesso!")
            return redirect(f"{request.path}?month={month_str}")
        else:
            messages.error(request, "Erro ao salvar. Verifique se os números estão corretos.")
    else:
        formset = LancamentoFormSet(queryset=queryset)

    # Totais
    total_orcado = sum(item.total_escala_calculada for item in queryset)
    total_realizado = sum(item.total_realizado for item in queryset)
    total_saldo = sum(item.saldo_orcamentario for item in queryset)
    total_efetivo = sum(item.valor_efetivo for item in queryset)
    total_pega_plantao = sum(item.valor_pega_plantao for item in queryset)

    context = {
        'formset': formset,
        'month_str': month_str,
        'competencia': competencia,
        'tem_dados': queryset.exists(),
        'total_orcado': total_orcado,
        'total_realizado': total_realizado,
        'total_saldo': total_saldo,
        'total_efetivo': total_efetivo,
        'total_pega_plantao': total_pega_plantao,
    }
    return render(request, 'plantoes/urgencia_folha.html', context)

# ==========================================
# MÓDULO: CIRURGIA GERAL
# ==========================================

# --- 1. CONFIGURAÇÕES (MATRIZ) ---

@login_required
def cirurgia_settings_view(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return redirect('core:company_list')
    
    setores = CirurgiaSetor.objects.filter(company_id=active_company_id).prefetch_related('configuracoes')
    
    context = {'setores': setores}
    return render(request, 'plantoes/cirurgia_settings.html', context)

# CRUD SETOR
class CirurgiaSetorCreateView(LoginRequiredMixin, CreateView):
    model = CirurgiaSetor
    form_class = CirurgiaSetorForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:cirurgia_settings')

    def form_valid(self, form):
        form.instance.company_id = self.request.session.get('active_company_id')
        return super().form_valid(form)

class CirurgiaSetorUpdateView(LoginRequiredMixin, UpdateView):
    model = CirurgiaSetor
    form_class = CirurgiaSetorForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:cirurgia_settings')
    
    def get_queryset(self):
        return super().get_queryset().filter(company_id=self.request.session.get('active_company_id'))

class CirurgiaSetorDeleteView(LoginRequiredMixin, DeleteView):
    model = CirurgiaSetor
    template_name = 'plantoes/generic_confirm_delete.html'
    success_url = reverse_lazy('plantoes:cirurgia_settings')
    
    def get_queryset(self):
        return super().get_queryset().filter(company_id=self.request.session.get('active_company_id'))

# CRUD CONFIGURAÇÃO (GABARITO)
class CirurgiaConfigCreateView(LoginRequiredMixin, CreateView):
    model = CirurgiaConfiguracao
    form_class = CirurgiaConfiguracaoForm
    template_name = 'plantoes/cirurgia_config_form.html'
    success_url = reverse_lazy('plantoes:cirurgia_settings')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = get_object_or_404(Company, pk=self.request.session.get('active_company_id'))
        return kwargs

class CirurgiaConfigUpdateView(LoginRequiredMixin, UpdateView):
    model = CirurgiaConfiguracao
    form_class = CirurgiaConfiguracaoForm
    template_name = 'plantoes/cirurgia_config_form.html'
    success_url = reverse_lazy('plantoes:cirurgia_settings')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = get_object_or_404(Company, pk=self.request.session.get('active_company_id'))
        return kwargs
        
class CirurgiaConfigDeleteView(LoginRequiredMixin, DeleteView):
    model = CirurgiaConfiguracao
    template_name = 'plantoes/generic_confirm_delete.html'
    success_url = reverse_lazy('plantoes:cirurgia_settings')


# --- 2. FOLHA MENSAL (CONTROLADORIA) ---

@login_required
def cirurgia_folha_view(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return redirect('core:company_list')

    # Filtros de Data
    today = timezone.now().date()
    month_str = request.GET.get('month', today.strftime('%Y-%m')) 
    try:
        competencia = datetime.strptime(f"{month_str}-01", "%Y-%m-%d").date()
    except ValueError:
        competencia = today.replace(day=1)

    # Cálculo dias do mês
    _, dias_no_mes_atual = calendar.monthrange(competencia.year, competencia.month)

    # Queryset
    queryset = CirurgiaLancamento.objects.filter(
        company_id=active_company_id,
        competencia=competencia
    ).order_by('setor_nome', 'cargo_nome')

    # AÇÃO: SINCRONIZAR
    if request.method == 'POST' and 'atualizar_valores' in request.POST:
        configs = CirurgiaConfiguracao.objects.filter(setor__company_id=active_company_id)
        config_map = {(c.setor.name, c.cargo): c for c in configs}
        
        count = 0
        for item in queryset:
            cfg = config_map.get((item.setor_nome, item.cargo_nome))
            if cfg:
                item.qtd_dia = cfg.qtd_dia
                item.valor_plantao_dia = cfg.valor_plantao_dia
                item.qtd_noite = cfg.qtd_noite
                item.valor_plantao_noite = cfg.valor_plantao_noite
                item.dias_mes = dias_no_mes_atual # Atualiza dias do mês
                item.save()
                count += 1
        messages.success(request, f"{count} itens sincronizados com a Matriz!")
        return redirect(f"{request.path}?month={month_str}")

    # AÇÃO: GERAR FOLHA
    if request.method == 'POST' and 'gerar_folha' in request.POST:
        configs = CirurgiaConfiguracao.objects.filter(setor__company_id=active_company_id)
        if not configs.exists():
            messages.error(request, "Cadastre a Matriz de Cirurgia primeiro!")
        else:
            novos = []
            for cfg in configs:
                if not queryset.filter(setor_nome=cfg.setor.name, cargo_nome=cfg.cargo).exists():
                    novos.append(CirurgiaLancamento(
                        company_id=active_company_id,
                        competencia=competencia,
                        setor_nome=cfg.setor.name,
                        cargo_nome=cfg.cargo,
                        qtd_dia=cfg.qtd_dia,
                        valor_plantao_dia=cfg.valor_plantao_dia,
                        qtd_noite=cfg.qtd_noite,
                        valor_plantao_noite=cfg.valor_plantao_noite,
                        dias_mes=dias_no_mes_atual
                    ))
            if novos:
                CirurgiaLancamento.objects.bulk_create(novos)
                messages.success(request, "Folha de Cirurgia gerada!")
            return redirect(f"{request.path}?month={month_str}")

    # AÇÃO: SALVAR GRID
    LancamentoFormSet = modelformset_factory(CirurgiaLancamento, form=CirurgiaLancamentoForm, extra=0)
    if request.method == 'POST' and 'salvar_grid' in request.POST:
        formset = LancamentoFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Alterações salvas!")
            return redirect(f"{request.path}?month={month_str}")
    else:
        formset = LancamentoFormSet(queryset=queryset)

    # CÁLCULOS CONTROLADORIA
    total_orcado = sum(item.total_escala_calculada for item in queryset)
    total_realizado = sum(item.total_realizado for item in queryset)
    total_saldo = sum(item.saldo_orcamentario for item in queryset)
    total_efetivo = sum(item.valor_efetivo for item in queryset)
    total_pega_plantao = sum(item.valor_pega_plantao for item in queryset)

    context = {
        'formset': formset,
        'month_str': month_str,
        'competencia': competencia,
        'tem_dados': queryset.exists(),
        # Cards
        'total_orcado': total_orcado,
        'total_realizado': total_realizado,
        'total_saldo': total_saldo,
        'total_efetivo': total_efetivo,
        'total_pega_plantao': total_pega_plantao,
    }
    return render(request, 'plantoes/cirurgia_folha.html', context)

# ==========================================
# MÓDULO: NEFROLOGIA (PRODUÇÃO)
# ==========================================

# --- 1. CONFIGURAÇÕES (TABELA DE PREÇOS) ---

@login_required
def nefrologia_settings_view(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return redirect('core:company_list')
    
    # Lista todos os procedimentos cadastrados
    configs = NefrologiaConfiguracao.objects.filter(company_id=active_company_id)
    
    context = {'configs': configs}
    return render(request, 'plantoes/nefrologia_settings.html', context)

class NefrologiaConfigCreateView(LoginRequiredMixin, CreateView):
    model = NefrologiaConfiguracao
    form_class = NefrologiaConfigForm
    template_name = 'plantoes/generic_form.html' # Podemos reusar o genérico ou criar um específico
    success_url = reverse_lazy('plantoes:nefrologia_settings')

    def form_valid(self, form):
        form.instance.company_id = self.request.session.get('active_company_id')
        return super().form_valid(form)

class NefrologiaConfigUpdateView(LoginRequiredMixin, UpdateView):
    model = NefrologiaConfiguracao
    form_class = NefrologiaConfigForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:nefrologia_settings')
    
    def get_queryset(self):
        return super().get_queryset().filter(company_id=self.request.session.get('active_company_id'))

class NefrologiaConfigDeleteView(LoginRequiredMixin, DeleteView):
    model = NefrologiaConfiguracao
    template_name = 'plantoes/generic_confirm_delete.html'
    success_url = reverse_lazy('plantoes:nefrologia_settings')
    
    def get_queryset(self):
        return super().get_queryset().filter(company_id=self.request.session.get('active_company_id'))


# --- 2. FOLHA MENSAL (PRODUÇÃO) ---

@login_required
def nefrologia_folha_view(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return redirect('core:company_list')

    # Filtros de Data
    today = timezone.now().date()
    month_str = request.GET.get('month', today.strftime('%Y-%m')) 
    try:
        competencia = datetime.strptime(f"{month_str}-01", "%Y-%m-%d").date()
    except ValueError:
        competencia = today.replace(day=1)

    queryset = NefrologiaLancamento.objects.filter(
        company_id=active_company_id,
        competencia=competencia
    ).order_by('nome_procedimento')

    # AÇÃO: GERAR FOLHA (Copia a Tabela de Preços para o Mês)
    if request.method == 'POST' and 'gerar_folha' in request.POST:
        configs = NefrologiaConfiguracao.objects.filter(company_id=active_company_id)
        if not configs.exists():
            messages.error(request, "Cadastre a Tabela de Preços da Nefrologia primeiro!")
        else:
            novos = []
            for cfg in configs:
                # Verifica se já existe para não duplicar
                if not queryset.filter(nome_procedimento=cfg.nome_procedimento).exists():
                    novos.append(NefrologiaLancamento(
                        company_id=active_company_id,
                        competencia=competencia,
                        nome_procedimento=cfg.nome_procedimento,
                        valor_unitario=cfg.valor_unitario,
                        meta_qtd=cfg.meta_mensal_qtd,
                        qtd_realizada=0 # Começa zerado para o usuário preencher
                    ))
            if novos:
                NefrologiaLancamento.objects.bulk_create(novos)
                messages.success(request, "Folha de Produção gerada!")
            return redirect(f"{request.path}?month={month_str}")

    # AÇÃO: SINCRONIZAR (Atualiza preços/metas mas mantém a produção lançada)
    if request.method == 'POST' and 'atualizar_valores' in request.POST:
        configs = NefrologiaConfiguracao.objects.filter(company_id=active_company_id)
        config_map = {c.nome_procedimento: c for c in configs}
        
        count = 0
        for item in queryset:
            cfg = config_map.get(item.nome_procedimento)
            if cfg:
                item.valor_unitario = cfg.valor_unitario
                item.meta_qtd = cfg.meta_mensal_qtd
                item.save()
                count += 1
        messages.success(request, f"{count} itens atualizados com a tabela de preços vigente!")
        return redirect(f"{request.path}?month={month_str}")

    # AÇÃO: SALVAR GRID
    LancamentoFormSet = modelformset_factory(NefrologiaLancamento, form=NefrologiaLancamentoForm, extra=0)
    if request.method == 'POST' and 'salvar_grid' in request.POST:
        formset = LancamentoFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Produção salva com sucesso!")
            return redirect(f"{request.path}?month={month_str}")
    else:
        formset = LancamentoFormSet(queryset=queryset)

    # CÁLCULOS (TOTAIS)
    total_orcado = sum(item.total_orcado for item in queryset)
    total_realizado = sum(item.total_realizado for item in queryset)
    total_saldo = sum(item.saldo_orcamentario for item in queryset)

    context = {
        'formset': formset,
        'month_str': month_str,
        'competencia': competencia,
        'tem_dados': queryset.exists(),
        'total_orcado': total_orcado,
        'total_realizado': total_realizado,
        'total_saldo': total_saldo,
    }
    return render(request, 'plantoes/nefrologia_folha.html', context)

# ==========================================
# MÓDULO: BUCOMAXILO (CONTRATOS)
# ==========================================

# --- 1. CONFIGURAÇÕES (CONTRATOS) ---

@login_required
def bucomaxilo_settings_view(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return redirect('core:company_list')
    
    configs = BucomaxiloConfiguracao.objects.filter(company_id=active_company_id)
    return render(request, 'plantoes/bucomaxilo_settings.html', {'configs': configs})

class BucomaxiloConfigCreateView(LoginRequiredMixin, CreateView):
    model = BucomaxiloConfiguracao
    form_class = BucomaxiloConfigForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:bucomaxilo_settings')

    def form_valid(self, form):
        form.instance.company_id = self.request.session.get('active_company_id')
        return super().form_valid(form)

class BucomaxiloConfigUpdateView(LoginRequiredMixin, UpdateView):
    model = BucomaxiloConfiguracao
    form_class = BucomaxiloConfigForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:bucomaxilo_settings')
    
    def get_queryset(self):
        return super().get_queryset().filter(company_id=self.request.session.get('active_company_id'))

class BucomaxiloConfigDeleteView(LoginRequiredMixin, DeleteView):
    model = BucomaxiloConfiguracao
    template_name = 'plantoes/generic_confirm_delete.html'
    success_url = reverse_lazy('plantoes:bucomaxilo_settings')
    
    def get_queryset(self):
        return super().get_queryset().filter(company_id=self.request.session.get('active_company_id'))


# --- 2. FOLHA MENSAL (PAGAMENTOS) ---

@login_required
def bucomaxilo_folha_view(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return redirect('core:company_list')

    # Filtros de Data
    today = timezone.now().date()
    month_str = request.GET.get('month', today.strftime('%Y-%m')) 
    try:
        competencia = datetime.strptime(f"{month_str}-01", "%Y-%m-%d").date()
    except ValueError:
        competencia = today.replace(day=1)

    # Dias no Mês (para cálculo pro-rata se necessário)
    _, dias_no_mes = calendar.monthrange(competencia.year, competencia.month)

    queryset = BucomaxiloLancamento.objects.filter(
        company_id=active_company_id,
        competencia=competencia
    ).order_by('nome_profissional')

    # AÇÃO: GERAR FOLHA (Copia Contratos)
    if request.method == 'POST' and 'gerar_folha' in request.POST:
        configs = BucomaxiloConfiguracao.objects.filter(company_id=active_company_id)
        if not configs.exists():
            messages.error(request, "Cadastre os Contratos/Profissionais primeiro!")
        else:
            novos = []
            for cfg in configs:
                if not queryset.filter(nome_profissional=cfg.nome_profissional).exists():
                    novos.append(BucomaxiloLancamento(
                        company_id=active_company_id,
                        competencia=competencia,
                        nome_profissional=cfg.nome_profissional,
                        descricao_servico=cfg.descricao_servico,
                        valor_contrato=cfg.valor_mensal,
                        dias_no_mes=dias_no_mes,
                        dias_trabalhados=dias_no_mes, # Assume mês cheio por padrão
                        valor_pagar=cfg.valor_mensal # Paga integral por padrão
                    ))
            if novos:
                BucomaxiloLancamento.objects.bulk_create(novos)
                messages.success(request, "Folha gerada com os contratos ativos!")
            return redirect(f"{request.path}?month={month_str}")

    # AÇÃO: SINCRONIZAR (Atualiza Valor do Contrato mas mantem o Valor a Pagar editado)
    if request.method == 'POST' and 'atualizar_valores' in request.POST:
        configs = BucomaxiloConfiguracao.objects.filter(company_id=active_company_id)
        config_map = {c.nome_profissional: c for c in configs}
        
        count = 0
        for item in queryset:
            cfg = config_map.get(item.nome_profissional)
            if cfg:
                item.valor_contrato = cfg.valor_mensal
                # Opcional: Recalcular o valor a pagar se quiser resetar
                # item.valor_pagar = cfg.valor_mensal 
                item.save()
                count += 1
        messages.success(request, f"{count} contratos sincronizados!")
        return redirect(f"{request.path}?month={month_str}")

    # AÇÃO: SALVAR GRID
    LancamentoFormSet = modelformset_factory(BucomaxiloLancamento, form=BucomaxiloLancamentoForm, extra=0)
    if request.method == 'POST' and 'salvar_grid' in request.POST:
        formset = LancamentoFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Pagamentos salvos!")
            return redirect(f"{request.path}?month={month_str}")
    else:
        formset = LancamentoFormSet(queryset=queryset)

    # TOTAIS
    total_contratos = sum(item.valor_contrato for item in queryset)
    total_pagar = sum(item.valor_pagar for item in queryset)
    total_saldo = sum(item.saldo_orcamentario for item in queryset)

    context = {
        'formset': formset,
        'month_str': month_str,
        'competencia': competencia,
        'tem_dados': queryset.exists(),
        'total_contratos': total_contratos,
        'total_pagar': total_pagar,
        'total_saldo': total_saldo,
    }
    return render(request, 'plantoes/bucomaxilo_folha.html', context)

# ==========================================
# MÓDULO: RESIDÊNCIA CIRURGIA (AULAS)
# ==========================================

# --- 1. CONFIGURAÇÕES (MÉDICOS) ---

@login_required
def residencia_settings_view(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return redirect('core:company_list')
    
    configs = ResidenciaConfiguracao.objects.filter(company_id=active_company_id)
    return render(request, 'plantoes/residencia_settings.html', {'configs': configs})

class ResidenciaConfigCreateView(LoginRequiredMixin, CreateView):
    model = ResidenciaConfiguracao
    form_class = ResidenciaConfigForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:residencia_settings')

    def form_valid(self, form):
        form.instance.company_id = self.request.session.get('active_company_id')
        return super().form_valid(form)

class ResidenciaConfigUpdateView(LoginRequiredMixin, UpdateView):
    model = ResidenciaConfiguracao
    form_class = ResidenciaConfigForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:residencia_settings')
    
    def get_queryset(self):
        return super().get_queryset().filter(company_id=self.request.session.get('active_company_id'))

class ResidenciaConfigDeleteView(LoginRequiredMixin, DeleteView):
    model = ResidenciaConfiguracao
    template_name = 'plantoes/generic_confirm_delete.html'
    success_url = reverse_lazy('plantoes:residencia_settings')
    
    def get_queryset(self):
        return super().get_queryset().filter(company_id=self.request.session.get('active_company_id'))


# --- 2. FOLHA MENSAL (PRODUÇÃO AULAS) ---

@login_required
def residencia_folha_view(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return redirect('core:company_list')

    # Filtros de Data
    today = timezone.now().date()
    month_str = request.GET.get('month', today.strftime('%Y-%m')) 
    try:
        competencia = datetime.strptime(f"{month_str}-01", "%Y-%m-%d").date()
    except ValueError:
        competencia = today.replace(day=1)

    queryset = ResidenciaLancamento.objects.filter(
        company_id=active_company_id,
        competencia=competencia
    ).order_by('nome_medico')

    # AÇÃO: GERAR FOLHA (Copia Médicos)
    if request.method == 'POST' and 'gerar_folha' in request.POST:
        configs = ResidenciaConfiguracao.objects.filter(company_id=active_company_id)
        if not configs.exists():
            messages.error(request, "Cadastre os Médicos da Residência primeiro!")
        else:
            novos = []
            for cfg in configs:
                if not queryset.filter(nome_medico=cfg.nome_medico).exists():
                    novos.append(ResidenciaLancamento(
                        company_id=active_company_id,
                        competencia=competencia,
                        nome_medico=cfg.nome_medico,
                        valor_aula=cfg.valor_aula,
                        meta_aulas=cfg.meta_aulas,
                        qtd_aulas=0 # Começa zerado
                    ))
            if novos:
                ResidenciaLancamento.objects.bulk_create(novos)
                messages.success(request, "Folha de aulas gerada!")
            return redirect(f"{request.path}?month={month_str}")

    # AÇÃO: SINCRONIZAR (Atualiza preços/metas)
    if request.method == 'POST' and 'atualizar_valores' in request.POST:
        configs = ResidenciaConfiguracao.objects.filter(company_id=active_company_id)
        config_map = {c.nome_medico: c for c in configs}
        
        count = 0
        for item in queryset:
            cfg = config_map.get(item.nome_medico)
            if cfg:
                item.valor_aula = cfg.valor_aula
                item.meta_aulas = cfg.meta_aulas
                item.save()
                count += 1
        messages.success(request, f"{count} registros sincronizados!")
        return redirect(f"{request.path}?month={month_str}")

    # AÇÃO: SALVAR GRID
    LancamentoFormSet = modelformset_factory(ResidenciaLancamento, form=ResidenciaLancamentoForm, extra=0)
    if request.method == 'POST' and 'salvar_grid' in request.POST:
        formset = LancamentoFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Produção salva com sucesso!")
            return redirect(f"{request.path}?month={month_str}")
    else:
        formset = LancamentoFormSet(queryset=queryset)

    # TOTAIS
    total_orcado = sum(item.total_orcado for item in queryset)
    total_realizado = sum(item.total_realizado for item in queryset)
    total_saldo = sum(item.saldo_orcamentario for item in queryset)

    context = {
        'formset': formset,
        'month_str': month_str,
        'competencia': competencia,
        'tem_dados': queryset.exists(),
        'total_orcado': total_orcado,
        'total_realizado': total_realizado,
        'total_saldo': total_saldo,
    }
    return render(request, 'plantoes/residencia_folha.html', context)

# ==========================================
# MÓDULO: COORDENAÇÕES
# ==========================================

# --- 1. CONFIGURAÇÕES ---
@login_required
def coordenacao_settings_view(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return redirect('core:company_list')
    
    configs = CoordenacaoConfiguracao.objects.filter(company_id=active_company_id)
    return render(request, 'plantoes/coordenacao_settings.html', {'configs': configs})

class CoordenacaoConfigCreateView(LoginRequiredMixin, CreateView):
    model = CoordenacaoConfiguracao
    form_class = CoordenacaoConfigForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:coordenacao_settings')

    def form_valid(self, form):
        form.instance.company_id = self.request.session.get('active_company_id')
        return super().form_valid(form)

class CoordenacaoConfigUpdateView(LoginRequiredMixin, UpdateView):
    model = CoordenacaoConfiguracao
    form_class = CoordenacaoConfigForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:coordenacao_settings')
    
    def get_queryset(self):
        return super().get_queryset().filter(company_id=self.request.session.get('active_company_id'))

class CoordenacaoConfigDeleteView(LoginRequiredMixin, DeleteView):
    model = CoordenacaoConfiguracao
    template_name = 'plantoes/generic_confirm_delete.html'
    success_url = reverse_lazy('plantoes:coordenacao_settings')
    
    def get_queryset(self):
        return super().get_queryset().filter(company_id=self.request.session.get('active_company_id'))


# --- 2. FOLHA MENSAL ---
@login_required
def coordenacao_folha_view(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return redirect('core:company_list')

    today = timezone.now().date()
    month_str = request.GET.get('month', today.strftime('%Y-%m')) 
    try:
        competencia = datetime.strptime(f"{month_str}-01", "%Y-%m-%d").date()
    except ValueError:
        competencia = today.replace(day=1)

    queryset = CoordenacaoLancamento.objects.filter(
        company_id=active_company_id,
        competencia=competencia
    ).order_by('nome_funcionario')

    # AÇÃO: GERAR FOLHA
    if request.method == 'POST' and 'gerar_folha' in request.POST:
        configs = CoordenacaoConfiguracao.objects.filter(company_id=active_company_id)
        if not configs.exists():
            messages.error(request, "Cadastre os Coordenadores primeiro!")
        else:
            novos = []
            for cfg in configs:
                if not queryset.filter(nome_funcionario=cfg.nome_funcionario).exists():
                    novos.append(CoordenacaoLancamento(
                        company_id=active_company_id,
                        competencia=competencia,
                        nome_funcionario=cfg.nome_funcionario,
                        matricula=cfg.matricula,
                        conselho=cfg.conselho,
                        setor=cfg.setor,
                        valor_contrato=cfg.valor_mensal,
                        valor_pagar=cfg.valor_mensal # Padrão: Paga o combinado
                    ))
            if novos:
                CoordenacaoLancamento.objects.bulk_create(novos)
                messages.success(request, "Folha de Coordenação gerada!")
            return redirect(f"{request.path}?month={month_str}")

    # AÇÃO: SINCRONIZAR
    if request.method == 'POST' and 'atualizar_valores' in request.POST:
        configs = CoordenacaoConfiguracao.objects.filter(company_id=active_company_id)
        config_map = {c.nome_funcionario: c for c in configs}
        count = 0
        for item in queryset:
            cfg = config_map.get(item.nome_funcionario)
            if cfg:
                item.valor_contrato = cfg.valor_mensal
                item.matricula = cfg.matricula
                item.setor = cfg.setor
                item.save()
                count += 1
        messages.success(request, f"{count} registros atualizados!")
        return redirect(f"{request.path}?month={month_str}")

    # AÇÃO: SALVAR
    LancamentoFormSet = modelformset_factory(CoordenacaoLancamento, form=CoordenacaoLancamentoForm, extra=0)
    if request.method == 'POST' and 'salvar_grid' in request.POST:
        formset = LancamentoFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Dados salvos com sucesso!")
            return redirect(f"{request.path}?month={month_str}")
    else:
        formset = LancamentoFormSet(queryset=queryset)

    # TOTAIS
    total_contratos = sum(item.valor_contrato for item in queryset)
    total_pagar = sum(item.valor_pagar for item in queryset)
    total_saldo = sum(item.saldo_orcamentario for item in queryset)

    context = {
        'formset': formset,
        'month_str': month_str,
        'competencia': competencia,
        'tem_dados': queryset.exists(),
        'total_contratos': total_contratos,
        'total_pagar': total_pagar,
        'total_saldo': total_saldo,
    }
    return render(request, 'plantoes/coordenacao_folha.html', context)


# ==============================================================
# MÓDULO: AMBULATÓRIO
# ==============================================================

@login_required
def ambulatorio_settings_view(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return redirect('core:company_list')
    configs = AmbulatorioConfiguracao.objects.filter(company_id=active_company_id)
    return render(request, 'plantoes/ambulatorio_settings.html', {'configs': configs})


class AmbulatorioConfigCreateView(LoginRequiredMixin, CreateView):
    model = AmbulatorioConfiguracao
    form_class = AmbulatorioConfigForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:ambulatorio_settings')

    def form_valid(self, form):
        form.instance.company_id = self.request.session.get('active_company_id')
        return super().form_valid(form)


class AmbulatorioConfigUpdateView(LoginRequiredMixin, UpdateView):
    model = AmbulatorioConfiguracao
    form_class = AmbulatorioConfigForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:ambulatorio_settings')

    def get_queryset(self):
        return super().get_queryset().filter(company_id=self.request.session.get('active_company_id'))


class AmbulatorioConfigDeleteView(LoginRequiredMixin, DeleteView):
    model = AmbulatorioConfiguracao
    template_name = 'plantoes/generic_confirm_delete.html'
    success_url = reverse_lazy('plantoes:ambulatorio_settings')

    def get_queryset(self):
        return super().get_queryset().filter(company_id=self.request.session.get('active_company_id'))


@login_required
def ambulatorio_folha_view(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return redirect('core:company_list')

    today = timezone.now().date()
    month_str = request.GET.get('month', today.strftime('%Y-%m'))
    try:
        competencia = datetime.strptime(f"{month_str}-01", "%Y-%m-%d").date()
    except ValueError:
        competencia = today.replace(day=1)

    queryset = AmbulatorioLancamento.objects.filter(
        company_id=active_company_id, competencia=competencia
    ).order_by('nome_medico')

    if request.method == 'POST' and 'gerar_folha' in request.POST:
        configs = AmbulatorioConfiguracao.objects.filter(company_id=active_company_id)
        if not configs.exists():
            messages.error(request, "Cadastre os médicos do Ambulatório primeiro!")
        else:
            novos = []
            for cfg in configs:
                if not queryset.filter(nome_medico=cfg.nome_medico).exists():
                    novos.append(AmbulatorioLancamento(
                        company_id=active_company_id,
                        competencia=competencia,
                        nome_medico=cfg.nome_medico,
                        especialidade=cfg.especialidade,
                        vinculo=cfg.vinculo,
                        ch_mensal=cfg.ch_mensal,
                        valor_contrato=cfg.valor_mensal,
                        valor_pagar=cfg.valor_mensal,
                    ))
            if novos:
                AmbulatorioLancamento.objects.bulk_create(novos)
                messages.success(request, "Folha do Ambulatório gerada!")
        return redirect(f"{request.path}?month={month_str}")

    if request.method == 'POST' and 'atualizar_valores' in request.POST:
        configs = AmbulatorioConfiguracao.objects.filter(company_id=active_company_id)
        config_map = {c.nome_medico: c for c in configs}
        count = 0
        for item in queryset:
            cfg = config_map.get(item.nome_medico)
            if cfg:
                item.valor_contrato = cfg.valor_mensal
                item.save()
                count += 1
        messages.success(request, f"{count} registros sincronizados!")
        return redirect(f"{request.path}?month={month_str}")

    LancamentoFormSet = modelformset_factory(AmbulatorioLancamento, form=AmbulatorioLancamentoForm, extra=0)
    if request.method == 'POST' and 'salvar_grid' in request.POST:
        formset = LancamentoFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Pagamentos salvos!")
            return redirect(f"{request.path}?month={month_str}")
    else:
        formset = LancamentoFormSet(queryset=queryset)

    total_contratos = sum(item.valor_contrato for item in queryset)
    total_pagar = sum(item.valor_pagar for item in queryset)
    total_saldo = sum(item.saldo_orcamentario for item in queryset)

    return render(request, 'plantoes/ambulatorio_folha.html', {
        'formset': formset, 'month_str': month_str, 'competencia': competencia,
        'tem_dados': queryset.exists(), 'total_contratos': total_contratos,
        'total_pagar': total_pagar, 'total_saldo': total_saldo,
    })


# ==============================================================
# MÓDULO: ULTRASSONOGRAFIA
# ==============================================================

@login_required
def ultrassonografia_settings_view(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return redirect('core:company_list')
    configs = UltrassonografiaConfiguracao.objects.filter(company_id=active_company_id)
    return render(request, 'plantoes/ultrassonografia_settings.html', {'configs': configs})


class UltrassonografiaConfigCreateView(LoginRequiredMixin, CreateView):
    model = UltrassonografiaConfiguracao
    form_class = UltrassonografiaConfigForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:ultrassonografia_settings')

    def form_valid(self, form):
        form.instance.company_id = self.request.session.get('active_company_id')
        return super().form_valid(form)


class UltrassonografiaConfigUpdateView(LoginRequiredMixin, UpdateView):
    model = UltrassonografiaConfiguracao
    form_class = UltrassonografiaConfigForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:ultrassonografia_settings')

    def get_queryset(self):
        return super().get_queryset().filter(company_id=self.request.session.get('active_company_id'))


class UltrassonografiaConfigDeleteView(LoginRequiredMixin, DeleteView):
    model = UltrassonografiaConfiguracao
    template_name = 'plantoes/generic_confirm_delete.html'
    success_url = reverse_lazy('plantoes:ultrassonografia_settings')

    def get_queryset(self):
        return super().get_queryset().filter(company_id=self.request.session.get('active_company_id'))


@login_required
def ultrassonografia_folha_view(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return redirect('core:company_list')

    today = timezone.now().date()
    month_str = request.GET.get('month', today.strftime('%Y-%m'))
    try:
        competencia = datetime.strptime(f"{month_str}-01", "%Y-%m-%d").date()
    except ValueError:
        competencia = today.replace(day=1)

    _, dias_no_mes_atual = calendar.monthrange(competencia.year, competencia.month)

    queryset = UltrassonografiaLancamento.objects.filter(
        company_id=active_company_id, competencia=competencia
    ).order_by('cargo_nome')

    if request.method == 'POST' and 'gerar_folha' in request.POST:
        configs = UltrassonografiaConfiguracao.objects.filter(company_id=active_company_id)
        if not configs.exists():
            messages.error(request, "Cadastre a Matriz da Ultrassonografia primeiro!")
        else:
            novos = []
            for cfg in configs:
                if not queryset.filter(cargo_nome=cfg.cargo).exists():
                    novos.append(UltrassonografiaLancamento(
                        company_id=active_company_id,
                        competencia=competencia,
                        cargo_nome=cfg.cargo,
                        qtd_dia=cfg.qtd_dia,
                        valor_plantao_dia=cfg.valor_plantao_dia,
                        qtd_noite=cfg.qtd_noite,
                        valor_plantao_noite=cfg.valor_plantao_noite,
                        dias_mes=dias_no_mes_atual,
                    ))
            if novos:
                UltrassonografiaLancamento.objects.bulk_create(novos)
                messages.success(request, "Folha de Ultrassonografia gerada!")
        return redirect(f"{request.path}?month={month_str}")

    if request.method == 'POST' and 'atualizar_valores' in request.POST:
        configs = UltrassonografiaConfiguracao.objects.filter(company_id=active_company_id)
        config_map = {c.cargo: c for c in configs}
        count = 0
        for item in queryset:
            cfg = config_map.get(item.cargo_nome)
            if cfg:
                item.qtd_dia = cfg.qtd_dia
                item.valor_plantao_dia = cfg.valor_plantao_dia
                item.qtd_noite = cfg.qtd_noite
                item.valor_plantao_noite = cfg.valor_plantao_noite
                item.dias_mes = dias_no_mes_atual
                item.save()
                count += 1
        messages.success(request, f"{count} itens sincronizados!")
        return redirect(f"{request.path}?month={month_str}")

    LancamentoFormSet = modelformset_factory(UltrassonografiaLancamento, form=UltrassonografiaLancamentoForm, extra=0)
    if request.method == 'POST' and 'salvar_grid' in request.POST:
        formset = LancamentoFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Lançamentos salvos!")
            return redirect(f"{request.path}?month={month_str}")
    else:
        formset = LancamentoFormSet(queryset=queryset)

    total_orcado = sum(item.total_escala_calculada for item in queryset)
    total_realizado = sum(item.total_realizado for item in queryset)
    total_saldo = sum(item.saldo_orcamentario for item in queryset)

    return render(request, 'plantoes/ultrassonografia_folha.html', {
        'formset': formset, 'month_str': month_str, 'competencia': competencia,
        'tem_dados': queryset.exists(), 'total_orcado': total_orcado,
        'total_realizado': total_realizado, 'total_saldo': total_saldo,
    })


# ==============================================================
# MÓDULO: ENDOSCOPIA
# ==============================================================

@login_required
def endoscopia_settings_view(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return redirect('core:company_list')
    configs = EndoscopiaConfiguracao.objects.filter(company_id=active_company_id)
    return render(request, 'plantoes/endoscopia_settings.html', {'configs': configs})


class EndoscopiaConfigCreateView(LoginRequiredMixin, CreateView):
    model = EndoscopiaConfiguracao
    form_class = EndoscopiaConfigForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:endoscopia_settings')

    def form_valid(self, form):
        form.instance.company_id = self.request.session.get('active_company_id')
        return super().form_valid(form)


class EndoscopiaConfigUpdateView(LoginRequiredMixin, UpdateView):
    model = EndoscopiaConfiguracao
    form_class = EndoscopiaConfigForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:endoscopia_settings')

    def get_queryset(self):
        return super().get_queryset().filter(company_id=self.request.session.get('active_company_id'))


class EndoscopiaConfigDeleteView(LoginRequiredMixin, DeleteView):
    model = EndoscopiaConfiguracao
    template_name = 'plantoes/generic_confirm_delete.html'
    success_url = reverse_lazy('plantoes:endoscopia_settings')

    def get_queryset(self):
        return super().get_queryset().filter(company_id=self.request.session.get('active_company_id'))


@login_required
def endoscopia_folha_view(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return redirect('core:company_list')

    today = timezone.now().date()
    month_str = request.GET.get('month', today.strftime('%Y-%m'))
    try:
        competencia = datetime.strptime(f"{month_str}-01", "%Y-%m-%d").date()
    except ValueError:
        competencia = today.replace(day=1)

    queryset = EndoscopiaLancamento.objects.filter(
        company_id=active_company_id, competencia=competencia
    ).order_by('nome_procedimento')

    if request.method == 'POST' and 'gerar_folha' in request.POST:
        configs = EndoscopiaConfiguracao.objects.filter(company_id=active_company_id)
        if not configs.exists():
            messages.error(request, "Cadastre os procedimentos de Endoscopia primeiro!")
        else:
            novos = []
            for cfg in configs:
                if not queryset.filter(nome_procedimento=cfg.nome_procedimento).exists():
                    novos.append(EndoscopiaLancamento(
                        company_id=active_company_id,
                        competencia=competencia,
                        nome_procedimento=cfg.nome_procedimento,
                        valor_unitario=cfg.valor_unitario,
                        meta_qtd=cfg.meta_mensal_qtd,
                        qtd_realizada=0,
                    ))
            if novos:
                EndoscopiaLancamento.objects.bulk_create(novos)
                messages.success(request, "Folha de Produção gerada!")
        return redirect(f"{request.path}?month={month_str}")

    if request.method == 'POST' and 'atualizar_valores' in request.POST:
        configs = EndoscopiaConfiguracao.objects.filter(company_id=active_company_id)
        config_map = {c.nome_procedimento: c for c in configs}
        count = 0
        for item in queryset:
            cfg = config_map.get(item.nome_procedimento)
            if cfg:
                item.valor_unitario = cfg.valor_unitario
                item.meta_qtd = cfg.meta_mensal_qtd
                item.save()
                count += 1
        messages.success(request, f"{count} itens atualizados!")
        return redirect(f"{request.path}?month={month_str}")

    LancamentoFormSet = modelformset_factory(EndoscopiaLancamento, form=EndoscopiaLancamentoForm, extra=0)
    if request.method == 'POST' and 'salvar_grid' in request.POST:
        formset = LancamentoFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Produção salva!")
            return redirect(f"{request.path}?month={month_str}")
    else:
        formset = LancamentoFormSet(queryset=queryset)

    total_orcado = sum(item.total_orcado for item in queryset)
    total_realizado = sum(item.total_realizado for item in queryset)
    total_saldo = sum(item.saldo_orcamentario for item in queryset)

    return render(request, 'plantoes/endoscopia_folha.html', {
        'formset': formset, 'month_str': month_str, 'competencia': competencia,
        'tem_dados': queryset.exists(), 'total_orcado': total_orcado,
        'total_realizado': total_realizado, 'total_saldo': total_saldo,
    })


# ==============================================================
# MÓDULO: ANESTESIOLOGIA
# ==============================================================

@login_required
def anestesiologia_settings_view(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return redirect('core:company_list')
    configs = AnestesiologiaConfiguracao.objects.filter(company_id=active_company_id)
    return render(request, 'plantoes/anestesiologia_settings.html', {'configs': configs})


class AnestesiologiaConfigCreateView(LoginRequiredMixin, CreateView):
    model = AnestesiologiaConfiguracao
    form_class = AnestesiologiaConfigForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:anestesiologia_settings')

    def form_valid(self, form):
        form.instance.company_id = self.request.session.get('active_company_id')
        return super().form_valid(form)


class AnestesiologiaConfigUpdateView(LoginRequiredMixin, UpdateView):
    model = AnestesiologiaConfiguracao
    form_class = AnestesiologiaConfigForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:anestesiologia_settings')

    def get_queryset(self):
        return super().get_queryset().filter(company_id=self.request.session.get('active_company_id'))


class AnestesiologiaConfigDeleteView(LoginRequiredMixin, DeleteView):
    model = AnestesiologiaConfiguracao
    template_name = 'plantoes/generic_confirm_delete.html'
    success_url = reverse_lazy('plantoes:anestesiologia_settings')

    def get_queryset(self):
        return super().get_queryset().filter(company_id=self.request.session.get('active_company_id'))


@login_required
def anestesiologia_folha_view(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return redirect('core:company_list')

    today = timezone.now().date()
    month_str = request.GET.get('month', today.strftime('%Y-%m'))
    try:
        competencia = datetime.strptime(f"{month_str}-01", "%Y-%m-%d").date()
    except ValueError:
        competencia = today.replace(day=1)

    _, dias_no_mes_atual = calendar.monthrange(competencia.year, competencia.month)

    queryset = AnestesiologiaLancamento.objects.filter(
        company_id=active_company_id, competencia=competencia
    ).order_by('tipo_servico')

    if request.method == 'POST' and 'gerar_folha' in request.POST:
        configs = AnestesiologiaConfiguracao.objects.filter(company_id=active_company_id)
        if not configs.exists():
            messages.error(request, "Cadastre a Matriz da Anestesiologia primeiro!")
        else:
            novos = []
            for cfg in configs:
                if not queryset.filter(tipo_servico=cfg.tipo_servico).exists():
                    novos.append(AnestesiologiaLancamento(
                        company_id=active_company_id,
                        competencia=competencia,
                        tipo_servico=cfg.tipo_servico,
                        qtd_dia=cfg.qtd_dia,
                        valor_plantao_dia=cfg.valor_plantao_dia,
                        qtd_noite=cfg.qtd_noite,
                        valor_plantao_noite=cfg.valor_plantao_noite,
                        dias_mes=dias_no_mes_atual,
                    ))
            if novos:
                AnestesiologiaLancamento.objects.bulk_create(novos)
                messages.success(request, "Folha de Anestesiologia gerada!")
        return redirect(f"{request.path}?month={month_str}")

    if request.method == 'POST' and 'atualizar_valores' in request.POST:
        configs = AnestesiologiaConfiguracao.objects.filter(company_id=active_company_id)
        config_map = {c.tipo_servico: c for c in configs}
        count = 0
        for item in queryset:
            cfg = config_map.get(item.tipo_servico)
            if cfg:
                item.qtd_dia = cfg.qtd_dia
                item.valor_plantao_dia = cfg.valor_plantao_dia
                item.qtd_noite = cfg.qtd_noite
                item.valor_plantao_noite = cfg.valor_plantao_noite
                item.dias_mes = dias_no_mes_atual
                item.save()
                count += 1
        messages.success(request, f"{count} itens sincronizados!")
        return redirect(f"{request.path}?month={month_str}")

    LancamentoFormSet = modelformset_factory(AnestesiologiaLancamento, form=AnestesiologiaLancamentoForm, extra=0)
    if request.method == 'POST' and 'salvar_grid' in request.POST:
        formset = LancamentoFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Lançamentos salvos!")
            return redirect(f"{request.path}?month={month_str}")
    else:
        formset = LancamentoFormSet(queryset=queryset)

    total_orcado = sum(item.total_escala_calculada for item in queryset)
    total_realizado = sum(item.total_realizado for item in queryset)
    total_saldo = sum(item.saldo_orcamentario for item in queryset)

    return render(request, 'plantoes/anestesiologia_folha.html', {
        'formset': formset, 'month_str': month_str, 'competencia': competencia,
        'tem_dados': queryset.exists(), 'total_orcado': total_orcado,
        'total_realizado': total_realizado, 'total_saldo': total_saldo,
    })


# ==============================================================
# MÓDULO: COMISSÕES
# ==============================================================

@login_required
def comissao_settings_view(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return redirect('core:company_list')
    configs = ComissaoConfiguracao.objects.filter(company_id=active_company_id)
    return render(request, 'plantoes/comissao_settings.html', {'configs': configs})


class ComissaoConfigCreateView(LoginRequiredMixin, CreateView):
    model = ComissaoConfiguracao
    form_class = ComissaoConfigForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:comissao_settings')

    def form_valid(self, form):
        form.instance.company_id = self.request.session.get('active_company_id')
        return super().form_valid(form)


class ComissaoConfigUpdateView(LoginRequiredMixin, UpdateView):
    model = ComissaoConfiguracao
    form_class = ComissaoConfigForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:comissao_settings')

    def get_queryset(self):
        return super().get_queryset().filter(company_id=self.request.session.get('active_company_id'))


class ComissaoConfigDeleteView(LoginRequiredMixin, DeleteView):
    model = ComissaoConfiguracao
    template_name = 'plantoes/generic_confirm_delete.html'
    success_url = reverse_lazy('plantoes:comissao_settings')

    def get_queryset(self):
        return super().get_queryset().filter(company_id=self.request.session.get('active_company_id'))


@login_required
def comissao_folha_view(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return redirect('core:company_list')

    today = timezone.now().date()
    month_str = request.GET.get('month', today.strftime('%Y-%m'))
    try:
        competencia = datetime.strptime(f"{month_str}-01", "%Y-%m-%d").date()
    except ValueError:
        competencia = today.replace(day=1)

    queryset = ComissaoLancamento.objects.filter(
        company_id=active_company_id, competencia=competencia
    ).order_by('nome_comissao')

    if request.method == 'POST' and 'gerar_folha' in request.POST:
        configs = ComissaoConfiguracao.objects.filter(company_id=active_company_id)
        if not configs.exists():
            messages.error(request, "Cadastre as Comissões primeiro!")
        else:
            novos = []
            for cfg in configs:
                if not queryset.filter(nome_comissao=cfg.nome_comissao).exists():
                    novos.append(ComissaoLancamento(
                        company_id=active_company_id,
                        competencia=competencia,
                        nome_comissao=cfg.nome_comissao,
                        descricao=cfg.descricao,
                        valor_contrato=cfg.valor_mensal,
                        valor_pagar=cfg.valor_mensal,
                    ))
            if novos:
                ComissaoLancamento.objects.bulk_create(novos)
                messages.success(request, "Folha de Comissões gerada!")
        return redirect(f"{request.path}?month={month_str}")

    if request.method == 'POST' and 'atualizar_valores' in request.POST:
        configs = ComissaoConfiguracao.objects.filter(company_id=active_company_id)
        config_map = {c.nome_comissao: c for c in configs}
        count = 0
        for item in queryset:
            cfg = config_map.get(item.nome_comissao)
            if cfg:
                item.valor_contrato = cfg.valor_mensal
                item.save()
                count += 1
        messages.success(request, f"{count} comissões sincronizadas!")
        return redirect(f"{request.path}?month={month_str}")

    LancamentoFormSet = modelformset_factory(ComissaoLancamento, form=ComissaoLancamentoForm, extra=0)
    if request.method == 'POST' and 'salvar_grid' in request.POST:
        formset = LancamentoFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Pagamentos salvos!")
            return redirect(f"{request.path}?month={month_str}")
    else:
        formset = LancamentoFormSet(queryset=queryset)

    total_contratos = sum(item.valor_contrato for item in queryset)
    total_pagar = sum(item.valor_pagar for item in queryset)
    total_saldo = sum(item.saldo_orcamentario for item in queryset)

    return render(request, 'plantoes/comissao_folha.html', {
        'formset': formset, 'month_str': month_str, 'competencia': competencia,
        'tem_dados': queryset.exists(), 'total_contratos': total_contratos,
        'total_pagar': total_pagar, 'total_saldo': total_saldo,
    })


# ==============================================================
# MÓDULO: COOPERATIVAS
# ==============================================================

@login_required
def cooperativa_settings_view(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return redirect('core:company_list')
    configs = CooperativaConfiguracao.objects.filter(company_id=active_company_id)
    return render(request, 'plantoes/cooperativa_settings.html', {'configs': configs})


class CooperativaConfigCreateView(LoginRequiredMixin, CreateView):
    model = CooperativaConfiguracao
    form_class = CooperativaConfigForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:cooperativa_settings')

    def form_valid(self, form):
        form.instance.company_id = self.request.session.get('active_company_id')
        return super().form_valid(form)


class CooperativaConfigUpdateView(LoginRequiredMixin, UpdateView):
    model = CooperativaConfiguracao
    form_class = CooperativaConfigForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:cooperativa_settings')

    def get_queryset(self):
        return super().get_queryset().filter(company_id=self.request.session.get('active_company_id'))


class CooperativaConfigDeleteView(LoginRequiredMixin, DeleteView):
    model = CooperativaConfiguracao
    template_name = 'plantoes/generic_confirm_delete.html'
    success_url = reverse_lazy('plantoes:cooperativa_settings')

    def get_queryset(self):
        return super().get_queryset().filter(company_id=self.request.session.get('active_company_id'))


@login_required
def cooperativa_folha_view(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return redirect('core:company_list')

    today = timezone.now().date()
    month_str = request.GET.get('month', today.strftime('%Y-%m'))
    try:
        competencia = datetime.strptime(f"{month_str}-01", "%Y-%m-%d").date()
    except ValueError:
        competencia = today.replace(day=1)

    queryset = CooperativaLancamento.objects.filter(
        company_id=active_company_id, competencia=competencia
    ).order_by('nome_cooperativa')

    if request.method == 'POST' and 'gerar_folha' in request.POST:
        configs = CooperativaConfiguracao.objects.filter(company_id=active_company_id)
        if not configs.exists():
            messages.error(request, "Cadastre as Cooperativas primeiro!")
        else:
            novos = []
            for cfg in configs:
                if not queryset.filter(nome_cooperativa=cfg.nome_cooperativa).exists():
                    novos.append(CooperativaLancamento(
                        company_id=active_company_id,
                        competencia=competencia,
                        nome_cooperativa=cfg.nome_cooperativa,
                        descricao=cfg.descricao,
                        valor_contrato=cfg.valor_mensal,
                        valor_pagar=cfg.valor_mensal,
                    ))
            if novos:
                CooperativaLancamento.objects.bulk_create(novos)
                messages.success(request, "Folha de Cooperativas gerada!")
        return redirect(f"{request.path}?month={month_str}")

    if request.method == 'POST' and 'atualizar_valores' in request.POST:
        configs = CooperativaConfiguracao.objects.filter(company_id=active_company_id)
        config_map = {c.nome_cooperativa: c for c in configs}
        count = 0
        for item in queryset:
            cfg = config_map.get(item.nome_cooperativa)
            if cfg:
                item.valor_contrato = cfg.valor_mensal
                item.save()
                count += 1
        messages.success(request, f"{count} cooperativas sincronizadas!")
        return redirect(f"{request.path}?month={month_str}")

    LancamentoFormSet = modelformset_factory(CooperativaLancamento, form=CooperativaLancamentoForm, extra=0)
    if request.method == 'POST' and 'salvar_grid' in request.POST:
        formset = LancamentoFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Pagamentos salvos!")
            return redirect(f"{request.path}?month={month_str}")
    else:
        formset = LancamentoFormSet(queryset=queryset)

    total_contratos = sum(item.valor_contrato for item in queryset)
    total_pagar = sum(item.valor_pagar for item in queryset)
    total_saldo = sum(item.saldo_orcamentario for item in queryset)

    return render(request, 'plantoes/cooperativa_folha.html', {
        'formset': formset, 'month_str': month_str, 'competencia': competencia,
        'tem_dados': queryset.exists(), 'total_contratos': total_contratos,
        'total_pagar': total_pagar, 'total_saldo': total_saldo,
    })


# ==========================================
# DASHBOARD CONSOLIDADO (HOME)
# ==========================================

@login_required
def plantoes_dashboard_view(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return redirect('core:company_list')

    # 1. Filtro de Competência
    today = timezone.now().date()
    month_str = request.GET.get('month', today.strftime('%Y-%m'))
    try:
        competencia = datetime.strptime(f"{month_str}-01", "%Y-%m-%d").date()
    except ValueError:
        competencia = today.replace(day=1)

    # 2. Coleta de Dados e Somas (Realizado)
    
    # A. Urgência e Emergência
    urg_qs = UrgenciaLancamento.objects.filter(company_id=active_company_id, competencia=competencia)
    total_urgencia = sum(item.total_realizado for item in urg_qs)

    # B. Cirurgia Geral
    cir_qs = CirurgiaLancamento.objects.filter(company_id=active_company_id, competencia=competencia)
    total_cirurgia = sum(item.total_realizado for item in cir_qs)

    # C. Nefrologia
    nefro_qs = NefrologiaLancamento.objects.filter(company_id=active_company_id, competencia=competencia)
    total_nefrologia = sum(item.total_realizado for item in nefro_qs)

    # D. Bucomaxilo (Campo valor_pagar)
    buco_qs = BucomaxiloLancamento.objects.filter(company_id=active_company_id, competencia=competencia)
    total_bucomaxilo = sum(item.valor_pagar for item in buco_qs)

    # E. Residência Cirurgia
    resid_qs = ResidenciaLancamento.objects.filter(company_id=active_company_id, competencia=competencia)
    total_residencia = sum(item.total_realizado for item in resid_qs)

    # F. Coordenações
    coord_qs = CoordenacaoLancamento.objects.filter(company_id=active_company_id, competencia=competencia)
    total_coordenacao = sum(item.valor_pagar for item in coord_qs)

    # G. Equipe de Transporte
    transp_qs = TransporteLancamento.objects.filter(
        company_id=active_company_id,
        competencia__year=competencia.year,
        competencia__month=competencia.month
    )
    total_transporte = sum((item.quantidade_viagens * item.valor_viagem) for item in transp_qs)

    # H. Ambulatório
    amb_qs = AmbulatorioLancamento.objects.filter(company_id=active_company_id, competencia=competencia)
    total_ambulatorio = sum(item.valor_pagar for item in amb_qs)

    # I. Ultrassonografia
    usg_qs = UltrassonografiaLancamento.objects.filter(company_id=active_company_id, competencia=competencia)
    total_ultrassonografia = sum(item.total_realizado for item in usg_qs)

    # J. Endoscopia
    endo_qs = EndoscopiaLancamento.objects.filter(company_id=active_company_id, competencia=competencia)
    total_endoscopia = sum(item.total_realizado for item in endo_qs)

    # K. Anestesiologia
    anest_qs = AnestesiologiaLancamento.objects.filter(company_id=active_company_id, competencia=competencia)
    total_anestesiologia = sum(item.total_realizado for item in anest_qs)

    # L. Comissões
    com_qs = ComissaoLancamento.objects.filter(company_id=active_company_id, competencia=competencia)
    total_comissoes = sum(item.valor_pagar for item in com_qs)

    # M. Cooperativas
    coop_qs = CooperativaLancamento.objects.filter(company_id=active_company_id, competencia=competencia)
    total_cooperativas = sum(item.valor_pagar for item in coop_qs)

    # 3. Consolidação
    items = [
        {'nome': 'Urgência e Emergência', 'valor': total_urgencia, 'url': 'plantoes:urgencia_folha', 'icon': 'bi-heart-pulse'},
        {'nome': 'Cirurgia Geral', 'valor': total_cirurgia, 'url': 'plantoes:cirurgia_folha', 'icon': 'bi-bandaid'},
        {'nome': 'Anestesiologia', 'valor': total_anestesiologia, 'url': 'plantoes:anestesiologia_folha', 'icon': 'bi-capsule'},
        {'nome': 'Serviço de Nefrologia', 'valor': total_nefrologia, 'url': 'plantoes:nefrologia_folha', 'icon': 'bi-droplet'},
        {'nome': 'Bucomaxilo', 'valor': total_bucomaxilo, 'url': 'plantoes:bucomaxilo_folha', 'icon': 'bi-person-lines-fill'},
        {'nome': 'Aulas COREME', 'valor': total_residencia, 'url': 'plantoes:residencia_folha', 'icon': 'bi-mortarboard'},
        {'nome': 'Ambulatório', 'valor': total_ambulatorio, 'url': 'plantoes:ambulatorio_folha', 'icon': 'bi-hospital'},
        {'nome': 'Ultrassonografia', 'valor': total_ultrassonografia, 'url': 'plantoes:ultrassonografia_folha', 'icon': 'bi-activity'},
        {'nome': 'Endoscopia e Exames', 'valor': total_endoscopia, 'url': 'plantoes:endoscopia_folha', 'icon': 'bi-search-heart'},
        {'nome': 'Coordenações', 'valor': total_coordenacao, 'url': 'plantoes:coordenacao_folha', 'icon': 'bi-people'},
        {'nome': 'Comissões', 'valor': total_comissoes, 'url': 'plantoes:comissao_folha', 'icon': 'bi-patch-check'},
        {'nome': 'Cooperativas', 'valor': total_cooperativas, 'url': 'plantoes:cooperativa_folha', 'icon': 'bi-building'},
        {'nome': 'Equipe de Transporte', 'valor': total_transporte, 'url': 'plantoes:transporte_list', 'icon': 'bi-ambulance'},
    ]

    # Ordenar do maior valor para o menor (Curva ABC)
    items.sort(key=lambda x: x['valor'], reverse=True)

    # 4. Total Geral e Cálculo de Porcentagem
    total_geral = sum(item['valor'] for item in items)

    for item in items:
        if total_geral > 0:
            item['percent'] = (item['valor'] / total_geral) * 100
        else:
            item['percent'] = 0

    context = {
        'month_str': month_str,
        'competencia': competencia,
        'items': items,
        'total_geral': total_geral,
    }
    return render(request, 'plantoes/dashboard.html', context)

# ==========================================
# RELATÓRIO ANUAL (CONSOLIDADO)
# ==========================================

@login_required
def plantoes_annual_report_view(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return redirect('core:company_list')

    # 1. Filtro de Ano
    today = timezone.now().date()
    try:
        current_year = int(request.GET.get('year', today.year))
    except ValueError:
        current_year = today.year
    
    years_list = [today.year - 1, today.year, today.year + 1]

    # 2. Estrutura de Dados
    services_data = [
        {'id': 'urgencia', 'name': 'Urgência e Emergência', 'months': []},
        {'id': 'cirurgia', 'name': 'Cirurgia Geral', 'months': []},
        {'id': 'anestesiologia', 'name': 'Anestesiologia', 'months': []},
        {'id': 'nefrologia', 'name': 'Serviço de Nefrologia', 'months': []},
        {'id': 'bucomaxilo', 'name': 'Bucomaxilo', 'months': []},
        {'id': 'residencia', 'name': 'Aulas COREME', 'months': []},
        {'id': 'ambulatorio', 'name': 'Ambulatório', 'months': []},
        {'id': 'ultrassonografia', 'name': 'Ultrassonografia', 'months': []},
        {'id': 'endoscopia', 'name': 'Endoscopia e Exames', 'months': []},
        {'id': 'coordenacao', 'name': 'Coordenações', 'months': []},
        {'id': 'comissoes', 'name': 'Comissões', 'months': []},
        {'id': 'cooperativas', 'name': 'Cooperativas', 'months': []},
        {'id': 'transporte', 'name': 'Equipe de Transporte', 'months': []},
    ]
    
    total_row = [{'valor': Decimal('0.00'), 'var_pct': Decimal('0.00')} for _ in range(12)]
    last_month_values = {s['id']: Decimal('0.00') for s in services_data}
    last_month_total = Decimal('0.00')

    # 3. Loop pelos 12 meses
    for month in range(1, 13):
        ref_date = datetime(current_year, month, 1).date()
        month_idx = month - 1 
        
        # --- BUSCAS ---

        # A. Urgência
        qs_urg = UrgenciaLancamento.objects.filter(company_id=active_company_id, competencia=ref_date)
        val_urg = sum((i.total_realizado for i in qs_urg), start=Decimal('0.00'))

        # B. Cirurgia
        qs_cir = CirurgiaLancamento.objects.filter(company_id=active_company_id, competencia=ref_date)
        val_cir = sum((i.total_realizado for i in qs_cir), start=Decimal('0.00'))

        # C. Nefro
        qs_nef = NefrologiaLancamento.objects.filter(company_id=active_company_id, competencia=ref_date)
        val_nef = sum((i.total_realizado for i in qs_nef), start=Decimal('0.00'))

        # D. Bucomaxilo
        qs_buc = BucomaxiloLancamento.objects.filter(company_id=active_company_id, competencia=ref_date)
        val_buc = sum((i.valor_pagar for i in qs_buc), start=Decimal('0.00'))

        # E. Residência
        qs_res = ResidenciaLancamento.objects.filter(company_id=active_company_id, competencia=ref_date)
        val_res = sum((i.total_realizado for i in qs_res), start=Decimal('0.00'))

        # F. Coordenação
        qs_coor = CoordenacaoLancamento.objects.filter(company_id=active_company_id, competencia=ref_date)
        val_coor = sum((i.valor_pagar for i in qs_coor), start=Decimal('0.00'))

        # G. Transporte
        qs_trans = TransporteLancamento.objects.filter(
            company_id=active_company_id,
            competencia__year=current_year,
            competencia__month=month
        )
        agg_trans = qs_trans.aggregate(
            total=Sum(F('quantidade_viagens') * F('valor_viagem'), output_field=DecimalField())
        )
        val_trans = agg_trans['total'] if agg_trans['total'] is not None else Decimal('0.00')

        # H. Ambulatório
        qs_amb = AmbulatorioLancamento.objects.filter(company_id=active_company_id, competencia=ref_date)
        val_amb = sum((i.valor_pagar for i in qs_amb), start=Decimal('0.00'))

        # I. Ultrassonografia
        qs_usg = UltrassonografiaLancamento.objects.filter(company_id=active_company_id, competencia=ref_date)
        val_usg = sum((i.total_realizado for i in qs_usg), start=Decimal('0.00'))

        # J. Endoscopia
        qs_end = EndoscopiaLancamento.objects.filter(company_id=active_company_id, competencia=ref_date)
        val_end = sum((i.total_realizado for i in qs_end), start=Decimal('0.00'))

        # K. Anestesiologia
        qs_anest = AnestesiologiaLancamento.objects.filter(company_id=active_company_id, competencia=ref_date)
        val_anest = sum((i.total_realizado for i in qs_anest), start=Decimal('0.00'))

        # L. Comissões
        qs_com = ComissaoLancamento.objects.filter(company_id=active_company_id, competencia=ref_date)
        val_com = sum((i.valor_pagar for i in qs_com), start=Decimal('0.00'))

        # M. Cooperativas
        qs_coop = CooperativaLancamento.objects.filter(company_id=active_company_id, competencia=ref_date)
        val_coop = sum((i.valor_pagar for i in qs_coop), start=Decimal('0.00'))

        current_values = {
            'urgencia': val_urg,
            'cirurgia': val_cir,
            'anestesiologia': val_anest,
            'nefrologia': val_nef,
            'bucomaxilo': val_buc,
            'residencia': val_res,
            'ambulatorio': val_amb,
            'ultrassonografia': val_usg,
            'endoscopia': val_end,
            'coordenacao': val_coor,
            'comissoes': val_com,
            'cooperativas': val_coop,
            'transporte': val_trans,
        }

        monthly_total_sum = Decimal('0.00')

        for service in services_data:
            s_id = service['id']
            val = current_values[s_id]
            prev_val = last_month_values[s_id]
            
            var_pct = Decimal('0.00')
            if prev_val > 0:
                var_pct = ((val - prev_val) / prev_val) * 100
            elif prev_val == 0 and val > 0:
                var_pct = Decimal('100.00')
            
            service['months'].append({
                'valor': val,
                'var_pct': var_pct,
                'has_data': (val > 0 or prev_val > 0)
            })
            
            last_month_values[s_id] = val
            monthly_total_sum += val

        # Totais da Linha Inferior
        total_var_pct = Decimal('0.00')
        if last_month_total > 0:
            total_var_pct = ((monthly_total_sum - last_month_total) / last_month_total) * 100
        elif last_month_total == 0 and monthly_total_sum > 0:
            total_var_pct = Decimal('100.00')

        total_row[month_idx] = {
            'valor': monthly_total_sum,
            'var_pct': total_var_pct
        }
        last_month_total = monthly_total_sum

    return render(request, 'plantoes/annual_report.html', {
        'current_year': current_year,
        'years_list': years_list,
        'services_data': services_data,
        'total_row': total_row,
        'months_names': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    })