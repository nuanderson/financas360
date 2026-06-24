"""
Módulo de Relatórios — Finanças 360
====================================
Todas as views de relatório compartilham as mesmas 2 funções utilitárias
que buscam os dados do banco em apenas 2 queries por relatório, independente
do número de contas.
"""

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
import calendar
import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Value, DecimalField, Count, Q
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.contrib.auth.models import User
try:
    from weasyprint import HTML as WeasyHTML
    _WEASYPRINT_OK = True
except Exception:
    WeasyHTML = None
    _WEASYPRINT_OK = False

from ..models import Budget, ChartOfAccounts, Company, Transaction
from ..permissions import role_required, MANAGERS


def _parse_year(value, default=None):
    """
    Converte um valor de ano vindo do GET para int.
    Suporta '2026', '2.026' (locale BR com ponto como separador de milhar)
    e '2,026' (locale EN). Retorna `default` (ou ano atual) se inválido.
    """
    if default is None:
        default = date.today().year
    try:
        digits = re.sub(r'[\.,\s]', '', str(value))
        year = int(digits)
        if 1900 <= year <= 2200:
            return year
    except (ValueError, TypeError):
        pass
    return default


# ══════════════════════════════════════════════════════════════════
#  UTILITÁRIOS COMPARTILHADOS
# ══════════════════════════════════════════════════════════════════

def _load_account_tree(company):
    """
    Carrega todas as contas da empresa em memória.
    Retorna (account_map, children_map, root_ids).
    Apenas 1 query no banco.
    """
    accounts = list(
        ChartOfAccounts.objects.filter(company=company).order_by('code')
    )
    account_map = {a.id: a for a in accounts}
    children_map = defaultdict(list)   # parent_id -> [child_id, ...]
    root_ids = []

    for acc in accounts:
        if acc.parent_account_id:
            children_map[acc.parent_account_id].append(acc.id)
        else:
            root_ids.append(acc.id)

    return account_map, children_map, root_ids


def _compute_rolled_totals(raw_totals, account_map, children_map):
    """
    Calcula totais acumulados (conta pai = soma de si + todos os filhos).
    Trabalha inteiramente em memória — zero queries adicionais.
    """
    computed = {}

    def _roll(aid):
        if aid in computed:
            return computed[aid]
        total = raw_totals.get(aid, Decimal('0.00'))
        for child_id in children_map.get(aid, []):
            total += _roll(child_id)
        computed[aid] = total
        return total

    for aid in account_map:
        _roll(aid)

    return computed


def _fetch_period_raw(company, start_date, end_date):
    """
    1 query: totais por conta_id para o período.
    """
    return {
        row['account_id']: row['total']
        for row in Transaction.objects.filter(
            company=company,
            date__range=[start_date, end_date]
        ).values('account_id').annotate(
            total=Coalesce(Sum('amount'), Value(Decimal('0.00')))
        )
    }


def _build_lines(root_id, computed, account_map, children_map, level=0):
    """
    Gera lista plana ordenada de linhas do DRE para um nó raiz.
    """
    lines = []
    acc = account_map.get(root_id)
    if not acc:
        return lines
    lines.append({
        'account': acc,
        'total': computed.get(root_id, Decimal('0.00')),
        'level': level,
    })
    for child_id in children_map.get(root_id, []):
        lines.extend(_build_lines(child_id, computed, account_map, children_map, level + 1))
    return lines


def _get_root_accounts(company):
    """
    Retorna (root_receita, root_despesa) ou None se não encontrado.
    Tenta pelo código '1'/'2' primeiro; fallback por tipo sem pai.
    """
    try:
        root_r = ChartOfAccounts.objects.get(company=company, code='1')
    except ChartOfAccounts.DoesNotExist:
        root_r = ChartOfAccounts.objects.filter(
            company=company, account_type='R', parent_account__isnull=True
        ).order_by('code').first()

    try:
        root_d = ChartOfAccounts.objects.get(company=company, code='2')
    except ChartOfAccounts.DoesNotExist:
        root_d = ChartOfAccounts.objects.filter(
            company=company, account_type='D', parent_account__isnull=True
        ).order_by('code').first()

    return root_r, root_d


def _dre_context(company, start_date, end_date):
    """
    Monta o contexto completo do DRE em 2 queries.
    """
    root_r, root_d = _get_root_accounts(company)
    account_map, children_map, _ = _load_account_tree(company)
    raw = _fetch_period_raw(company, start_date, end_date)
    computed = _compute_rolled_totals(raw, account_map, children_map)

    revenue_lines = _build_lines(root_r.id, computed, account_map, children_map) if root_r else []
    expense_lines = _build_lines(root_d.id, computed, account_map, children_map) if root_d else []

    total_revenue = computed.get(root_r.id, Decimal('0.00')) if root_r else Decimal('0.00')
    total_expense = computed.get(root_d.id, Decimal('0.00')) if root_d else Decimal('0.00')
    net_result = total_revenue - total_expense

    # Adiciona % em relação ao total de receitas em cada linha
    for line in revenue_lines + expense_lines:
        if total_revenue > 0:
            line['pct'] = round((line['total'] / total_revenue) * 100, 1)
        else:
            line['pct'] = Decimal('0.0')

    return {
        'revenue_lines': revenue_lines,
        'expense_lines': expense_lines,
        'total_revenue': total_revenue,
        'total_expense': total_expense,
        'net_result': net_result,
    }


# ══════════════════════════════════════════════════════════════════
#  HUB DE RELATÓRIOS
# ══════════════════════════════════════════════════════════════════

@login_required
@role_required(*MANAGERS)
def reports_hub(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        messages.error(request, "Selecione uma empresa primeiro.")
        return redirect('core:company_list')
    active_company = get_object_or_404(Company, pk=active_company_id, users=request.user)
    return render(request, 'core/reports_hub.html', {'company': active_company})


# ══════════════════════════════════════════════════════════════════
#  RELATÓRIO 1 — DRE GERENCIAL (período livre)
# ══════════════════════════════════════════════════════════════════

@login_required
@role_required(*MANAGERS)
def dre_report(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        messages.error(request, "Selecione uma empresa primeiro.")
        return redirect('core:company_list')
    active_company = get_object_or_404(Company, pk=active_company_id, users=request.user)

    today = date.today()
    start_date_str = request.GET.get('start_date', today.replace(day=1).strftime('%Y-%m-%d'))
    end_date_str   = request.GET.get('end_date', today.replace(
        day=calendar.monthrange(today.year, today.month)[1]
    ).strftime('%Y-%m-%d'))

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date   = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        start_date = today.replace(day=1)
        end_date   = today.replace(day=calendar.monthrange(today.year, today.month)[1])
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str   = end_date.strftime('%Y-%m-%d')

    root_r, root_d = _get_root_accounts(active_company)
    if not root_r or not root_d:
        messages.error(request, "Plano de contas base não encontrado. Verifique se existem contas raiz.")
        return redirect('core:reports_hub')

    dre = _dre_context(active_company, start_date, end_date)

    context = {
        'company': active_company,
        'start_date_str': start_date_str,
        'end_date_str': end_date_str,
        **dre,
    }
    return render(request, 'core/dre_report.html', context)


@login_required
@role_required(*MANAGERS)
def dre_report_pdf(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return redirect('core:company_list')
    active_company = get_object_or_404(Company, pk=active_company_id, users=request.user)

    today = date.today()
    start_date_str = request.GET.get('start_date', today.replace(day=1).strftime('%Y-%m-%d'))
    end_date_str   = request.GET.get('end_date', today.replace(
        day=calendar.monthrange(today.year, today.month)[1]
    ).strftime('%Y-%m-%d'))

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date   = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        return redirect('core:dre_report')

    root_r, root_d = _get_root_accounts(active_company)
    if not root_r or not root_d:
        messages.error(request, "Plano de contas base não encontrado.")
        return redirect('core:reports_hub')

    dre = _dre_context(active_company, start_date, end_date)
    context = {
        'company': active_company,
        'start_date_str': start_date.strftime('%d/%m/%Y'),
        'end_date_str': end_date.strftime('%d/%m/%Y'),
        'generated_at': datetime.now().strftime('%d/%m/%Y %H:%M'),
        **dre,
    }
    html_string = render_to_string('core/dre_report_pdf.html', context)
    if not _WEASYPRINT_OK:
        return HttpResponse("PDF indisponível neste ambiente.", status=501)
    pdf = WeasyHTML(string=html_string).write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="DRE_{active_company.name}_{start_date_str}_{end_date_str}.pdf"'
    )
    return response


# ══════════════════════════════════════════════════════════════════
#  RELATÓRIO 2 — DRE MENSAL (12 colunas por ano)
# ══════════════════════════════════════════════════════════════════

@login_required
@role_required(*MANAGERS)
def dre_mensal(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        messages.error(request, "Selecione uma empresa primeiro.")
        return redirect('core:company_list')
    active_company = get_object_or_404(Company, pk=active_company_id, users=request.user)

    year = _parse_year(request.GET.get('year', ''))

    account_map, children_map, root_ids = _load_account_tree(active_company)

    # 1 query: totais por conta e mês
    monthly_rows = Transaction.objects.filter(
        company=active_company,
        date__year=year
    ).values('account_id', 'date__month').annotate(
        total=Coalesce(Sum('amount'), Value(Decimal('0.00')))
    )

    # Organiza raw em {account_id: {month: total}}
    monthly_raw_map = defaultdict(lambda: defaultdict(Decimal))
    for row in monthly_rows:
        monthly_raw_map[row['account_id']][row['date__month']] = row['total']

    # Calcula rolled totals para cada mês
    MONTHS = list(range(1, 13))
    monthly_computed = {}
    for m in MONTHS:
        raw = {aid: monthly_raw_map[aid].get(m, Decimal('0.00')) for aid in account_map}
        monthly_computed[m] = _compute_rolled_totals(raw, account_map, children_map)

    root_r, root_d = _get_root_accounts(active_company)
    if not root_r or not root_d:
        messages.error(request, "Plano de contas base não encontrado.")
        return redirect('core:reports_hub')

    def build_mensal_lines(root_id, level=0):
        lines = []
        acc = account_map.get(root_id)
        if not acc:
            return lines
        month_totals = [monthly_computed[m].get(root_id, Decimal('0.00')) for m in MONTHS]
        annual_total = sum(month_totals)
        lines.append({
            'account': acc,
            'month_totals': month_totals,
            'annual_total': annual_total,
            'level': level,
        })
        for child_id in children_map.get(root_id, []):
            lines.extend(build_mensal_lines(child_id, level + 1))
        return lines

    revenue_lines = build_mensal_lines(root_r.id)
    expense_lines = build_mensal_lines(root_d.id)

    # Totais por mês (linha de rodapé)
    month_totals_revenue = [
        sum(monthly_computed[m].get(root_r.id, Decimal('0.00')) for m in [m])
        for m in MONTHS
    ]
    month_totals_expense = [
        sum(monthly_computed[m].get(root_d.id, Decimal('0.00')) for m in [m])
        for m in MONTHS
    ]
    month_totals_result  = [r - e for r, e in zip(month_totals_revenue, month_totals_expense)]

    total_revenue = sum(month_totals_revenue)
    total_expense = sum(month_totals_expense)
    net_result    = total_revenue - total_expense

    MONTH_NAMES = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                   'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

    context = {
        'company': active_company,
        'year': year,
        'prev_year': year - 1,
        'next_year': year + 1,
        'month_names': MONTH_NAMES,
        'revenue_lines': revenue_lines,
        'expense_lines': expense_lines,
        'month_totals_revenue': month_totals_revenue,
        'month_totals_expense': month_totals_expense,
        'month_totals_result': month_totals_result,
        'total_revenue': total_revenue,
        'total_expense': total_expense,
        'net_result': net_result,
    }
    return render(request, 'core/dre_mensal.html', context)


@login_required
@role_required(*MANAGERS)
def dre_mensal_pdf(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return redirect('core:company_list')
    active_company = get_object_or_404(Company, pk=active_company_id, users=request.user)

    year = _parse_year(request.GET.get('year', ''))

    # Reutiliza a lógica do dre_mensal
    account_map, children_map, _ = _load_account_tree(active_company)
    monthly_rows = Transaction.objects.filter(
        company=active_company, date__year=year
    ).values('account_id', 'date__month').annotate(
        total=Coalesce(Sum('amount'), Value(Decimal('0.00')))
    )
    monthly_raw_map = defaultdict(lambda: defaultdict(Decimal))
    for row in monthly_rows:
        monthly_raw_map[row['account_id']][row['date__month']] = row['total']

    MONTHS = list(range(1, 13))
    monthly_computed = {}
    for m in MONTHS:
        raw = {aid: monthly_raw_map[aid].get(m, Decimal('0.00')) for aid in account_map}
        monthly_computed[m] = _compute_rolled_totals(raw, account_map, children_map)

    root_r, root_d = _get_root_accounts(active_company)
    if not root_r or not root_d:
        return redirect('core:reports_hub')

    def build_mensal_lines(root_id, level=0):
        lines = []
        acc = account_map.get(root_id)
        if not acc:
            return lines
        month_totals = [monthly_computed[m].get(root_id, Decimal('0.00')) for m in MONTHS]
        lines.append({'account': acc, 'month_totals': month_totals,
                      'annual_total': sum(month_totals), 'level': level})
        for child_id in children_map.get(root_id, []):
            lines.extend(build_mensal_lines(child_id, level + 1))
        return lines

    revenue_lines = build_mensal_lines(root_r.id)
    expense_lines = build_mensal_lines(root_d.id)
    month_totals_revenue = [monthly_computed[m].get(root_r.id, Decimal('0.00')) for m in MONTHS]
    month_totals_expense = [monthly_computed[m].get(root_d.id, Decimal('0.00')) for m in MONTHS]
    month_totals_result  = [r - e for r, e in zip(month_totals_revenue, month_totals_expense)]

    MONTH_NAMES = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                   'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

    context = {
        'company': active_company,
        'year': year,
        'month_names': MONTH_NAMES,
        'revenue_lines': revenue_lines,
        'expense_lines': expense_lines,
        'month_totals_revenue': month_totals_revenue,
        'month_totals_expense': month_totals_expense,
        'month_totals_result': month_totals_result,
        'total_revenue': sum(month_totals_revenue),
        'total_expense': sum(month_totals_expense),
        'net_result': sum(month_totals_revenue) - sum(month_totals_expense),
        'generated_at': datetime.now().strftime('%d/%m/%Y %H:%M'),
    }
    html_string = render_to_string('core/dre_mensal_pdf.html', context)
    if not _WEASYPRINT_OK:
        return HttpResponse("PDF indisponível neste ambiente.", status=501)
    pdf = WeasyHTML(string=html_string).write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="DRE_Mensal_{active_company.name}_{year}.pdf"'
    return response


# ══════════════════════════════════════════════════════════════════
#  RELATÓRIO 3 — DRE COMPARATIVO (dois períodos)
# ══════════════════════════════════════════════════════════════════

@login_required
@role_required(*MANAGERS)
def dre_comparativo(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        messages.error(request, "Selecione uma empresa primeiro.")
        return redirect('core:company_list')
    active_company = get_object_or_404(Company, pk=active_company_id, users=request.user)

    today = date.today()
    # Período A — padrão: mês atual
    a_start_str = request.GET.get('a_start', today.replace(day=1).strftime('%Y-%m-%d'))
    a_end_str   = request.GET.get('a_end',   today.replace(
        day=calendar.monthrange(today.year, today.month)[1]).strftime('%Y-%m-%d'))
    # Período B — padrão: mesmo mês do ano anterior
    prev = today.replace(year=today.year - 1)
    b_start_str = request.GET.get('b_start', prev.replace(day=1).strftime('%Y-%m-%d'))
    b_end_str   = request.GET.get('b_end',   prev.replace(
        day=calendar.monthrange(prev.year, prev.month)[1]).strftime('%Y-%m-%d'))

    try:
        a_start = datetime.strptime(a_start_str, '%Y-%m-%d').date()
        a_end   = datetime.strptime(a_end_str,   '%Y-%m-%d').date()
        b_start = datetime.strptime(b_start_str, '%Y-%m-%d').date()
        b_end   = datetime.strptime(b_end_str,   '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, "Data inválida.")
        return redirect('core:dre_comparativo')

    root_r, root_d = _get_root_accounts(active_company)
    if not root_r or not root_d:
        messages.error(request, "Plano de contas base não encontrado.")
        return redirect('core:reports_hub')

    account_map, children_map, _ = _load_account_tree(active_company)
    raw_a = _fetch_period_raw(active_company, a_start, a_end)
    raw_b = _fetch_period_raw(active_company, b_start, b_end)
    comp_a = _compute_rolled_totals(raw_a, account_map, children_map)
    comp_b = _compute_rolled_totals(raw_b, account_map, children_map)

    def build_comp_lines(root_id, level=0):
        lines = []
        acc = account_map.get(root_id)
        if not acc:
            return lines
        val_a = comp_a.get(root_id, Decimal('0.00'))
        val_b = comp_b.get(root_id, Decimal('0.00'))
        variacao_rs  = val_a - val_b
        variacao_pct = (variacao_rs / val_b * 100) if val_b != 0 else None
        lines.append({
            'account': acc,
            'val_a': val_a,
            'val_b': val_b,
            'variacao_rs': variacao_rs,
            'variacao_pct': variacao_pct,
            'level': level,
        })
        for child_id in children_map.get(root_id, []):
            lines.extend(build_comp_lines(child_id, level + 1))
        return lines

    revenue_lines = build_comp_lines(root_r.id)
    expense_lines = build_comp_lines(root_d.id)

    def _total(comp, root): return comp.get(root.id, Decimal('0.00'))

    rev_a, rev_b = _total(comp_a, root_r), _total(comp_b, root_r)
    exp_a, exp_b = _total(comp_a, root_d), _total(comp_b, root_d)

    context = {
        'company': active_company,
        'a_start_str': a_start_str, 'a_end_str': a_end_str,
        'b_start_str': b_start_str, 'b_end_str': b_end_str,
        'revenue_lines': revenue_lines,
        'expense_lines': expense_lines,
        'rev_a': rev_a, 'rev_b': rev_b,
        'exp_a': exp_a, 'exp_b': exp_b,
        'result_a': rev_a - exp_a,
        'result_b': rev_b - exp_b,
    }
    return render(request, 'core/dre_comparativo.html', context)


# ══════════════════════════════════════════════════════════════════
#  RELATÓRIO 4 — ORÇAMENTO VS. REALIZADO
# ══════════════════════════════════════════════════════════════════

@login_required
@role_required(*MANAGERS)
def budget_vs_actual_report(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        messages.error(request, "Selecione uma empresa primeiro.")
        return redirect('core:company_list')
    active_company = get_object_or_404(Company, pk=active_company_id, users=request.user)

    today = date.today()
    year  = _parse_year(request.GET.get('year', ''))
    month = request.GET.get('month', '')  # vazio = ano inteiro

    if month:
        month = int(month)
        start_date = date(year, month, 1)
        end_date   = date(year, month, calendar.monthrange(year, month)[1])
        periodo_label = f"{['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'][month-1]}/{year}"
    else:
        start_date = date(year, 1, 1)
        end_date   = date(year, 12, 31)
        periodo_label = f"Ano {year}"

    dias_no_ano    = Decimal(366 if calendar.isleap(year) else 365)
    dias_no_periodo = Decimal((end_date - start_date).days + 1)
    fator          = dias_no_periodo / dias_no_ano

    account_map, children_map, _ = _load_account_tree(active_company)
    raw = _fetch_period_raw(active_company, start_date, end_date)
    computed = _compute_rolled_totals(raw, account_map, children_map)

    # Busca médias mensais de orçamento do ano em 1 query
    # (amount = meta mensal; média dos meses cadastrados = referência do período)
    from django.db.models import Avg
    budget_map = {
        row['account_id']: row['avg'] or Decimal('0.00')
        for row in Budget.objects.filter(
            account__company=active_company, year=year
        ).values('account_id').annotate(avg=Avg('amount'))
    }

    root_r, root_d = _get_root_accounts(active_company)
    if not root_d:
        messages.error(request, "Plano de contas base não encontrado.")
        return redirect('core:reports_hub')

    def build_budget_lines(root_id, level=0):
        lines = []
        acc = account_map.get(root_id)
        if not acc:
            return lines
        realizado = computed.get(root_id, Decimal('0.00'))
        orcado_anual = budget_map.get(root_id, Decimal('0.00'))
        orcado_periodo = orcado_anual * fator
        desvio = realizado - orcado_periodo
        desvio_pct = (desvio / orcado_periodo * 100) if orcado_periodo != 0 else None

        # Semáforo: despesas acima do orçado = ruim (vermelho)
        if orcado_periodo == 0:
            semaforo = 'secondary'
        elif acc.account_type == 'D':
            semaforo = 'danger' if desvio > 0 else 'success'
        else:
            semaforo = 'success' if desvio >= 0 else 'warning'

        lines.append({
            'account': acc,
            'realizado': realizado,
            'orcado': orcado_periodo,
            'desvio': desvio,
            'desvio_pct': desvio_pct,
            'semaforo': semaforo,
            'level': level,
        })
        for child_id in children_map.get(root_id, []):
            lines.extend(build_budget_lines(child_id, level + 1))
        return lines

    expense_lines = build_budget_lines(root_d.id)
    revenue_lines = build_budget_lines(root_r.id) if root_r else []

    total_realizado = computed.get(root_d.id, Decimal('0.00'))
    total_orcado    = budget_map.get(root_d.id, Decimal('0.00')) * fator
    total_desvio    = total_realizado - total_orcado
    exec_pct        = (total_realizado / total_orcado * 100) if total_orcado > 0 else Decimal('0.00')

    context = {
        'company': active_company,
        'year': year,
        'month': month,
        'periodo_label': periodo_label,
        'months': list(range(1, 13)),
        'month_names': ['Janeiro','Fevereiro','Março','Abril','Maio','Junho',
                        'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'],
        'expense_lines': expense_lines,
        'revenue_lines': revenue_lines,
        'total_realizado': total_realizado,
        'total_orcado': total_orcado,
        'total_desvio': total_desvio,
        'exec_pct': exec_pct,
    }
    return render(request, 'core/budget_vs_actual_report.html', context)


# ══════════════════════════════════════════════════════════════════
#  RELATÓRIO 5 — EXTRATO ANALÍTICO
# ══════════════════════════════════════════════════════════════════

@login_required
@role_required(*MANAGERS)
def extrato_analitico(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        messages.error(request, "Selecione uma empresa primeiro.")
        return redirect('core:company_list')
    active_company = get_object_or_404(Company, pk=active_company_id, users=request.user)

    today = date.today()
    start_date_str = request.GET.get('start_date', today.replace(day=1).strftime('%Y-%m-%d'))
    end_date_str   = request.GET.get('end_date', today.replace(
        day=calendar.monthrange(today.year, today.month)[1]
    ).strftime('%Y-%m-%d'))
    account_type   = request.GET.get('account_type', '')
    account_id     = request.GET.get('account', '')

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date   = datetime.strptime(end_date_str,   '%Y-%m-%d').date()
    except ValueError:
        start_date = today.replace(day=1)
        end_date   = today.replace(day=calendar.monthrange(today.year, today.month)[1])

    transactions = Transaction.objects.filter(
        company=active_company,
        date__range=[start_date, end_date]
    ).select_related('account', 'created_by').order_by('date', 'account__code')

    if account_type:
        transactions = transactions.filter(account__account_type=account_type)
    if account_id:
        transactions = transactions.filter(account_id=account_id)

    total_receitas = transactions.filter(account__account_type='R').aggregate(
        t=Coalesce(Sum('amount'), Value(Decimal('0.00')))
    )['t']
    total_despesas = transactions.filter(account__account_type__in=['D','E']).aggregate(
        t=Coalesce(Sum('amount'), Value(Decimal('0.00')))
    )['t']

    all_accounts = ChartOfAccounts.objects.filter(company=active_company).order_by('code')

    export = request.GET.get('export')
    if export == 'pdf':
        context = {
            'company': active_company,
            'transactions': transactions,
            'start_date_str': start_date.strftime('%d/%m/%Y'),
            'end_date_str': end_date.strftime('%d/%m/%Y'),
            'total_receitas': total_receitas,
            'total_despesas': total_despesas,
            'saldo': total_receitas - total_despesas,
            'generated_at': datetime.now().strftime('%d/%m/%Y %H:%M'),
        }
        html_string = render_to_string('core/extrato_analitico_pdf.html', context)
        if not _WEASYPRINT_OK:
            return HttpResponse("PDF indisponivel neste ambiente.", status=501)
        pdf = WeasyHTML(string=html_string).write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="Extrato_{active_company.name}_{start_date_str}_{end_date_str}.pdf"'
        )
        return response

    context = {
        'company': active_company,
        'transactions': transactions,
        'start_date_str': start_date_str,
        'end_date_str': end_date_str,
        'account_type': account_type,
        'account_id': account_id,
        'all_accounts': all_accounts,
        'total_receitas': total_receitas,
        'total_despesas': total_despesas,
        'saldo': total_receitas - total_despesas,
        'total_count': transactions.count(),
    }
    return render(request, 'core/extrato_analitico.html', context)


# ══════════════════════════════════════════════════════════════════
#  RELATÓRIO 6 — PRODUTIVIDADE DA EQUIPE
# ══════════════════════════════════════════════════════════════════

@login_required
@role_required(*MANAGERS)
def productivity_report(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        messages.error(request, "Selecione uma empresa primeiro.")
        return redirect('core:company_list')
    active_company = get_object_or_404(Company, pk=active_company_id, users=request.user)

    today = date.today()
    start_date_str = request.GET.get('start_date', today.replace(day=1).strftime('%Y-%m-%d'))
    end_date_str   = request.GET.get('end_date', today.strftime('%Y-%m-%d'))
    user_filter_id = request.GET.get('user_id', '')

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date   = datetime.strptime(end_date_str,   '%Y-%m-%d').date()
    except ValueError:
        start_date = today.replace(day=1)
        end_date   = today

    qs = Transaction.objects.filter(
        company=active_company,
        date__range=[start_date, end_date],
    )
    if user_filter_id:
        qs = qs.filter(created_by_id=user_filter_id)

    # ── Resumo por usuário ────────────────────────────────────────
    by_user = (
        qs.values('created_by__id', 'created_by__username',
                  'created_by__first_name', 'created_by__last_name')
        .annotate(
            total_lancamentos=Count('id'),
            qtd_receitas=Count('id', filter=Q(account__account_type='R')),
            qtd_despesas=Count('id', filter=Q(account__account_type__in=['D', 'E'])),
            valor_receitas=Coalesce(
                Sum('amount', filter=Q(account__account_type='R')),
                Value(Decimal('0.00')), output_field=DecimalField()),
            valor_despesas=Coalesce(
                Sum('amount', filter=Q(account__account_type__in=['D', 'E'])),
                Value(Decimal('0.00')), output_field=DecimalField()),
            valor_total=Coalesce(Sum('amount'), Value(Decimal('0.00')),
                                 output_field=DecimalField()),
        )
        .order_by('-total_lancamentos')
    )

    # Nome amigável para exibição
    user_summary = []
    for row in by_user:
        fn = row['created_by__first_name'] or ''
        ln = row['created_by__last_name'] or ''
        full = f"{fn} {ln}".strip() or row['created_by__username'] or '(sem usuário)'
        user_summary.append({**row, 'display_name': full})

    # ── Evolução diária por usuário ───────────────────────────────
    daily_qs = (
        qs.values('date', 'created_by__username',
                  'created_by__first_name', 'created_by__last_name')
        .annotate(
            lancamentos=Count('id'),
            valor=Coalesce(Sum('amount'), Value(Decimal('0.00')),
                           output_field=DecimalField()),
        )
        .order_by('-date', '-lancamentos')
    )
    daily_rows = []
    for row in daily_qs:
        fn = row['created_by__first_name'] or ''
        ln = row['created_by__last_name'] or ''
        full = f"{fn} {ln}".strip() or row['created_by__username'] or '(sem usuário)'
        daily_rows.append({**row, 'display_name': full})

    # ── Totais gerais ─────────────────────────────────────────────
    totals = qs.aggregate(
        total_lancamentos=Count('id'),
        total_valor=Coalesce(Sum('amount'), Value(Decimal('0.00')),
                             output_field=DecimalField()),
    )
    usuarios_ativos = qs.values('created_by').distinct().count()
    top_user = user_summary[0] if user_summary else None

    # Lista de usuários da empresa para o filtro
    company_users = User.objects.filter(
        companies=active_company
    ).order_by('username')

    context = {
        'company':        active_company,
        'start_date_str': start_date_str,
        'end_date_str':   end_date_str,
        'user_filter_id': user_filter_id,
        'company_users':  company_users,
        'user_summary':   user_summary,
        'daily_rows':     daily_rows,
        'total_lancamentos': totals['total_lancamentos'],
        'total_valor':    totals['total_valor'],
        'usuarios_ativos': usuarios_ativos,
        'top_user':       top_user,
    }
    return render(request, 'core/productivity_report.html', context)


# Mantém compatibilidade retroativa com código legado
def get_account_total(account, transactions):
    """Deprecated — use _dre_context() instead."""
    total = transactions.filter(account=account).aggregate(
        total=Coalesce(Sum('amount'), Value(0.0), output_field=DecimalField())
    )['total']
    for sub in account.sub_accounts.all():
        total += get_account_total(sub, transactions)
    return total
