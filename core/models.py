from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

# Modelo para guardar as empresas dos clientes
class Company(models.Model):
    MANAGEMENT_CHOICES = (
        ('Pública', 'Gestão Pública (Foco em Orçamento)'),
        ('Particular', 'Gestão Particular (Foco em Lucratividade)'),
    )
    name = models.CharField(_("name"),max_length=100, unique=True, help_text=_("Client company name"))
    # Relação Muitos-para-Muitos.
    # Um usuário pode gerenciar várias empresas.
    # Uma empresa pode ser gerenciada por vários usuários (equipe).
    users = models.ManyToManyField(User, related_name='companies', verbose_name=_("users"),help_text=_("Users who can manage this company"))

    management_type = models.CharField(
        _("tipo de gestão"),
        max_length=15,
        choices=MANAGEMENT_CHOICES,
        default='particular'
    )

    def __str__(self):
        # Retorna o nome da empresa como sua representação em texto
        return self.name
        
    class Meta:
        verbose_name = _("Company") # Nome do modelo no singular
        verbose_name_plural = _("Companies") # Nome do modelo no plural

# Modelo para o plano de contas de cada empresa
class ChartOfAccounts(models.Model):
    ACCOUNT_TYPE_CHOICES = (
        ('R', _('Revenue')), # Receita
        ('D', _('Expense')), # Despesa
    )

    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("company"))
    code = models.CharField(_("code"),max_length=20, help_text=_("Account code, e.g., 1.01.01"))
    name = models.CharField(_("name"),max_length=100, help_text=_("Account name, e.g., Product Sales"))
    account_type = models.CharField(_("account type"),max_length=1, choices=ACCOUNT_TYPE_CHOICES)

    parent_account = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_accounts', verbose_name=_("parent account"))

    def __str__(self):
        return f"[{self.company.name}] {self.code} - {self.name}"

    class Meta:
        verbose_name = _("Chart of Account")
        verbose_name_plural = _("Chart of Accounts")

    def get_level(self):
        level = 0
        p = self.parent_account
        while p:
            level += 1
            p = p.parent_account
        return level

# Modelo para cada transação (entrada ou saída)
class Transaction(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("company"))
    account = models.ForeignKey(ChartOfAccounts, on_delete=models.PROTECT, verbose_name=_("account"))

    date = models.DateField(_("date"))
    amount = models.DecimalField(_("amount"),max_digits=12, decimal_places=2)
    description = models.TextField(_("description"),blank=True, null=True)

    # Campo para saber QUEM fez (opcional: null=True para não quebrar dados antigos)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Criado por")
    # Campo para saber QUANDO foi digitado (automático)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")

    def __str__(self):
        return f"[{self.date}] {self.account.name} - R$ {self.amount}"

    class Meta:
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")


class Budget(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("empresa"))
    # Cada registro de orçamento pertence a uma conta específica
    account = models.ForeignKey(ChartOfAccounts, on_delete=models.CASCADE, verbose_name=_("account"))
    # O ano para o qual este orçamento se aplica
    year = models.PositiveIntegerField(_("year"))
    # O valor total previsto para a conta no ano inteiro
    annual_amount = models.DecimalField(_("annual amount"), max_digits=15, decimal_places=2)

    def __str__(self):
        return f"Orçamento para {self.account.name} em {self.year}"

    class Meta:
        verbose_name = _("Budget")
        verbose_name_plural = _("Budgets")
        # Garante que só exista um orçamento por conta e por ano
        unique_together = ('company', 'account', 'year')    
    

class NoteTag(models.Model):
    name = models.CharField(max_length=30, verbose_name="Nome do Marcador")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='tags')

    class Meta:
        unique_together = ('name', 'company')
        verbose_name = "Marcador de Nota"
        verbose_name_plural = "Marcadores de Notas"

    def __str__(self):
        return self.name

class Note(models.Model):
    COLOR_CHOICES = [
        ('warning', 'Amarelo (Padrão)'),
        ('info', 'Azul (Informativo)'),
        ('success', 'Verde (Ideia/OK)'),
        ('danger', 'Vermelho (Urgente)'),
        ('secondary', 'Cinza (Arquivo)'),
    ]

    title = models.CharField(max_length=100, blank=True, verbose_name="Título")
    content = models.TextField(verbose_name="Conteúdo")
    color = models.CharField(max_length=20, choices=COLOR_CHOICES, default='warning', verbose_name="Cor")

    # Datas
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reminder_date = models.DateField(null=True, blank=True, verbose_name="Lembrar em")

    # Vínculos
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    tag = models.ForeignKey(NoteTag, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Marcador")

    # Flags de Lógica
    is_global = models.BooleanField(default=False, verbose_name="Global (Aparece em todas as empresas)")
    is_public = models.BooleanField(default=False, verbose_name="Pública (Para toda equipe)")

    is_archived = models.BooleanField(default=False, verbose_name="Arquivado")

    def __str__(self):
        return self.title or f"Nota #{self.id}"
