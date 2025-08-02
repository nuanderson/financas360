from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import Company # Importamos o modelo Company do nosso app principal

class Especialidade(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("empresa"))
    name = models.CharField(_("nome"), max_length=100)

    class Meta:
        verbose_name = _("Especialidade")
        verbose_name_plural = _("Especialidades")
        unique_together = ('company', 'name') # Evita nomes duplicados para a mesma empresa

    def __str__(self):
        return self.name

class Turno(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("empresa"))
    name = models.CharField(_("nome"), max_length=50) # Ex: Dia, Noite

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

class OrcamentoPlantao(models.Model):
    TIPO_PLANTAO_CHOICES = (
        (12, '12 horas'),
        (24, '24 horas'),
    )
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("empresa"))
    especialidade = models.ForeignKey(Especialidade, on_delete=models.PROTECT, verbose_name=_("especialidade"))
    turno = models.ForeignKey(Turno, on_delete=models.PROTECT, verbose_name=_("turno"))
    unidade_assistencia = models.ForeignKey(UnidadeAssistencia, on_delete=models.PROTECT, verbose_name=_("unidade de assistência"))
    quantidade = models.PositiveIntegerField(_("quantidade de plantonistas"))
    tipo_plantao = models.PositiveIntegerField(_("tipo de plantão"), choices=TIPO_PLANTAO_CHOICES)
    valor_plantao = models.DecimalField(_("valor do plantão"), max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = _("Orçamento de Plantão")
        verbose_name_plural = _("Orçamentos de Plantão")

    def __str__(self):
        return f"{self.especialidade} em {self.unidade_assistencia} ({self.turno})"

class LancamentoPlantao(models.Model):
    orcamento = models.ForeignKey(OrcamentoPlantao, on_delete=models.CASCADE, related_name="lancamentos", verbose_name=_("orçamento de plantão"))
    date = models.DateField(_("data do lançamento"))
    valor_realizado = models.DecimalField(_("valor realizado"), max_digits=10, decimal_places=2)
    observacoes = models.TextField(_("observações"), blank=True, null=True)

    class Meta:
        verbose_name = _("Lançamento de Plantão")
        verbose_name_plural = _("Lançamentos de Plantão")

    def __str__(self):
        return f"Lançamento para {self.orcamento} em {self.date.strftime('%m/%Y')}"