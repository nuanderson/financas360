from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import Company


class Especialidade(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("empresa"))
    name = models.CharField(_("nome"), max_length=100)

    class Meta:
        verbose_name = _("Especialidade")
        verbose_name_plural = _("Especialidades")
        unique_together = ('company', 'name')  # Evita nomes duplicados para a mesma empresa

    def __str__(self):
        return self.name


class Turno(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("empresa"))
    name = models.CharField(_("nome"), max_length=50)  # Ex: Dia, Noite

    class Meta:
        verbose_name = _("Turno")
        verbose_name_plural = _("Turnos")
        unique_together = ('company', 'name')

    def __str__(self):
        return self.name


class UnidadeAssistencia(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("empresa"))
    name = models.CharField(_("nome da unidade"), max_length=150)

    class Meta:
        verbose_name = _("Unidade de Assistência")
        verbose_name_plural = _("Unidades de Assistência")
        unique_together = ('company', 'name')

    def __str__(self):
        return self.name


class OrcamentoMensalPlantao(models.Model):
    unidade_assistencia = models.ForeignKey(UnidadeAssistencia, on_delete=models.CASCADE, verbose_name=_("unidade de assistência"))
    date = models.DateField(_("Mês e Ano do Orçamento"))
    valor_orcado = models.DecimalField(_("valor orçado"), max_digits=15, decimal_places=2)

    class Meta:
        verbose_name = _("Orçamento Mensal de Plantão")
        verbose_name_plural = _("Orçamentos Mensais de Plantão")
        # Garante que só haja um valor de orçamento por unidade de assistência e por mês/ano
        unique_together = ('unidade_assistencia', 'date')

    def __str__(self):
        return f"Orçamento de {self.date.strftime('%B/%Y')} para {self.unidade_assistencia.name}"


class LancamentoPlantao(models.Model):
    TIPO_PLANTAO_CHOICES = ((12, '12 horas'),(24, '24 horas'))

    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("empresa"))
    especialidade = models.ForeignKey(Especialidade, on_delete=models.PROTECT, verbose_name=_("especialidade"))
    turno = models.ForeignKey(Turno, on_delete=models.PROTECT, verbose_name=_("turno"))
    unidade_assistencia = models.ForeignKey(UnidadeAssistencia, on_delete=models.PROTECT, verbose_name=_("unidade de assistência"))

    date = models.DateField(_("data do plantão"))
    quantidade = models.PositiveIntegerField(_("quantidade de plantonistas"))
    tipo_plantao = models.PositiveIntegerField(_("tipo de plantão"), choices=TIPO_PLANTAO_CHOICES)
    valor_unitario = models.DecimalField(_("valor unitário do plantão"), max_digits=10, decimal_places=2)
    observacoes = models.TextField(_("observações"), blank=True, null=True)

    class Meta:
        verbose_name = _("Lançamento de Plantão")
        verbose_name_plural = _("Lançamentos de Plantão")

    def __str__(self):
        return f"Plantão de {self.especialidade} em {self.date.strftime('%d/%m/%Y')}"

    @property
    def get_total_value(self):
        """ Calcula o valor total do lançamento (quantidade * valor unitário). """
        return self.quantidade * self.valor_unitario