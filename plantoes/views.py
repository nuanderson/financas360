import locale
import calendar
from django.core.mail import send_mail
from decimal import Decimal
from django.db.models import Sum, F, Avg, FloatField
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

from .models import Especialidade, Turno, UnidadeAssistencia, OrcamentoMensalPlantao, LancamentoPlantao, TransporteLancamento, UrgenciaConfiguracao, UrgenciaSetor, UrgenciaLancamento, CirurgiaConfiguracao, CirurgiaLancamento, CirurgiaSetor 
from .forms import EspecialidadeForm, TurnoForm, UnidadeAssistenciaForm, OrcamentoMensalPlantaoForm, LancamentoPlantaoForm, TransporteForm, UrgenciaConfiguracaoForm, UrgenciaSetorForm, UrgenciaLancamentoForm, CirurgiaConfiguracaoForm, CirurgiaSetorForm, CirurgiaLancamentoForm

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