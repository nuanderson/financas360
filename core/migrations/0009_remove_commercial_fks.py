from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_transaction_bank_account'),
        ('commercial', '0003_monthlygoal'),
    ]

    operations = [
        migrations.RemoveField(model_name='transaction', name='customer'),
        migrations.RemoveField(model_name='transaction', name='supplier'),
        migrations.RemoveField(model_name='transaction', name='sale_origin'),
        migrations.RemoveField(model_name='transaction', name='bank_account'),
    ]
