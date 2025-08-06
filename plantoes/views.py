import locale
from django.core.mail import send_mail
from decimal import Decimal
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.contrib import messages
from django.forms import modelformset_factory, formset_factory
from datetime import datetime, date

from .models import Especialidade, Turno, UnidadeAssistencia, OrcamentoPlantao, LancamentoPlantao
from .forms import EspecialidadeForm, TurnoForm, UnidadeAssistenciaForm, OrcamentoPlantaoForm, LancamentoPlantaoForm

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

# --- Mixin de Segurança ---
# --- Mixin para filtrar QuerySets (usado por Update e Delete) ---
class CompanyQuerysetMixin(LoginRequiredMixin):
    def get_queryset(self):
        active_company_id = self.request.session.get('active_company_id')
        if not active_company_id:
            return self.model.objects.none()

        active_company = get_object_or_404(Company, pk=active_company_id, users=self.request.user)
        return self.model.objects.filter(company=active_company)


# --- Mixin para salvar o formulário (usado por Create e Update) ---
class CompanyFormMixin(LoginRequiredMixin):
    def form_valid(self, form):
        active_company_id = self.request.session.get('active_company_id')
        active_company = get_object_or_404(Company, pk=active_company_id, users=self.request.user)
        form.instance.company = active_company
        return super().form_valid(form)


# --- CRUD de Especialidade ---
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

class OrcamentoPlantaoListView(CompanyQuerysetMixin, ListView):
    model = OrcamentoPlantao
    template_name = 'plantoes/orcamento_plantao_list.html'
    context_object_name = 'orcamentos'

    def get_queryset(self):
        # Busca a empresa ativa da sessão.
        active_company_id = self.request.session.get('active_company_id')
        if not active_company_id:
            return OrcamentoPlantao.objects.none()  # Retorna queryset vazio se não houver empresa.

        # Garante que o usuário tem permissão para a empresa ativa.
        active_company = get_object_or_404(Company, pk=active_company_id, users=self.request.user)
        return OrcamentoPlantao.objects.filter(company=active_company).select_related(
            'especialidade', 'turno', 'unidade_assistencia'
        )

class OrcamentoPlantaoCreateView(CompanyFormMixin, CreateView):
    model = OrcamentoPlantao
    form_class = OrcamentoPlantaoForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:orcamento_list')

    def get_form_kwargs(self):
        # Passa a 'company' para o __init__ do formulário para filtrar os dropdowns
        kwargs = super().get_form_kwargs()
        active_company_id = self.request.session.get('active_company_id')
        if active_company_id:
            kwargs['company'] = get_object_or_404(Company, pk=active_company_id)
        return kwargs

class OrcamentoPlantaoUpdateView(CompanyQuerysetMixin, CompanyFormMixin, UpdateView):
    model = OrcamentoPlantao
    form_class = OrcamentoPlantaoForm
    template_name = 'plantoes/generic_form.html'
    success_url = reverse_lazy('plantoes:orcamento_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        active_company_id = self.request.session.get('active_company_id')
        if active_company_id:
            kwargs['company'] = get_object_or_404(Company, pk=active_company_id)
        return kwargs

class OrcamentoPlantaoDeleteView(CompanyQuerysetMixin, DeleteView):
    model = OrcamentoPlantao
    template_name = 'plantoes/generic_confirm_delete.html'
    success_url = reverse_lazy('plantoes:orcamento_list')


@login_required
def lancamento_plantao_view(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        messages.error(request, "Por favor, selecione uma empresa primeiro.")
        return redirect('core:company_list')
    active_company = get_object_or_404(Company, pk=active_company_id, users=request.user)

    current_year = datetime.now().year
    current_month = datetime.now().month

    # Lemos os valores do filtro como texto
    year_str = request.GET.get('year', str(current_year))
    month_str = request.GET.get('month', str(current_month))

    # Removemos o ponto do ano e convertemos para inteiro
    year = int(year_str.replace('.', ''))
    month = int(month_str)

    orcamentos = OrcamentoPlantao.objects.filter(company=active_company).order_by('pk')

    for orc in orcamentos:
        LancamentoPlantao.objects.get_or_create(
            orcamento=orc, date__year=year, date__month=month,
            defaults={'valor_realizado': 0, 'date': date(year, month, 1)}
        )

    queryset = LancamentoPlantao.objects.filter(
        orcamento__in=orcamentos, date__year=year, date__month=month
    ).order_by('orcamento__pk')

    LancamentoFormSet = modelformset_factory(LancamentoPlantao, form=LancamentoPlantaoForm, extra=0)

    if request.method == 'POST':
        formset = LancamentoFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            instances = formset.save()
            messages.success(request, "Lançamentos salvos com sucesso!")

            # --- INÍCIO DA LÓGICA DE ENVIO DE E-MAIL RESTAURADA ---
            for lancamento in instances:
                orcamento = lancamento.orcamento

                # Pega o nome do campo do mês atual (ex: 'jul_budget')
                month_field_name = f"{lancamento.date.strftime('%b').lower()}_budget"
                # Busca o valor orçado para o mês específico no objeto de orçamento
                monthly_budget = getattr(orcamento, month_field_name, 0)

                # Verifica se o valor realizado ultrapassou o orçamento
                if monthly_budget > 0 and lancamento.valor_realizado > monthly_budget:
                    subject = f"[Alerta] Orçamento de Plantão Excedido - {orcamento}"
                    message = f"""
Olá Gestor,

O valor realizado para o plantão abaixo excedeu o orçamento para o mês de {lancamento.date.strftime('%B de %Y')}.

Detalhes do Plantão:
- Especialidade: {orcamento.especialidade.name}
- Unidade: {orcamento.unidade_assistencia.name}
- Turno: {orcamento.turno.name}

- Valor Orçado para o Mês: R$ {monthly_budget}
- Valor Realizado: R$ {lancamento.valor_realizado}

Observações do Lançamento:
{lancamento.observacoes or 'Nenhuma observação fornecida.'}

Atenciosamente,
Sistema Finanças 360
"""
                    recipient_list = [request.user.email]
                    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
            # --- FIM DA LÓGICA DE ENVIO DE E-MAIL ---

            return redirect(f"{request.path}?year={year}&month={month}")
    else:
        formset = LancamentoFormSet(queryset=queryset)

    # Combina os formulários do formset com seus objetos de orçamento correspondentes
    forms_with_orcamentos = zip(formset.forms, orcamentos)

    try:
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
    except locale.Error:
        locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil')

    years = range(current_year - 5, current_year + 2)
    months = [(i, datetime(current_year, i, 1).strftime('%B')) for i in range(1, 13)]

    context = {
        'formset': formset,
        'forms_with_orcamentos': forms_with_orcamentos,
        'years': years,
        'months': months,
        'selected_year': year,
        'selected_month': month,
    }
    return render(request, 'plantoes/lancamento_plantao.html', context)

@login_required
def plantoes_budget_dashboard(request):
    # Busca a empresa ativa diretamente da sessão
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        messages.error(request, "Por favor, selecione uma empresa primeiro.")
        return redirect('core:company_list')

    active_company = get_object_or_404(Company, pk=active_company_id, users=request.user)

    current_year = datetime.now().year
    year = int(request.GET.get('year', current_year))

    # 1. Busca os dados base
    orcamentos = OrcamentoPlantao.objects.filter(company=active_company).select_related(
        'especialidade', 'turno', 'unidade_assistencia'
    )
    lancamentos = LancamentoPlantao.objects.filter(
        orcamento__company=active_company,
        date__year=year
    )

    # 2. Pré-calcula os totais realizados mensais para otimização
    monthly_totals = {}
    month_totals_qs = lancamentos.values('orcamento_id', 'date__month').annotate(total=Sum('valor_realizado'))
    for item in month_totals_qs:
        monthly_totals[(item['orcamento_id'], item['date__month'])] = item['total']

    # 3. Constrói a estrutura de dados para o template
    report_data = []
    days_in_month_avg = Decimal(30.4375) # Média de dias no mês para o cálculo do orçamento

    for orcamento in orcamentos:
        row_data = {'orcamento': orcamento, 'monthly_data': []}

        # Calcula o orçamento mensal com base na planilha de referência
        monthly_budget = orcamento.valor_plantao * orcamento.quantidade
        if orcamento.tipo_plantao == 12:
            # Na planilha, plantões de 12h são por dia (Dia + Noite)
            monthly_budget = monthly_budget * 2 * days_in_month_avg
        else: # 24h
            monthly_budget = monthly_budget * days_in_month_avg

        row_data['monthly_budget'] = monthly_budget.quantize(Decimal('0.01'))

        # Monta o "pacote" para cada um dos 12 meses
        for month in range(1, 13):
            actual = monthly_totals.get((orcamento.id, month), Decimal(0))

            variation = Decimal(0)
            if month > 1:
                previous_actual = monthly_totals.get((orcamento.id, month - 1), Decimal(0))
                if previous_actual > 0:
                    variation = ((actual - previous_actual) / previous_actual) * 100

            is_over_budget = actual > row_data['monthly_budget']

            row_data['monthly_data'].append({
                'actual': actual,
                'variation': variation,
                'is_over_budget': is_over_budget,
            })
        report_data.append(row_data)

    years = range(current_year - 5, current_year + 2)

    context = {
        'report_data': report_data,
        'years': years,
        'selected_year': year,
        'months': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    }
    return render(request, 'plantoes/plantoes_budget_dashboard.html', context)