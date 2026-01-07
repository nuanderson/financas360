import locale
import calendar
from django.core.mail import send_mail
from decimal import Decimal
from django.db.models import Sum, F
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.contrib import messages
from django.forms import modelformset_factory, formset_factory
from datetime import datetime, date
from django.conf import settings

from .models import Especialidade, Turno, UnidadeAssistencia, OrcamentoMensalPlantao, LancamentoPlantao
from .forms import EspecialidadeForm, TurnoForm, UnidadeAssistenciaForm, OrcamentoMensalPlantaoForm, LancamentoPlantaoForm

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