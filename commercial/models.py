from django.db import models
from core.models import Company, ChartOfAccounts as Account

# --- CADASTROS BÁSICOS (Mantidos) ---

class Customer(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='customers')
    name = models.CharField("Nome Completo", max_length=255)
    cpf = models.CharField("CPF", max_length=14, blank=True, null=True)
    phone = models.CharField("Telefone/WhatsApp", max_length=20, blank=True, null=True)
    email = models.EmailField("Email", blank=True, null=True)
    birth_date = models.DateField("Data de Nascimento", blank=True, null=True)
    address = models.TextField("Endereço", blank=True, null=True)
    notes = models.TextField("Observações", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# --- NOVO MODEL: CONTA BANCÁRIA (TESOURARIA) ---
class BankAccount(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='bank_accounts')
    name = models.CharField("Nome da Conta", max_length=100, help_text="Ex: Banco Cora, Maquininha Rede, Caixinha")
    initial_balance = models.DecimalField("Saldo Inicial", max_digits=12, decimal_places=2, default=0)
    
    def __str__(self):
        return self.name

class Supplier(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='suppliers')
    trade_name = models.CharField("Nome Fantasia", max_length=255)
    corporate_name = models.CharField("Razão Social", max_length=255, blank=True, null=True)
    tax_id = models.CharField("CNPJ/CPF", max_length=20, blank=True, null=True)
    contact_info = models.CharField("Contato", max_length=255, blank=True, null=True)
    default_account = models.ForeignKey(
        Account, on_delete=models.SET_NULL, null=True, blank=True, 
        verbose_name="Categoria Padrão"
    )
    def __str__(self):
        return self.trade_name

class Service(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='services')
    name = models.CharField("Nome do Procedimento", max_length=255)
    default_price = models.DecimalField("Preço Padrão", max_digits=10, decimal_places=2, default=0)
    description = models.TextField("Descrição", blank=True, null=True)
    def __str__(self):
        return self.name

# --- O MOTOR COMERCIAL (VENDA) ATUALIZADO ---

class Sale(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Orçamento'),
        ('CONFIRMED', 'Fechado/Confirmado'),
        ('CANCELED', 'Cancelado'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('CREDIT_CARD', 'Cartão de Crédito'),
        ('DEBIT_CARD', 'Cartão de Débito'),
        ('PIX', 'Pix'),
        ('BOLETO', 'Boleto'),
        ('MONEY', 'Dinheiro'),
        ('TRANSFER', 'Transferência'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='sales')
    
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, verbose_name="Cliente")
    service = models.ForeignKey(Service, on_delete=models.PROTECT, verbose_name="Serviço")
    
    # 1. Categoria (Vem do Plano de Contas - Ex: Receita de Procedimentos)
    category = models.ForeignKey(
        Account, 
        on_delete=models.PROTECT, 
        verbose_name="Categoria (Plano de Contas)",
        null=True # Deixo null temporariamente para evitar erro na migração
    )

    # 2. Conta Bancária (Vem da nova tabela BankAccount - Ex: Cora, Rede)
    bank_account = models.ForeignKey(
        BankAccount, 
        on_delete=models.PROTECT, 
        verbose_name="Conta de Destino (Banco/Caixa)",
        null=True
    )
    
    sale_date = models.DateField("Data da Venda")
    total_amount = models.DecimalField("Valor Total", max_digits=10, decimal_places=2)
    entry_amount = models.DecimalField("Valor de Entrada", max_digits=10, decimal_places=2, default=0)
    installment_count = models.IntegerField("Nº de Parcelas (Restante)", default=1)
    payment_method = models.CharField("Forma de Pagto", max_length=20, choices=PAYMENT_METHOD_CHOICES, default='CREDIT_CARD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField("Observações", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.name} - {self.service.name}"