from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def create_profiles_for_existing_users(apps, schema_editor):
    """
    Migração de dados: cria UserProfile para todos os usuários existentes.
    Regra:
      is_superuser=True  → admin
      is_staff=True      → gestor
      demais             → gestor  (default seguro)
    """
    User        = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('core', 'UserProfile')

    for user in User.objects.all():
        role = 'admin' if user.is_superuser else 'gestor'
        UserProfile.objects.get_or_create(
            user=user,
            defaults={'role': role},
        )


def reverse_profiles(apps, schema_editor):
    UserProfile = apps.get_model('core', 'UserProfile')
    UserProfile.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_budget_monthly_refactor'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('role', models.CharField(
                    choices=[
                        ('admin',             'Administrador'),
                        ('gestor',            'Gestor'),
                        ('analista_receitas', 'Analista de Receitas'),
                        ('analista_despesas', 'Analista de Despesas'),
                        ('analista_plantoes', 'Analista de Plantões'),
                    ],
                    default='gestor',
                    max_length=30,
                    verbose_name='Papel',
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='profile',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Perfil de Usuário',
                'verbose_name_plural': 'Perfis de Usuários',
            },
        ),
        migrations.RunPython(
            create_profiles_for_existing_users,
            reverse_profiles,
        ),
    ]
