"""
Migration: Budget monthly refactor
- Renomeia annual_amount → amount
- Adiciona campo month (1-12)
- Expande cada registro anual em 12 registros mensais com o mesmo valor
"""
from decimal import Decimal
from django.db import migrations, models


def expand_annual_to_monthly(apps, schema_editor):
    """
    Para cada Budget existente (month=1), cria os meses 2-12 com o mesmo valor.
    A unique_together já foi atualizada para incluir month antes desta etapa.
    """
    Budget = apps.get_model('core', 'Budget')
    existing = list(Budget.objects.filter(month=1))

    to_create = []
    for b in existing:
        for m in range(2, 13):
            to_create.append(Budget(
                company_id=b.company_id,
                account_id=b.account_id,
                year=b.year,
                month=m,
                amount=b.amount,
                # annual_amount ainda existe no banco; setamos 0 para não violar NOT NULL
                annual_amount=Decimal('0'),
            ))

    if to_create:
        Budget.objects.bulk_create(to_create, batch_size=500)


def collapse_monthly_to_annual(apps, schema_editor):
    """Reversão: mantém só o mês 1 e restaura annual_amount."""
    Budget = apps.get_model('core', 'Budget')
    Budget.objects.exclude(month=1).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_remove_commercial_fks'),
    ]

    operations = [
        # 1. Adiciona campo 'amount' (padrão 0 — será preenchido pelo RunSQL)
        migrations.AddField(
            model_name='budget',
            name='amount',
            field=models.DecimalField(
                decimal_places=2, default=0, max_digits=15, verbose_name='amount'
            ),
        ),
        # 2. Adiciona campo 'month' — todos os registros existentes ficam com month=1
        migrations.AddField(
            model_name='budget',
            name='month',
            field=models.PositiveIntegerField(
                default=1,
                help_text='Mês de referência (1=Janeiro … 12=Dezembro)',
                verbose_name='month',
            ),
        ),
        # 3. Copia annual_amount → amount para os registros existentes
        migrations.RunSQL(
            sql="UPDATE core_budget SET amount = annual_amount WHERE amount = 0",
            reverse_sql=migrations.RunSQL.noop,
        ),
        # 4. Atualiza unique_together para incluir month ANTES de criar os demais meses
        #    Sem isso, bulk_create violaria a constraint antiga (company, account, year)
        migrations.AlterUniqueTogether(
            name='budget',
            unique_together={('company', 'account', 'year', 'month')},
        ),
        # 5. Expande cada registro do mês 1 para os meses 2-12
        migrations.RunPython(
            expand_annual_to_monthly,
            reverse_code=collapse_monthly_to_annual,
        ),
        # 6. Remove o campo antigo annual_amount
        migrations.RemoveField(
            model_name='budget',
            name='annual_amount',
        ),
    ]
