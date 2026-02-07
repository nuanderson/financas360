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

from .models import Especialidade, Turno, UnidadeAssistencia, OrcamentoMensalPlantao, LancamentoPlantao, TransporteLancamento, UrgenciaConfiguracao, UrgenciaSetor, UrgenciaLancamento, CirurgiaConfiguracao, CirurgiaLancamento, CirurgiaSetor, NefrologiaConfiguracao, NefrologiaLancamento, BucomaxiloConfiguracao, BucomaxiloLancamento, ResidenciaConfiguracao, ResidenciaLancamento, CoordenacaoConfiguracao, CoordenacaoLancamento
from .forms import EspecialidadeForm, TurnoForm, UnidadeAssistenciaForm, OrcamentoMensalPlantaoForm, LancamentoPlantaoForm, TransporteForm, UrgenciaConfiguracaoForm, UrgenciaSetorForm, UrgenciaLancamentoForm, CirurgiaConfiguracaoForm, CirurgiaSetorForm, CirurgiaLancamentoForm, NefrologiaConfigForm, NefrologiaLancamentoForm, BucomaxiloConfigForm, BucomaxiloLancamentoForm, ResidenciaConfigForm, ResidenciaLancamentoForm, CoordenacaoConfigForm, CoordenacaoLancamentoForm

from core.models import Company

@login_required
def plantoes_settings(request):
    # Esta view busca os dados da empresa ativa e lista os itens de cada categoria
    # Buscamos o ID da empresa ativa diretamente da sessão
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        messages.error(request, "Por favor, selecione uma empresa primeiro.")
        return redirect('core:company_list')

    # Com o ID, buscamos o objeto da empresa no banco
    active_company = get_object_or_404(Company, pk=active_company_id, users=request.user)

    especialidades = Especialidade.objects.filter(company=active_company)
    turnos = Turno.objects.filter(company=active_company)
    unidades = UnidadeAssistencia.objects.filter(company=active_company)

    context = {
        'especialidades': especialidades,
        'turnos': turnos,
        'unidades': unidades,
    }
    return render(request, 'plantoes/plantoes_settings.html', context)


class CompanyQuerysetMixin(LoginRequiredMixin):
    def get_queryset(self):
        active_company_id = self.request.session.get('active_company_id')
        if not active_company_id:
            return self.model.objects.none()

        active_company = get_object_or_404(Company, pk=active_company_id, users=self.request.user)
        return self.model.objects.filter(company=active_company)



class CompanyFormMixin(LoginRequiredMixin):
    def form_valid(self, form):
        active_company_id = self.request.session.get('active_company_id')
        active_company = get_object_or_404(Company, pk=active_company_id, users=self.request.user)
        form.instance.company = active_company
        return super().form_valid(form)

class EspecialidadeCreateView(CompanyFormMixin, CreateView):
    model = Especialidade
    form_class = EspecialidadeForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:plantoes_settings')

class EspecialidadeUpdateView(CompanyFormMixin, CompanyQuerysetMixin, UpdateView):
    model = Especialidade
    form_class = EspecialidadeForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:plantoes_settings')

class EspecialidadeDeleteView(CompanyQuerysetMixin, DeleteView):
    model = Especialidade
    template_name = 'plantoes/generic_confirm_delete.html'
    success_url = reverse_lazy('plantoes:plantoes_settings')

# --- CRUD de Turno (segue o mesmo padrão) ---
class TurnoCreateView(CompanyFormMixin, CreateView):
    model = Turno
    form_class = TurnoForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:plantoes_settings')

class TurnoUpdateView(CompanyFormMixin, CompanyQuerysetMixin, UpdateView):
    model = Turno
    form_class = TurnoForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:plantoes_settings')

class TurnoDeleteView(CompanyQuerysetMixin, DeleteView):
    model = Turno
    template_name = 'plantoes/generic_confirm_delete.html'
    success_url = reverse_lazy('plantoes:plantoes_settings')

# --- CRUD de Unidade de Assistência (segue o mesmo padrão) ---
class UnidadeAssistenciaCreateView(CompanyFormMixin, CreateView):
    model = UnidadeAssistencia
    form_class = UnidadeAssistenciaForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:plantoes_settings')

class UnidadeAssistenciaUpdateView(CompanyFormMixin, CompanyQuerysetMixin, UpdateView):
    model = UnidadeAssistencia
    form_class = UnidadeAssistenciaForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:plantoes_settings')

class UnidadeAssistenciaDeleteView(CompanyQuerysetMixin, DeleteView):
    model = UnidadeAssistencia
    template_name = 'plantoes/generic_confirm_delete.html'
    success_url = reverse_lazy('plantoes:plantoes_settings')

class LancamentoPlantaoListView(CompanyQuerysetMixin, ListView):
    model = LancamentoPlantao
    template_name = 'plantoes/lancamento_plantao_list.html'
    context_object_name = 'lancamentos'
    paginate_by = 15

class LancamentoPlantaoCreateView(CompanyFormMixin, CreateView):
    model = LancamentoPlantao
    form_class = LancamentoPlantaoForm
    template_name = 'plantoes/lancamento_plantao_form.html'
    success_url = reverse_lazy('plantoes:lancamento_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Busca a empresa ativa da sessão
        active_company_id = self.request.session.get('active_company_id')
        if active_company_id:
            kwargs['company'] = get_object_or_404(Company, pk=active_company_id)
        return kwargs

class LancamentoPlantaoUpdateView(CompanyQuerysetMixin, CompanyFormMixin, UpdateView):
    model = LancamentoPlantao
    form_class = LancamentoPlantaoForm
    template_name = 'plantoes/lancamento_plantao_form.html'
    success_url = reverse_lazy('plantoes:lancamento_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Busca a empresa ativa da sessão
        active_company_id = self.request.session.get('active_company_id')
        if active_company_id:
            kwargs['company'] = get_object_or_404(Company, pk=active_company_id)
        return kwargs

class LancamentoPlantaoDeleteView(CompanyQuerysetMixin, DeleteView):
    model = LancamentoPlantao
    template_name = 'plantoes/generic_confirm_delete.html' # Podemos reutilizar o genérico
    success_url = reverse_lazy('plantoes:lancamento_list')

@login_required
def orcamento_mensal_view(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        messages.error(request, "Por favor, selecione uma empresa primeiro.")
        return redirect('core:company_list')
    
    active_company = get_object_or_404(Company, pk=active_company_id, users=request.user)
    
    current_year = datetime.now().year
    unidade_id = request.GET.get('unidade_assistencia')
    year_str = request.GET.get('year', str(current_year))
    year = int(year_str.replace('.', ''))
    
    # 🔒 só pega unidades da empresa ativa
    unidades_da_empresa = UnidadeAssistencia.objects.filter(company=active_company)
    unidade_selecionada = None
    formset = None

    if unidade_id:
        unidade_selecionada = get_object_or_404(unidades_da_empresa, pk=unidade_id)
        
        # 🔄 garante que existam 12 meses de orçamento para a unidade/ano
        for month in range(1, 13):
            OrcamentoMensalPlantao.objects.get_or_create(
                unidade_assistencia=unidade_selecionada,
                date=date(year, month, 1),
                defaults={'valor_orcado': 0}
            )

        queryset = OrcamentoMensalPlantao.objects.filter(
            unidade_assistencia=unidade_selecionada, date__year=year
        ).order_by('date')
        
        BudgetFormSet = modelformset_factory(
            OrcamentoMensalPlantao, 
            form=OrcamentoMensalPlantaoForm, 
            extra=0
        )

        if request.method == 'POST':
            formset = BudgetFormSet(request.POST, queryset=queryset)
            if formset.is_valid():
                formset.save()
                messages.success(request, f"Orçamento para '{unidade_selecionada.name}' salvo com sucesso!")
                return redirect(f"{request.path}?year={year}&unidade_assistencia={unidade_id}")
        else:
            formset = BudgetFormSet(queryset=queryset)

    years = range(current_year - 5, current_year + 2)
    context = {
        'formset': formset,
        'years': years,
        'selected_year': year,
        'unidades': unidades_da_empresa,
        'unidade_selecionada': unidade_selecionada,
    }
    return render(request, 'plantoes/orcamento_mensal.html', context)


@login_required
def plantoes_report_view(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        messages.error(request, "Por favor, selecione uma empresa primeiro.")
        return redirect('core:company_list')
    
    active_company = get_object_or_404(Company, pk=active_company_id, users=request.user)

    current_year = datetime.now().year
    year = int(request.GET.get('year', current_year))

    unidades = UnidadeAssistencia.objects.filter(company=active_company)
    # Filtramos o orçamento através da Unidade de Assistência
    orcamentos_mensais = OrcamentoMensalPlantao.objects.filter(
        unidade_assistencia__company=active_company, 
        date__year=year
    )
    lancamentos = LancamentoPlantao.objects.filter(company=active_company, date__year=year)

    budget_map = {b.date.month: b.valor_orcado for b in orcamentos_mensais}
    
    report_data_by_unit = []
    for unidade in unidades:
        unit_data = {
            'unidade': unidade,
            'plantoes': [],
            'totals_monthly': []
        }
        
        lancamentos_da_unidade = lancamentos.filter(unidade_assistencia=unidade)
        tipos_de_plantao = lancamentos_da_unidade.values('especialidade__name', 'turno__name').distinct()

        for tipo in tipos_de_plantao:
            plantao_row = {'name': f"{tipo['especialidade__name']} - {tipo['turno__name']}", 'monthly_actuals': []}
            for month in range(1, 13):
                # Pega o número de dias do mês/ano específico
                days_in_month = calendar.monthrange(year, month)[1]
                
                # Busca os lançamentos para este tipo de plantão neste mês
                lancamentos_do_mes = lancamentos_da_unidade.filter(
                    especialidade__name=tipo['especialidade__name'],
                    turno__name=tipo['turno__name'],
                    date__month=month
                )
                
                # Calcula o total projetado para o mês
                total_mes_projetado = Decimal(0)
                for lancamento in lancamentos_do_mes:
                    custo_diario = lancamento.quantidade * lancamento.valor_unitario
                    total_mes_projetado += custo_diario * days_in_month
                
                plantao_row['monthly_actuals'].append(total_mes_projetado)
            unit_data['plantoes'].append(plantao_row)
        
        total_realizado_unitario_mes = [sum(p['monthly_actuals'][i] for p in unit_data['plantoes']) for i in range(12)]

        for i in range(12):
            month = i + 1
            budgeted = budget_map.get(month, Decimal(0))
            actual = total_realizado_unitario_mes[i]
            unit_data['totals_monthly'].append({
                'budgeted': budgeted,
                'actual': actual,
                'is_over_budget': actual > budgeted if budgeted > 0 else False
            })

        if unit_data['plantoes']:
            report_data_by_unit.append(unit_data)

    years = range(current_year - 5, current_year + 2)
    context = {
        'report_data_by_unit': report_data_by_unit,
        'years': years,
        'selected_year': year,
        'months': ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    }
    return render(request, 'plantoes/plantoes_report.html', context)


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

@login_required
def urgencia_settings_view(request):
    """
    Tela principal que lista os Setores e suas Configurações de Escala.
    """
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return redirect('core:company_list')
    
    # Busca os setores da empresa
    setores = UrgenciaSetor.objects.filter(company_id=active_company_id).prefetch_related('configuracoes')
    
    context = {
        'setores': setores,
    }
    return render(request, 'plantoes/urgencia_settings.html', context)


# CRUD SETOR
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


# CRUD CONFIGURAÇÃO (GABARITO)
class UrgenciaConfigCreateView(LoginRequiredMixin, CreateView):
    model = UrgenciaConfiguracao
    form_class = UrgenciaConfiguracaoForm
    template_name = 'plantoes/urgencia_config_form.html' # Template específico para ficar bonito
    success_url = reverse_lazy('plantoes:urgencia_settings')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        active_company_id = self.request.session.get('active_company_id')
        # Passa a empresa para o form filtrar os setores
        kwargs['company'] = get_object_or_404(Company, pk=active_company_id)
        return kwargs

class UrgenciaConfigUpdateView(LoginRequiredMixin, UpdateView):
    model = UrgenciaConfiguracao
    form_class = UrgenciaConfiguracaoForm
    template_name = 'plantoes/urgencia_config_form.html'
    success_url = reverse_lazy('plantoes:urgencia_settings')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        active_company_id = self.request.session.get('active_company_id')
        kwargs['company'] = get_object_or_404(Company, pk=active_company_id)
        return kwargs
        
class UrgenciaConfigDeleteView(LoginRequiredMixin, DeleteView):
    model = UrgenciaConfiguracao
    template_name = 'plantoes/generic_confirm_delete.html'
    success_url = reverse_lazy('plantoes:urgencia_settings')

# LANÇAMENTO MENSAL (FOLHA DE URGÊNCIA)

@login_required
def urgencia_folha_view(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return redirect('core:company_list')

    # 1. Filtros de Data (Mês/Ano)
    today = timezone.now().date()
    month_str = request.GET.get('month', today.strftime('%Y-%m')) 
    
    try:
        # Cria a data de competência (Dia 1 do mês selecionado)
        competencia = datetime.strptime(f"{month_str}-01", "%Y-%m-%d").date()
    except ValueError:
        competencia = today.replace(day=1)

    # === CÁLCULO INTELIGENTE DE DIAS DO MÊS ===
    # A função monthrange retorna uma tupla (dia_semana, numero_dias).
    # Usamos o índice [1] para pegar quantos dias tem naquele mês/ano específico.
    _, dias_no_mes_atual = calendar.monthrange(competencia.year, competencia.month)

    # 2. Busca os lançamentos existentes para essa competência
    queryset = UrgenciaLancamento.objects.filter(
        company_id=active_company_id,
        competencia=competencia
    ).order_by('setor_nome', 'cargo_nome')

    # =========================================================
    # AÇÃO 1: SINCRONIZAR VALORES (ATUALIZAR COM A MATRIZ)
    # =========================================================
    if request.method == 'POST' and 'atualizar_valores' in request.POST:
        # Busca todas as configurações atuais da empresa
        configs = UrgenciaConfiguracao.objects.filter(setor__company_id=active_company_id)
        
        # Mapa para busca rápida
        config_map = {
            (c.setor.name, c.cargo): c for c in configs
        }
        
        count_updated = 0
        for lancamento in queryset:
            chave = (lancamento.setor_nome, lancamento.cargo_nome)
            config = config_map.get(chave)
            
            if config:
                # Atualiza valores fixos
                lancamento.qtd_dia = config.qtd_dia
                lancamento.valor_plantao_dia = config.valor_plantao_dia
                lancamento.qtd_noite = config.qtd_noite
                lancamento.valor_plantao_noite = config.valor_plantao_noite
                
                # ATUALIZAÇÃO INTELIGENTE:
                # Atualiza o campo "Dias Mês" para o calendário real (ex: Fev = 28)
                lancamento.dias_mes = dias_no_mes_atual
                
                lancamento.save()
                count_updated += 1
        
        if count_updated > 0:
            messages.success(request, f"{count_updated} linhas atualizadas com valores da Matriz e ajustadas para {dias_no_mes_atual} dias!")
        else:
            messages.info(request, "Nenhuma alteração encontrada na Matriz para os itens desta folha.")
            
        return redirect(f"{request.path}?month={month_str}")

    # =========================================================
    # AÇÃO 2: GERAR FOLHA (CRIAR NOVOS LANÇAMENTOS)
    # =========================================================
    if request.method == 'POST' and 'gerar_folha' in request.POST:
        configs = UrgenciaConfiguracao.objects.filter(setor__company_id=active_company_id)
        
        if not configs.exists():
            messages.error(request, "Nenhuma configuração encontrada. Cadastre a Matriz primeiro!")
        else:
            novos_lancamentos = []
            for cfg in configs:
                # Verifica duplicidade
                if not queryset.filter(setor_nome=cfg.setor.name, cargo_nome=cfg.cargo).exists():
                    novos_lancamentos.append(UrgenciaLancamento(
                        company_id=active_company_id,
                        competencia=competencia,
                        setor_nome=cfg.setor.name,
                        cargo_nome=cfg.cargo,
                        qtd_dia=cfg.qtd_dia,
                        valor_plantao_dia=cfg.valor_plantao_dia,
                        qtd_noite=cfg.qtd_noite,
                        valor_plantao_noite=cfg.valor_plantao_noite,
                        
                        # AQUI ESTÁ A MUDANÇA:
                        # Usa o cálculo do calendário (dias_no_mes_atual)
                        dias_mes=dias_no_mes_atual
                    ))
            
            if novos_lancamentos:
                UrgenciaLancamento.objects.bulk_create(novos_lancamentos)
                messages.success(request, f"Folha gerada com base em {dias_no_mes_atual} dias!")
            else:
                messages.info(request, "A folha já estava completa.")
            
            return redirect(f"{request.path}?month={month_str}")

    # =========================================================
    # AÇÃO 3: SALVAR EDIÇÕES DO GRID (FORMSET)
    # =========================================================
    LancamentoFormSet = modelformset_factory(
        UrgenciaLancamento,
        form=UrgenciaLancamentoForm,
        extra=0,
    )

    if request.method == 'POST' and 'salvar_grid' in request.POST:
        formset = LancamentoFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Valores atualizados com sucesso!")
            return redirect(f"{request.path}?month={month_str}")
        else:
            messages.error(request, "Erro ao salvar. Verifique os valores digitados.")
    else:
        formset = LancamentoFormSet(queryset=queryset)

    # 3. CÁLCULOS PARA OS CARDS (DASHBOARD)
    total_efetivo = sum(item.valor_efetivo for item in queryset)
    total_pega_plantao = sum(item.valor_pega_plantao for item in queryset)
    
    # Total Orçado (A soma de todas as metas)
    total_orcado = sum(item.total_escala_calculada for item in queryset)
    
    # Total Realizado (Com a lógica inteligente de fallback)
    total_realizado = sum(item.total_realizado for item in queryset)
    
    # Total do Saldo (A soma das diferenças)
    # Se negativo = Estourou o orçamento geral
    total_saldo = sum(item.saldo_orcamentario for item in queryset)

    context = {
        'formset': formset,
        'month_str': month_str,
        'competencia': competencia,
        
        # Variáveis para os Cards
        'total_orcado': total_orcado,       # Novo: Para saber a Meta Global
        'total_realizado': total_realizado,
        'total_saldo': total_saldo,         # Novo: O Veredito
        
        'total_efetivo': total_efetivo,
        'total_pega_plantao': total_pega_plantao,
        
        'tem_dados': queryset.exists(),
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

    # G. Equipe de Transporte (NOVO)
    # Lógica: Filtrar por competência (precisamos filtrar por mês/ano pois o campo é Data completa)
    transp_qs = TransporteLancamento.objects.filter(
        company_id=active_company_id, 
        competencia__year=competencia.year,
        competencia__month=competencia.month
    )
    # Cálculo manual: Quantidade * Valor Viagem (pois não tem campo total salvo)
    total_transporte = sum((item.quantidade_viagens * item.valor_viagem) for item in transp_qs)

    # 3. Consolidação
    # Lista de dicionários para facilitar o template
    items = [
        {
            'nome': 'Urgência e Emergência', 
            'valor': total_urgencia, 
            'url': 'plantoes:urgencia_folha', 
            'icon': 'bi-heart-pulse'
        },
        {
            'nome': 'Cirurgia Geral', 
            'valor': total_cirurgia, 
            'url': 'plantoes:cirurgia_folha', 
            'icon': 'bi-bandaid'
        },
        {
            'nome': 'Serviço de Nefrologia', 
            'valor': total_nefrologia, 
            'url': 'plantoes:nefrologia_folha', 
            'icon': 'bi-droplet'
        },
        {
            'nome': 'Bucomaxilo', 
            'valor': total_bucomaxilo, 
            'url': 'plantoes:bucomaxilo_folha', 
            'icon': 'bi-person-lines-fill'
        },
        {
            'nome': 'Residência Cirurgia', 
            'valor': total_residencia, 
            'url': 'plantoes:residencia_folha', 
            'icon': 'bi-mortarboard'
        },
        {
            'nome': 'Coordenações', 
            'valor': total_coordenacao, 
            'url': 'plantoes:coordenacao_folha', 
            'icon': 'bi-people'
        },
        {
            'nome': 'Equipe de Transporte', 
            'valor': total_transporte, 
            'url': 'plantoes:transporte_list', # Link aponta para a listagem
            'icon': 'bi-ambulance' # Ícone de ambulância/transporte
        },
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
        {'id': 'nefrologia', 'name': 'Serviço de Nefrologia', 'months': []},
        {'id': 'bucomaxilo', 'name': 'Bucomaxilo', 'months': []},
        {'id': 'residencia', 'name': 'Residência Cirurgia', 'months': []},
        {'id': 'coordenacao', 'name': 'Coordenações', 'months': []},
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

        # G. Transporte (CORREÇÃO AQUI)
        # Filtramos pelo ano e mês da competência
        qs_trans = TransporteLancamento.objects.filter(
            company_id=active_company_id, 
            competencia__year=current_year, 
            competencia__month=month
        )
        
        # Usamos o aggregate do banco para multiplicar Qtd * Valor e somar tudo
        agg_trans = qs_trans.aggregate(
            total=Sum(F('quantidade_viagens') * F('valor_viagem'), output_field=DecimalField())
        )
        
        # Se retornar None (sem lançamentos), usamos 0.00
        val_trans = agg_trans['total'] if agg_trans['total'] is not None else Decimal('0.00')


        current_values = {
            'urgencia': val_urg,
            'cirurgia': val_cir,
            'nefrologia': val_nef,
            'bucomaxilo': val_buc,
            'residencia': val_res,
            'coordenacao': val_coor,
            'transporte': val_trans
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