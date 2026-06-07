from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('commercial', '0003_monthlygoal'),
        ('core', '0009_remove_commercial_fks'),
    ]

    operations = [
        migrations.DeleteModel(name='MonthlyGoal'),
        migrations.DeleteModel(name='Sale'),
        migrations.DeleteModel(name='Service'),
        migrations.DeleteModel(name='Supplier'),
        migrations.DeleteModel(name='BankAccount'),
        migrations.DeleteModel(name='Customer'),
    ]
