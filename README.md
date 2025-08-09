# Finanças 360

**Finanças 360** é um sistema web de gestão financeira multi-empresa, desenvolvido com o framework Django. O objetivo da plataforma é permitir que prestadores de serviço (como BPOs financeiros ou contadores) gerenciem as finanças de múltiplos clientes de forma centralizada, segura e eficiente, com módulos especializados para diferentes nichos de negócio.

## Status do Projeto

**Status:** `MVP Concluído` | `Novos Módulos em Desenvolvimento`

O núcleo do sistema está completo. A fase atual é de expansão com novos módulos de alto valor agregado.

---

## Funcionalidades Implementadas

Até o momento, o sistema conta com as seguintes funcionalidades prontas e operacionais:

### 1. Módulo Financeiro Principal

- **Dashboard Analítico e Interativo:** Página inicial com cards de resumo, filtros dinâmicos por data e gráficos de distribuição de despesas e comparativo mensal de receitas.
- **Planejamento e Controle (Quadro Orçamentário):** Tabela hierárquica completa de 12 meses, comparando Orçamento Anual vs. Realizado Mensal, com cálculo de variação e alertas visuais de estouro de orçamento.
- **Gestão Completa (CRUD):** Interface completa para o usuário gerenciar Empresas, Plano de Contas e Lançamentos.
- **Importação de Dados:** Funcionalidade para importar Plano de Contas via arquivo CSV e opção de usar um modelo padrão.
- **Relatórios (DRE):** Geração de DRE Gerencial com base na hierarquia das contas e exportação para PDF.

### 2. Módulo de Controle de Plantões

- **Base de Dados Dedicada:** Estrutura completa no banco de dados para gerenciar Especialidades, Turnos, Unidades de Assistência, Orçamentos de Plantão e Lançamentos mensais realizados.
- **Tela de Configurações:** Interface para o usuário cadastrar (CRUD) os dados básicos do módulo (Especialidades, Turnos, Unidades).
- **Tela de Orçamento de Plantões:** Interface completa para o usuário montar o planejamento, definindo a quantidade, tipo e valor para cada combinação de plantão.
- **Tela de Lançamentos Mensais:** Interface estilo "planilha" para o usuário registrar de forma rápida os valores realizados de todos os plantões para um determinado mês.
- **Notificações por E-mail:** Envio automático de e-mail de alerta para o gestor quando um lançamento de plantão ultrapassa o valor orçado.

### 3. Melhorias Gerais e de UX

- **Busca e Filtro Inteligente:** Uso da biblioteca Select2 e JavaScript para criar campos de busca e filtros dinâmicos nos formulários.
- **Formatação de Números:** Todos os valores financeiros são exibidos no padrão brasileiro (`R$ 1.234,56`).
- **Layout Profissional:** Interface consistente e responsiva com Bootstrap 5 e um template base com sidebar de navegação.

---

## Próximos Passos (Roadmap)

### 🎯 Foco Imediato

1. **Quadro Orçamentário de Plantões:**
   - [ ] **Objetivo:** Finalizar a tela de análise do módulo de plantões.
   - [ ] **Implementação:** Criar a `view` e o `template` que exibirá a comparação entre o orçado e o realizado mensal dos plantões, com a mesma inteligência visual do quadro financeiro.

### 🚀 Funcionalidades Futuras

- [ ] **Expansão do Dashboard Principal:** Adicionar novos gráficos (Evolução do Resultado Líquido, Top 5 Despesas, Fontes de Receita).
- [ ] **Deployment:** Planejar e executar o processo de colocar a aplicação online em um servidor de produção.
- [ ] **Testes Automatizados:** Escrever testes para garantir a estabilidade e a qualidade do código a longo prazo.

---

## Tecnologias Utilizadas

- **Backend:** Python, Django
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5, Chart.js, jQuery, Select2
- **Relatórios:** WeasyPrint
- **Banco de Dados (Desenvolvimento):** SQLite

## Instalação e Configuração

### Pré-requisitos

- Python 3.8+
- pip

### Configuração do Ambiente

1. Clone o repositório:
```bash
git clone https://github.com/nuanderson/financas360.git
cd financas360
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:
```env
SECRET_KEY=sua_chave_secreta_aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
EMAIL_HOST_USER=seu_email@example.com
EMAIL_HOST_PASSWORD=sua_senha_de_app
```

5. Execute as migrações:
```bash
python manage.py migrate
```

6. Crie um superusuário:
```bash
python manage.py createsuperuser
```

7. Execute o servidor de desenvolvimento:
```bash
python manage.py runserver
```

O sistema estará disponível em `http://localhost:8000`.

## Estrutura do Projeto

```
financas360/
├── config/          # Configurações do Django
├── core/            # Módulo financeiro principal
├── plantoes/        # Módulo de controle de plantões
├── templates/       # Templates base
├── locale/          # Arquivos de tradução
├── manage.py        # Script de gerenciamento do Django
└── requirements.txt # Dependências do projeto
```

## Contribuição

Este projeto está em desenvolvimento ativo. Para contribuir:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## Licença

Este projeto é licenciado sob a [MIT License](LICENSE).

## Contato

Nuanderson - [GitHub](https://github.com/nuanderson)

Link do Projeto: [https://github.com/nuanderson/financas360](https://github.com/nuanderson/financas360)