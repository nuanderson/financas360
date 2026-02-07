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


class TransporteLancamento(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Empresa"))
    competencia = models.DateField(_("Mês de Referência")) # Dia 1 do mês
    
    quantidade_viagens = models.PositiveIntegerField(_("Qtd. Viagens"))
    valor_viagem = models.DecimalField(_("Valor por Viagem"), max_digits=10, decimal_places=2)
    
    # Campo opcional para descrição (ex: 'Ambulância UTI', 'Transferência Simples')
    descricao = models.CharField(_("Descrição"), max_length=150, blank=True, null=True)

    class Meta:
        verbose_name = _("Lançamento de Transporte")
        verbose_name_plural = _("Lançamentos de Transporte")
        ordering = ['-competencia'] # Mais recentes primeiro
        unique_together = ('company', 'competencia', 'descricao') # Evita duplicidade no mesmo mês/tipo

    def __str__(self):
        return f"Transporte {self.competencia.strftime('%m/%Y')} - {self.quantidade_viagens} viagens"

    @property
    def total(self):
        return self.quantidade_viagens * self.valor_viagem


# MÓDULO: URGÊNCIA E EMERGÊNCIA

class UrgenciaSetor(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Empresa"))
    name = models.CharField(_("Nome do Setor"), max_length=150, help_text="Ex: Eixo Vermelho, Sala Amarela, UTI")

    class Meta:
        verbose_name = _("Setor de Urgência")
        verbose_name_plural = _("Setores de Urgência")
        unique_together = ('company', 'name')

    def __str__(self):
        return self.name


class UrgenciaConfiguracao(models.Model):
    """
    O 'GABARITO'. Define a estrutura padrão de escala para um setor.
    Isso evita que o usuário tenha que digitar valores e quantidades todo mês.
    """
    setor = models.ForeignKey(UrgenciaSetor, on_delete=models.CASCADE, related_name='configuracoes')
    cargo = models.CharField(_("Cargo/Função"), max_length=100, default="Clínico Geral")
    
    # Estrutura DIA
    qtd_dia = models.PositiveIntegerField(_("Qtd. Plantonistas (Dia)"), default=0)
    valor_plantao_dia = models.DecimalField(_("Valor Plantão (Dia)"), max_digits=10, decimal_places=2, default=0)
    
    # Estrutura NOITE
    qtd_noite = models.PositiveIntegerField(_("Qtd. Plantonistas (Noite)"), default=0)
    valor_plantao_noite = models.DecimalField(_("Valor Plantão (Noite)"), max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        verbose_name = _("Configuração de Escala (Urgência)")
        verbose_name_plural = _("Configurações de Escala")

    def __str__(self):
        return f"Config {self.setor.name} - {self.cargo}"


class UrgenciaLancamento(models.Model):
    """
    O REALIZADO. É uma cópia da configuração para um mês específico.
    Aqui os valores ficam 'congelados' para o histórico não mudar se a configuração mudar depois.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    competencia = models.DateField(_("Mês de Referência")) # Dia 1 do mês
    setor_nome = models.CharField(_("Setor"), max_length=150) # Cópia do nome para histórico
    cargo_nome = models.CharField(_("Cargo"), max_length=100) # Cópia do nome para histórico

    # Dados copiados da Configuração (mas editáveis neste mês específico)
    qtd_dia = models.PositiveIntegerField(_("Qtd. Dia"), default=0)
    valor_plantao_dia = models.DecimalField(_("Valor Dia"), max_digits=10, decimal_places=2, default=0)
    
    qtd_noite = models.PositiveIntegerField(_("Qtd. Noite"), default=0)
    valor_plantao_noite = models.DecimalField(_("Valor Noite"), max_digits=10, decimal_places=2, default=0)
    
    dias_mes = models.DecimalField(_("Dias no Mês"), max_digits=5, decimal_places=2, default=30)

    # Valores Variáveis (Digitados mensalmente conforme sua planilha Excel)
    valor_pega_plantao = models.DecimalField(_("Valor Pega Plantão"), max_digits=12, decimal_places=2, default=0)
    valor_efetivo = models.DecimalField(_("Valor Efetivo"), max_digits=12, decimal_places=2, default=0)
    observacoes = models.TextField(_("Obs"), blank=True, null=True)

    class Meta:
        verbose_name = _("Lançamento Urgência")
        verbose_name_plural = _("Lançamentos Urgência")
        ordering = ['setor_nome', 'cargo_nome']

    @property
    def total_escala_calculada(self):
        """
        Reproduz a fórmula da planilha:
        (Qtd Dia * Valor Dia * Dias) + (Qtd Noite * Valor Noite * Dias)
        """
        custo_dia = self.qtd_dia * self.valor_plantao_dia * self.dias_mes
        custo_noite = self.qtd_noite * self.valor_plantao_noite * self.dias_mes
        return custo_dia + custo_noite


    @property
    def custo_real_soma(self):
        """
        Soma pura do que foi digitado nos inputs.
        """
        return self.valor_pega_plantao + self.valor_efetivo

    @property
    def total_realizado(self):
        """
        Mantemos essa lógica para exibição visual do 'Custo Final':
        Se não digitou nada (0), assume-se que o custo será igual ao orçado (Previsão).
        Se digitou algo, assume-se a soma real.
        """
        soma = self.custo_real_soma
        if soma == 0:
            return self.total_escala_calculada
        return soma

    @property
    def saldo_orcamentario(self):
        """
        A LÓGICA DE CONTROLADORIA:
        Orçado (Teto) - Realizado (Execução).
        
        Se inputs forem zero: Consideramos que o Saldo é 0 (está na meta),
        para não gerar uma 'falsa economia' antes de preencher.
        """
        if self.custo_real_soma == 0:
            return 0
            
        # Ex: Orçado 100 - Real 120 = -20 (Prejuízo/Vermelho)
        return self.total_escala_calculada - self.custo_real_soma

# ==========================================
# MÓDULO: CIRURGIA GERAL
# ==========================================

class CirurgiaSetor(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Empresa"))
    name = models.CharField(_("Nome do Setor"), max_length=150, help_text="Ex: Cirurgia Geral Eletiva, Ortopedia Cirúrgica")

    class Meta:
        verbose_name = _("Setor de Cirurgia")
        verbose_name_plural = _("Setores de Cirurgia")
        unique_together = ('company', 'name')

    def __str__(self):
        return self.name


class CirurgiaConfiguracao(models.Model):
    """
    O 'GABARITO' da Cirurgia.
    """
    setor = models.ForeignKey(CirurgiaSetor, on_delete=models.CASCADE, related_name='configuracoes')
    cargo = models.CharField(_("Cargo/Função"), max_length=100, default="Cirurgião")
    
    # Estrutura DIA
    qtd_dia = models.PositiveIntegerField(_("Qtd. Plantonistas (Dia)"), default=0)
    valor_plantao_dia = models.DecimalField(_("Valor Plantão (Dia)"), max_digits=10, decimal_places=2, default=0)
    
    # Estrutura NOITE
    qtd_noite = models.PositiveIntegerField(_("Qtd. Plantonistas (Noite)"), default=0)
    valor_plantao_noite = models.DecimalField(_("Valor Plantão (Noite)"), max_digits=10, decimal_places=2, default=0)
    
    # OBS: O campo dias_base_mensal foi removido aqui também, seguindo a melhoria que fizemos.

    class Meta:
        verbose_name = _("Configuração de Escala (Cirurgia)")
        verbose_name_plural = _("Configurações de Escala (Cirurgia)")

    def __str__(self):
        return f"Config {self.setor.name} - {self.cargo}"


class CirurgiaLancamento(models.Model):
    """
    A FOLHA MENSAL da Cirurgia.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    competencia = models.DateField(_("Mês de Referência"))
    setor_nome = models.CharField(_("Setor"), max_length=150)
    cargo_nome = models.CharField(_("Cargo"), max_length=100)

    # Dados copiados da Configuração (Valores de Referência)
    qtd_dia = models.PositiveIntegerField(_("Qtd. Dia"), default=0)
    valor_plantao_dia = models.DecimalField(_("Valor Dia"), max_digits=10, decimal_places=2, default=0)
    
    qtd_noite = models.PositiveIntegerField(_("Qtd. Noite"), default=0)
    valor_plantao_noite = models.DecimalField(_("Valor Noite"), max_digits=10, decimal_places=2, default=0)
    
    dias_mes = models.DecimalField(_("Dias no Mês"), max_digits=5, decimal_places=2, default=30)

    # Valores Variáveis (Controladoria)
    valor_pega_plantao = models.DecimalField(_("Valor Pega Plantão"), max_digits=12, decimal_places=2, default=0)
    valor_efetivo = models.DecimalField(_("Valor Efetivo"), max_digits=12, decimal_places=2, default=0)
    observacoes = models.TextField(_("Obs"), blank=True, null=True)

    class Meta:
        verbose_name = _("Lançamento Cirurgia")
        verbose_name_plural = _("Lançamentos Cirurgia")
        ordering = ['setor_nome', 'cargo_nome']

    @property
    def total_escala_calculada(self):
        """META (Orçamento)"""
        custo_dia = self.qtd_dia * self.valor_plantao_dia * self.dias_mes
        custo_noite = self.qtd_noite * self.valor_plantao_noite * self.dias_mes
        return custo_dia + custo_noite

    @property
    def custo_real_soma(self):
        """Soma pura dos inputs"""
        return self.valor_pega_plantao + self.valor_efetivo

    @property
    def total_realizado(self):
        """
        Visualização Inteligente:
        Se inputs == 0, mostra a Meta.
        Se inputs > 0, mostra a Realidade.
        """
        soma = self.custo_real_soma
        if soma == 0:
            return self.total_escala_calculada
        return soma

    @property
    def saldo_orcamentario(self):
        """
        CONTROLADORIA: Meta - Realizado
        """
        if self.custo_real_soma == 0:
            return 0
        return self.total_escala_calculada - self.custo_real_soma

# ==========================================
# MÓDULO: NEFROLOGIA (PRODUÇÃO)
# ==========================================

class NefrologiaConfiguracao(models.Model):
    """
    TABELA DE PREÇOS E METAS (Gabarito)
    Ex: Hemodiálise S/CDL | R$ 600,00 | Meta: 105
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Empresa"))
    nome_procedimento = models.CharField(_("Nome do Procedimento"), max_length=150, help_text="Ex: Hemodiálise S/CDL")
    
    valor_unitario = models.DecimalField(_("Valor Unitário"), max_digits=10, decimal_places=2, default=0)
    meta_mensal_qtd = models.IntegerField(_("Meta/Média Mensal (Qtd)"), default=0, help_text="Quantidade estimada para previsão orçamentária")

    class Meta:
        verbose_name = _("Configuração Nefrologia")
        verbose_name_plural = _("Configurações Nefrologia")

    def __str__(self):
        return f"{self.nome_procedimento} - R$ {self.valor_unitario}"

    @property
    def total_meta_financeira(self):
        return self.valor_unitario * self.meta_mensal_qtd


class NefrologiaLancamento(models.Model):
    """
    PRODUÇÃO MENSAL
    O usuário preenche apenas a 'qtd_realizada'.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    competencia = models.DateField(_("Mês de Referência"))
    
    # Dados copiados da Configuração (Snapshot)
    nome_procedimento = models.CharField(_("Procedimento"), max_length=150)
    valor_unitario = models.DecimalField(_("Valor Unitário"), max_digits=10, decimal_places=2, default=0)
    meta_qtd = models.IntegerField(_("Meta (Qtd)"), default=0)

    # O Campo Editável
    qtd_realizada = models.IntegerField(_("Qtd. Realizada"), default=0)
    observacoes = models.TextField(_("Obs"), blank=True, null=True)

    class Meta:
        verbose_name = _("Lançamento Nefrologia")
        verbose_name_plural = _("Lançamentos Nefrologia")
        ordering = ['nome_procedimento']

    @property
    def total_orcado(self):
        """Valor da Meta (Previsão)"""
        return self.valor_unitario * self.meta_qtd

    @property
    def total_realizado(self):
        """Valor Final (O que vai pagar)"""
        return self.valor_unitario * self.qtd_realizada

    @property
    def saldo_orcamentario(self):
        """
        CONTROLADORIA:
        Se realizou MENOS que a meta, sobrou dinheiro (Positivo).
        Se realizou MAIS que a meta, gastou mais (Negativo).
        """
        if self.qtd_realizada == 0:
            return 0 # Não calcula saldo se ainda não preencheu
        return self.total_orcado - self.total_realizado

# ==========================================
# MÓDULO: BUCOMAXILO (CONTRATOS FIXOS)
# ==========================================

class BucomaxiloConfiguracao(models.Model):
    """
    CONTRATOS FIXOS (Gabarito)
    Ex: Dr. Diógenes | Sobreaviso | R$ 8.000,00
    Ex: Clare Odonto | Serviço PJ  | R$ 6.243,32
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Empresa"))
    nome_profissional = models.CharField(_("Profissional / Empresa"), max_length=150)
    descricao_servico = models.CharField(_("Descrição do Serviço"), max_length=150, default="Sobreaviso 24h", help_text="Ex: Sobreaviso, Plantão Fixo, Aluguel Equipamento")
    
    valor_mensal = models.DecimalField(_("Valor Mensal Fixo"), max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = _("Configuração Bucomaxilo")
        verbose_name_plural = _("Configurações Bucomaxilo")

    def __str__(self):
        return f"{self.nome_profissional} - R$ {self.valor_mensal}"


class BucomaxiloLancamento(models.Model):
    """
    FOLHA MENSAL BUCOMAXILO
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    competencia = models.DateField(_("Mês de Referência"))
    
    # Snapshot do Contrato
    nome_profissional = models.CharField(_("Profissional"), max_length=150)
    descricao_servico = models.CharField(_("Descrição"), max_length=150)
    valor_contrato = models.DecimalField(_("Valor Contrato"), max_digits=10, decimal_places=2, default=0)

    # Variáveis do Mês (Para cálculo Pro-rata)
    dias_no_mes = models.IntegerField(_("Dias no Mês"), default=30)
    dias_trabalhados = models.IntegerField(_("Dias Trabalhados"), default=30)
    
    # Valor Final (Pode ser calculado ou sobrescrito)
    valor_pagar = models.DecimalField(_("Valor a Pagar"), max_digits=10, decimal_places=2, default=0)
    observacoes = models.TextField(_("Obs"), blank=True, null=True)

    class Meta:
        verbose_name = _("Lançamento Bucomaxilo")
        verbose_name_plural = _("Lançamentos Bucomaxilo")
        ordering = ['nome_profissional']

    @property
    def saldo_orcamentario(self):
        """
        CONTROLADORIA:
        Contrato (Meta) - Valor a Pagar (Real).
        Se pagar menos que o contrato (falta), fica positivo (Economia).
        Se pagar mais (extra), fica negativo.
        """
        if self.valor_pagar == 0:
            return 0
        return self.valor_contrato - self.valor_pagar

# ==========================================
# MÓDULO: RESIDÊNCIA DE CIRURGIA (AULAS)
# ==========================================

class ResidenciaConfiguracao(models.Model):
    """
    CADASTRO DE MÉDICOS/PRECEPTORES
    Ex: Dr. Angelo | R$ 250,00 | Meta: 4 aulas/mês
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Empresa"))
    nome_medico = models.CharField(_("Nome do Médico"), max_length=150)
    
    valor_aula = models.DecimalField(_("Valor por Aula"), max_digits=10, decimal_places=2, default=250.00)
    meta_aulas = models.IntegerField(_("Meta de Aulas (Mensal)"), default=0, help_text="Quantidade esperada para previsão orçamentária")

    class Meta:
        verbose_name = _("Configuração Residência")
        verbose_name_plural = _("Configurações Residência")

    def __str__(self):
        return f"{self.nome_medico} - R$ {self.valor_aula}"

    @property
    def total_meta_financeira(self):
        return self.valor_aula * self.meta_aulas


class ResidenciaLancamento(models.Model):
    """
    FOLHA MENSAL (AULAS DADAS)
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    competencia = models.DateField(_("Mês de Referência"))
    
    # Snapshot (Cópia da Config)
    nome_medico = models.CharField(_("Médico"), max_length=150)
    valor_aula = models.DecimalField(_("Valor Aula"), max_digits=10, decimal_places=2, default=0)
    meta_aulas = models.IntegerField(_("Meta Aulas"), default=0)

    # O Campo Editável (Produção)
    qtd_aulas = models.IntegerField(_("Qtd. Aulas Realizadas"), default=0)
    observacoes = models.TextField(_("Obs"), blank=True, null=True)

    class Meta:
        verbose_name = _("Lançamento Residência")
        verbose_name_plural = _("Lançamentos Residência")
        ordering = ['nome_medico']

    @property
    def total_orcado(self):
        """Valor da Meta (Previsão)"""
        return self.valor_aula * self.meta_aulas

    @property
    def total_realizado(self):
        """Valor Final (O que vai pagar)"""
        return self.valor_aula * self.qtd_aulas

    @property
    def saldo_orcamentario(self):
        """
        CONTROLADORIA:
        Meta - Realizado.
        """
        if self.qtd_aulas == 0:
            return 0 
        return self.total_orcado - self.total_realizado

# ==========================================
# MÓDULO: COORDENAÇÕES (FIXO MENSAL)
# ==========================================

class CoordenacaoConfiguracao(models.Model):
    """
    CADASTRO DE COORDENADORES (Gabarito)
    Campos baseados na imagem: Funcionário, Matrícula, Conselho, Setor, Valor.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Empresa"))
    nome_funcionario = models.CharField(_("Nome do Funcionário"), max_length=150)
    matricula = models.CharField(_("Matrícula / Função"), max_length=100, blank=True, null=True, help_text="Ex: Diretor, Vascular, etc.")
    conselho = models.CharField(_("Conselho"), max_length=50, blank=True, null=True, help_text="Ex: CRM, COREN")
    setor = models.CharField(_("Setor"), max_length=100, blank=True, null=True)
    
    valor_mensal = models.DecimalField(_("Valor Mensal"), max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = _("Configuração Coordenação")
        verbose_name_plural = _("Configurações Coordenação")

    def __str__(self):
        return f"{self.nome_funcionario} - {self.setor}"


class CoordenacaoLancamento(models.Model):
    """
    FOLHA MENSAL COORDENAÇÃO
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    competencia = models.DateField(_("Mês de Referência"))
    
    # Snapshot (Cópia da Config)
    nome_funcionario = models.CharField(_("Funcionário"), max_length=150)
    matricula = models.CharField(_("Matrícula"), max_length=100, blank=True, null=True)
    conselho = models.CharField(_("Conselho"), max_length=50, blank=True, null=True)
    setor = models.CharField(_("Setor"), max_length=100, blank=True, null=True)
    
    # Valores
    valor_contrato = models.DecimalField(_("Valor Contrato (Fixo)"), max_digits=10, decimal_places=2, default=0)
    valor_pagar = models.DecimalField(_("Valor a Pagar (Real)"), max_digits=10, decimal_places=2, default=0)
    
    observacoes = models.TextField(_("Obs"), blank=True, null=True)

    class Meta:
        verbose_name = _("Lançamento Coordenação")
        verbose_name_plural = _("Lançamentos Coordenação")
        ordering = ['nome_funcionario']

    @property
    def saldo_orcamentario(self):
        """
        Meta (Contrato) - Real (Pago)
        Positivo = Economia (Pagou menos)
        Negativo = Extra (Pagou a mais)
        """
        if self.valor_pagar == 0:
            return 0
        return self.valor_contrato - self.valor_pagar