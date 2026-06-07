from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Value, DecimalField
from django.db.models.functions import Coalesce
from datetime import date, datetime
from decimal import Decimal
from dateutil.relativedelta import relativedelta
import calendar

from ..models import Company, Transaction, Budget, ChartOfAccounts


@login_required
def expense_chart_data(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return JsonResponse({'error': 'Nenhuma empresa ativa'}, status=404)

    company = get_object_or_404(Company, pk=active_company_id, users=request.user)

    today = date.today()
    start_date_str = request.GET.get('start_date', today.replace(day=1).strftime('%Y-%m-%d'))
    end_date_str = request.GET.get('end_date', (today.replace(day=calendar.monthrange(today.year, today.month)[1])).strftime('%Y-%m-%d'))

    expenses = Transaction.objects.filter(
        company=company,
        account__account_type__in=['D', 'E'],
        date__range=[start_date_str, end_date_str]
    )

    category_expenses = expenses.values('account__parent_account__name').annotate(
        total=Coalesce(Sum('amount'), Value(0.0), output_field=DecimalField())
    ).order_by('-total')

    labels = [item['account__parent_account__name'] or 'Sem Categoria' for item in category_expenses]
    data = [float(item['total']) for item in category_expenses]

    return JsonResponse({'labels': labels, 'data': data})


@login_required
def revenue_expense_summary_data(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return JsonResponse({'error': 'Nenhuma empresa ativa'}, status=404)

    company = get_object_or_404(Company, pk=active_company_id, users=request.user)

    today = date.today()
    start_date_str = request.GET.get('start_date', today.replace(day=1).strftime('%Y-%m-%d'))
    end_date_str = request.GET.get('end_date', (today.replace(day=calendar.monthrange(today.year, today.month)[1])).strftime('%Y-%m-%d'))
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    labels = []
    revenue_data = []
    expense_data = []

    current_date = start_date
    while current_date <= end_date:
        target_month = current_date.month
        target_year = current_date.year
        labels.append(current_date.strftime("%b/%Y"))

        transactions = Transaction.objects.filter(company=company, date__year=target_year, date__month=target_month)

        revenue = transactions.filter(account__account_type='R').aggregate(
            total=Coalesce(Sum('amount'), Value(0.0), output_field=DecimalField())
        )['total']
        expense = transactions.filter(account__account_type__in=['D', 'E']).aggregate(
            total=Coalesce(Sum('amount'), Value(0.0), output_field=DecimalField())
        )['total']

        revenue_data.append(float(revenue))
        expense_data.append(float(expense))
        current_date = (current_date.replace(day=1) + relativedelta(months=1))

    return JsonResponse({'labels': labels, 'revenue_data': revenue_data, 'expense_data': expense_data})


@login_required
def budget_deviations_chart_data(request):
    active_company_id = request.session.get('active_company_id')
    company = get_object_or_404(Company, pk=active_company_id, users=request.user)

    today = date.today()
    start_date_str = request.GET.get('start_date', today.replace(day=1).strftime('%Y-%m-%d'))
    end_date_str = request.GET.get('end_date', (today.replace(day=calendar.monthrange(today.year, today.month)[1])).strftime('%Y-%m-%d'))

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Data inválida'}, status=400)

    account_ids_budget = Budget.objects.filter(
        account__company=company,
        year=start_date.year,
        account__account_type__in=['D', 'E']
    ).values_list('account_id', flat=True)

    account_ids_trans = Transaction.objects.filter(
        company=company,
        date__range=[start_date, end_date],
        account__account_type__in=['D', 'E']
    ).values_list('account_id', flat=True)

    relevant_account_ids = set(list(account_ids_budget) + list(account_ids_trans))
    accounts = ChartOfAccounts.objects.filter(id__in=relevant_account_ids)

    deviations = []
    dias_no_ano = Decimal(366 if calendar.isleap(start_date.year) else 365)
    dias_no_periodo = Decimal((end_date - start_date).days + 1)
    fator_proporcional = dias_no_periodo / dias_no_ano

    # Meses cobertos pelo período
    months_in_period = list(range(start_date.month, end_date.month + 1)) if start_date.year == end_date.year else list(range(1, 13))

    for account in accounts:
        # Soma os budgets mensais dos meses do período
        orcado_periodo = Budget.objects.filter(
            account=account,
            year=start_date.year,
            month__in=months_in_period
        ).aggregate(total=Coalesce(Sum('amount'), Value(Decimal(0))))['total']

        realizado = Transaction.objects.filter(
            account=account,
            date__range=[start_date, end_date]
        ).aggregate(total=Coalesce(Sum('amount'), Value(Decimal(0))))['total']

        if orcado_periodo > 0 or realizado > 0:
            desvio = realizado - orcado_periodo
            deviations.append({'name': f"{account.code} - {account.name}", 'desvio': float(desvio)})

    deviations.sort(key=lambda x: abs(x['desvio']), reverse=True)
    top_deviations = deviations[:10]

    return JsonResponse({
        'labels': [item['name'] for item in top_deviations],
        'data': [item['desvio'] for item in top_deviations],
        'colors': ['#dc3545' if v > 0 else '#198754' for v in [item['desvio'] for item in top_deviations]]
    })


@login_required
def budget_vs_actual_timeline_data(request):
    active_company_id = request.session.get('active_company_id')
    company = get_object_or_404(Company, pk=active_company_id, users=request.user)

    labels = []
    budget_data = []
    actual_data = []

    for i in range(12):
        target_date = datetime.now() - relativedelta(months=i)
        target_year = target_date.year
        target_month = target_date.month
        labels.append(target_date.strftime("%b/%Y"))

        # Busca diretamente o budget do mês específico
        orcamento_mes_qs = Budget.objects.filter(
            account__company=company,
            year=target_year,
            month=target_month,
            account__account_type__in=['D', 'E']
        ).aggregate(total=Sum('amount'))['total']

        orcamento_mes = float(orcamento_mes_qs) if orcamento_mes_qs is not None else None

        budget_data.append(orcamento_mes)

        realizado_mes = Transaction.objects.filter(
            company=company,
            account__account_type__in=['D', 'E'],
            date__year=target_year,
            date__month=target_month
        ).aggregate(total=Coalesce(Sum('amount'), Value(Decimal(0))))['total']
        actual_data.append(float(realizado_mes))

    labels.reverse()
    budget_data.reverse()
    actual_data.reverse()

    return JsonResponse({'labels': labels, 'budget_data': budget_data, 'actual_data': actual_data})


@login_required
def expense_percentage_chart_data(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        return JsonResponse({'error': 'No active company'}, status=400)

    company = get_object_or_404(Company, pk=active_company_id, users=request.user)

    today = date.today()
    start_date_str = request.GET.get('start_date', today.replace(day=1).strftime('%Y-%m-%d'))
    end_date_str = request.GET.get('end_date', (today.replace(day=calendar.monthrange(today.year, today.month)[1])).strftime('%Y-%m-%d'))

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

    total_realizado = Transaction.objects.filter(
        company=company,
        account__account_type__in=['D', 'E'],
        date__range=[start_date, end_date]
    ).aggregate(total=Coalesce(Sum('amount'), Value(Decimal('0.00'))))['total']

    if not total_realizado or total_realizado == 0:
        return JsonResponse({'labels': [], 'data': [], 'total_realizado': 0})

    top_expenses = Transaction.objects.filter(
        company=company,
        account__account_type__in=['D', 'E'],
        date__range=[start_date, end_date]
    ).values('account__name').annotate(total=Sum('amount')).order_by('-total')[:5]

    labels = []
    data = []
    total_top_5 = Decimal(0)

    for item in top_expenses:
        amount = item['total']
        percent = (amount / total_realizado) * 100
        labels.append(item['account__name'])
        data.append(float(round(percent, 2)))
        total_top_5 += amount

    others = total_realizado - total_top_5
    if others > 0:
        percent_others = (others / total_realizado) * 100
        if percent_others > 1:
            labels.append("Outros")
            data.append(float(round(percent_others, 2)))

    return JsonResponse({'labels': labels, 'data': data, 'total_realizado': float(total_realizado)})


@login_required
def revenue_vs_expense_12m_data(request):
    active_company_id = request.session.get('active_company_id')
    company = get_object_or_404(Company, pk=active_company_id, users=request.user)

    labels = []
    revenue_data = []
    expense_data = []

    for i in range(12):
        target_date = datetime.now() - relativedelta(months=i)
        target_year = target_date.year
        target_month = target_date.month
        labels.append(target_date.strftime("%b/%Y"))

        receita_mes = Transaction.objects.filter(
            company=company,
            account__account_type='R',
            date__year=target_year,
            date__month=target_month
        ).aggregate(total=Coalesce(Sum('amount'), Value(Decimal(0))))['total']
        revenue_data.append(float(receita_mes))

        despesa_mes = Transaction.objects.filter(
            company=company,
            account__account_type__in=['D', 'E'],
            date__year=target_year,
            date__month=target_month
        ).aggregate(total=Coalesce(Sum('amount'), Value(Decimal(0))))['total']
        expense_data.append(float(despesa_mes))

    labels.reverse()
    revenue_data.reverse()
    expense_data.reverse()

    return JsonResponse({'labels': labels, 'revenue_data': revenue_data, 'expense_data': expense_data})
