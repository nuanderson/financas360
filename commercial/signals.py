from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Sale
from core.models import Transaction
from dateutil.relativedelta import relativedelta

@receiver(post_save, sender=Sale)
def create_installments_signal(sender, instance, created, **kwargs):
    # Verifica se está confirmado e se ainda não gerou transações
    if instance.status == 'CONFIRMED' and not instance.generated_transactions.exists():
        
        print(f"💰 Gerando financeiro para venda {instance.id}...")

        # 1. Lançar a Entrada (Se houver)
        if instance.entry_amount > 0:
            Transaction.objects.create(
                company=instance.company,
                description=f"Entrada - {instance.service.name} ({instance.customer.name})",
                amount=instance.entry_amount,
                
                # --- NOVOS CAMPOS ---
                account=instance.category,          # Plano de contas (Receita)
                bank_account=instance.bank_account, # Onde caiu o dinheiro (Cora/Rede)
                # --------------------
                
                date=instance.sale_date,
                due_date=instance.sale_date,
                status='PAID',
                payment_date=instance.sale_date,
                customer=instance.customer,
                sale_origin=instance
            )

        # 2. Lançar as Parcelas (Restante)
        remaining_amount = instance.total_amount - instance.entry_amount
        if remaining_amount > 0 and instance.installment_count > 0:
            installment_value = remaining_amount / instance.installment_count
            
            for i in range(1, instance.installment_count + 1):
                due_date = instance.sale_date + relativedelta(months=i)
                
                Transaction.objects.create(
                    company=instance.company,
                    description=f"Parcela {i}/{instance.installment_count} - {instance.service.name}",
                    amount=installment_value,
                    
                    # --- NOVOS CAMPOS ---
                    account=instance.category,          # Plano de contas
                    bank_account=instance.bank_account, # Banco
                    # --------------------
                    
                    date=due_date,
                    due_date=due_date,
                    status='PENDING', 
                    payment_date=None,
                    customer=instance.customer,
                    sale_origin=instance
                )