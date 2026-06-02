# agente-dados-mcp

> MCP server privacy-first para análise exploratória de datasets locais.
> **O código vai pro dado, o dado nunca vai pro LLM.**

Funciona em qualquer cliente MCP-compatível (Claude Code, Claude Desktop,
Cursor, Windsurf, Cline, Zed, Continue.dev).

## O que ele faz

1. Você carrega um dataset local (CSV, Parquet, Excel `.xlsx`/`.xls`, ou JSON).
2. O servidor extrai **apenas o schema** (nomes de colunas, tipos, contagens,
   cardinalidade, PII detectada). Nenhum valor de célula sai da sua máquina.
3. O LLM do seu cliente (Claude, GPT, Gemini — o que estiver configurado)
   conversa com você, propõe análises e gera código pandas + Plotly.
4. O código é parseado por AST e bloqueado se contiver imports/funções
   perigosas (`os`, `eval`, `open`, `__class__`, etc.).
5. Se aprovado, executa local contra o DataFrame.
6. O retorno é multimodal: PNG inline no chat + resumo markdown + link pra
   versão HTML interativa.

## Privacidade por arquitetura

- **Dados nunca saem da sua máquina.** O LLM só vê estrutura.
- **Sem chave de API nossa** — usa o LLM do cliente que você já paga.
- **Sem persistência entre sessões** — fechou o cliente, sumiu o estado.
- **PII é flaggeada e exige autorização explícita** antes de virar agregação.

Ver [`docs/ETHICS.md`](docs/ETHICS.md) para a matriz de risco completa.

## Instalação

Requer Python 3.11+.

```bash
git clone https://github.com/aulaterca/agente-dados-mcp.git
cd agente-dados-mcp
pip install -e .
```

Ou, quando publicado:

```bash
pip install agente-dados-mcp
# ou
uvx agente-dados-mcp
```

## Configurar no cliente MCP

### Claude Code

Edite `~/.claude/mcp.json` (ou `.mcp.json` no projeto):

```json
{
  "mcpServers": {
    "agente-dados": {
      "command": "agente-dados-mcp"
    }
  }
}
```

Reinicie o cliente. As quatro tools (`carregar_dataset`, `autorizar_colunas`,
`executar_analise`, `limpar_sessao`) devem aparecer.

### Outros clientes

Ver [`docs/INSTALL.md`](docs/INSTALL.md) (Cursor, Windsurf, Claude Desktop).

## Uso

```
você: Carregue exemplos/adult.csv e me mostre o schema.

agente: [chama carregar_dataset]
        Carreguei 32.561 linhas, 15 colunas. PII detectada:
          age, race, sex, native-country, income
        Quais você autoriza usar em agregações?

você: Pode usar idade e país, mas não race/sex/income.

agente: [chama autorizar_colunas([...])]
        O que você quer analisar?

você: Distribuição de idade por país (top 10 países).

agente: [gera código pandas + plotly]
        [chama executar_analise]
        [AST valida → executa → retorna PNG + resumo + link HTML]
```

## Desenvolvimento

```bash
pip install -e ".[dev]"
pytest
ruff check src tests
```

## Arquitetura

```
cliente MCP (Claude Code, Cursor, …)
        ↓ stdio
agente-dados-mcp (Python)
  ├─ carregar_dataset   →  CSV/Parquet/Excel/JSON + schema + PII
  ├─ autorizar_colunas  →  consent gate
  ├─ executar_analise   →  AST validator → sandbox exec → PNG + HTML
  └─ limpar_sessao      →  reset
        ↑
   df fica em memória local
```

Ver [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) e
[`docs/PRESENTATION.md`](docs/PRESENTATION.md).

## Licença

MIT.
