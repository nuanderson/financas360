from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Value, DecimalField
from django.db.models.functions import Coalesce
from datetime import date, datetime
from decimal import Decimal
import calendar

from ..models import Company, Transaction, Budget
from ..permissions import has_role, NON_PLANTOES


@login_required
def dashboard_dispatcher(request, company_id=None):
    # Analista de Plantões não acessa o dashboard financeiro
    if not has_role(request.user, *NON_PLANTOES):
        messages.error(request, "Você não tem permissão para acessar o painel financeiro.")
        return redirect('core:company_list')

    c_id = company_id or request.session.get('company_id') or request.session.get('active_company_id')

    if not c_id:
        return redirect('core:company_list')

    company = get_object_or_404(Company, pk=c_id, users=request.user)

    request.session['company_id'] = company.id
    request.session['active_company_id'] = company.id

    if company.management_type == 'Pública':
        return dashboard_orcamento(request, company)
    else:
        return dashboard_lucratividade(request, company)


@login_required
def dashboard_lucratividade(request, company):
    today = date.today()
    start_date_str = request.GET.get('start_date', today.replace(day=1).strftime('%Y-%m-%d'))
    end_date_str = request.GET.get('end_date',
                                   (today.replace(day=calendar.monthrange(today.year, today.month)[1])).strftime('%Y-%m-%d'))
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    transactions = Transaction.objects.filter(company=company, date__range=[start_date, end_date])

    total_revenue = transactions.filter(account__account_type='R').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = transactions.filter(account__account_type__in=['D', 'E']).aggregate(Sum('amount'))['amount__sum'] or 0
    net_result = total_revenue - total_expenses

    def get_pct(prefix, base):
        total = Transaction.objects.filter(
            company=company, date__range=[start_date, end_date], account__code__startswith=prefix
        ).aggregate(total=Coalesce(Sum('amount'), Value(Decimal('0.00'))))['total']
        return (total / base * 100) if base > 0 else 0, total

    percentual_folha_lc, _ = get_pct("2.01.1.01", total_expenses)
    percentual_rec_serv_terceiros, _ = get_pct("1.01.01", total_revenue)
    percentual_rec_convenios, _ = get_pct("1.01.02", total_revenue)
    percentual_rec_particulares, _ = get_pct("1.01.03", total_revenue)
    percentual_rec_conv_desconto, _ = get_pct("1.01.04", total_revenue)
    percentual_rec_fundo_programa_emenda, _ = get_pct("1.01.05", total_revenue)
    percentual_rec_outras_receitas, _ = get_pct("1.01.06", total_revenue)

    context = {
        'company': company,
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'net_result': net_result,
        'start_date_str': start_date_str,
        'end_date_str': end_date_str,
        'percentual_folha_lc': percentual_folha_lc,
        'percentual_rec_serv_terceiros': percentual_rec_serv_terceiros,
        'percentual_rec_convenios': percentual_rec_convenios,
        'percentual_rec_particulares': percentual_rec_particulares,
        'percentual_rec_conv_desconto': percentual_rec_conv_desconto,
        'percentual_rec_fundo_programa_emenda': percentual_rec_fundo_programa_emenda,
        'percentual_rec_outras_receitas': percentual_rec_outras_receitas,
    }
    return render(request, 'core/dashboard_lucratividade.html', context)


@login_required
def dashboard_orcamento(request, company):
    today = date.today()
    competence = request.GET.get('competence')

    if competence:
        try:
            year, month = map(int, competence.split('-'))
            start_date = date(year, month, 1)
            last_day = calendar.monthrange(year, month)[1]
            end_date = date(year, month, last_day)
        except ValueError:
            start_date = today.replace(day=1)
            end_date = today.replace(day=calendar.monthrange(today.year, today.month)[1])
            competence = start_date.strftime('%Y-%m')
    else:
        start_date = today.replace(day=1)
        end_date = today.replace(day=calendar.monthrange(today.year, today.month)[1])
        competence = start_date.strftime('%Y-%m')

    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    total_receitas = Transaction.objects.filter(
        company=company, date__range=[start_date, end_date], account__account_type='R'
    ).aggregate(total=Coalesce(Sum('amount'), Value(Decimal('0.00'))))['total']

    total_realizado = Transaction.objects.filter(
        company=company, date__range=[start_date, end_date], account__account_type__in=['D', 'E']
    ).aggregate(total=Coalesce(Sum('amount'), Value(Decimal('0.00'))))['total']

    # Soma os budgets mensais dos meses do período selecionado
    months_in_period = list(range(start_date.month, end_date.month + 1)) if start_date.year == end_date.year else list(range(1, 13))
    total_orcado_periodo = Budget.objects.filter(
        account__company=company,
        year=start_date.year,
        month__in=months_in_period,
        account__account_type__in=['D', 'E']
    ).aggregate(total=Coalesce(Sum('amount'), Value(Decimal('0.00'))))['total']

    percentual_executado = 0
    if total_orcado_periodo > 0:
        percentual_executado = (total_realizado / total_orcado_periodo) * 100

    def get_group_total(prefix_code):
        return Transaction.objects.filter(
            company=company, date__range=[start_date, end_date], account__code__startswith=prefix_code
        ).aggregate(total=Coalesce(Sum('amount'), Value(Decimal('0.00'))))['total']

    glosas_total = get_group_total("1.03")
    repasse_total = get_group_total("1.01")
    percentual_glosa = (glosas_total / repasse_total * 100) if repasse_total > 0 else 0

    folha_total = get_group_total("2.01.01")
    percentual_folha = (folha_total / total_realizado * 100) if total_realizado > 0 else 0

    receitas_extra = Transaction.objects.filter(
        company=company, date__range=[start_date, end_date], account__code="1.04"
    ).aggregate(total=Coalesce(Sum('amount'), Value(Decimal('0.00'))))['total']

    servicos_terceiros = get_group_total("2.01.03")
    percentual_servicos_terceiros = (servicos_terceiros / total_realizado * 100) if total_realizado > 0 else 0

    materiais = get_group_total("2.01.02")
    percentual_materiais = (materiais / total_realizado * 100) if total_realizado > 0 else 0

    apoio_gestao = get_group_total("2.01.04")
    percentual_apoio_gestao = (apoio_gestao / total_realizado * 100) if total_realizado > 0 else 0

    outras_despesas = get_group_total("2.01.05")
    percentual_outras_despesas = (outras_despesas / total_realizado * 100) if total_realizado > 0 else 0

    despesas_administrativas = get_group_total("2.01.06")
    percentual_despesas_administrativas = (despesas_administrativas / total_realizado * 100) if total_realizado > 0 else 0

    progress_color = 'success'
    if percentual_executado > 95:
        progress_color = 'danger'
    elif percentual_executado > 80:
        progress_color = 'warning'

    resultado_liquido = total_receitas - total_realizado

    context = {
        'company': company,
        'competence': competence,
        'start_date_str': start_date_str,
        'end_date_str': end_date_str,
        'total_receitas': total_receitas,
        'total_realizado': total_realizado,
        'total_orcado_periodo': total_orcado_periodo,
        'resultado_liquido': resultado_liquido,
        'percentual_executado_display': percentual_executado,
        'percentual_executado_raw': f'{percentual_executado:.2f}'.replace(',', '.'),
        'progress_color': progress_color,
        'percentual_glosa': percentual_glosa,
        'percentual_folha': percentual_folha,
        'receitas_extra': receitas_extra,
        'servicos_terceiros': servicos_terceiros,
        'percentual_servicos_terceiros': percentual_servicos_terceiros,
        'materiais': materiais,
        'percentual_materiais': percentual_materiais,
        'apoio_gestao': apoio_gestao,
        'percentual_apoio_gestao': percentual_apoio_gestao,
        'outras_despesas': outras_despesas,
        'percentual_outras_despesas': percentual_outras_despesas,
        'despesas_administrativas': despesas_administrativas,
        'percentual_despesas_administrativas': percentual_despesas_administrativas,
    }
    return render(request, 'core/dashboard_orcamento.html', context)
