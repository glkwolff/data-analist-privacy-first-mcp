# Arquitetura

## Visão geral

```
┌─────────────────────────────────────────────────────────────────┐
│  Máquina do usuário                                             │
│                                                                 │
│  ┌──────────────┐   stdio     ┌──────────────────────────────┐  │
│  │ Cliente MCP  │ ◄─────────► │  agente-dados-mcp (Python)   │  │
│  │ (Claude Code,│             │                              │  │
│  │  Cursor, …)  │             │  ┌────────────────────────┐  │  │
│  │              │             │  │ FastMCP tools          │  │  │
│  │ ┌──────────┐ │             │  │ - carregar_dataset     │  │  │
│  │ │   LLM    │ │             │  │ - autorizar_colunas    │  │  │
│  │ │ (Claude, │ │             │  │ - executar_analise     │  │  │
│  │ │  GPT, …) │ │             │  │ - limpar_sessao        │  │  │
│  │ └──────────┘ │             │  └────────────────────────┘  │  │
│  └──────────────┘             │                              │  │
│        ▲                      │  ┌────────────────────────┐  │  │
│        │ schema, PNG,         │  │ validator (AST)        │  │  │
│        │ markdown,            │  │ executor (sandbox)     │  │  │
│        │ link HTML            │  │ renderer (PNG + HTML)  │  │  │
│        │                      │  │ pii / schema / state   │  │  │
│        ▼                      │  └────────────────────────┘  │  │
│  ┌──────────────┐             │           │                  │  │
│  │   Usuário    │             │           ▼                  │  │
│  │              │             │     pandas DataFrame         │  │
│  └──────────────┘             │     em memória do processo   │  │
│                               └──────────────────────────────┘  │
│        │                                  ▲                     │
│        │ "analise vendas.csv"             │ lê 1x               │
│        ▼                                  │                     │
│  ┌──────────────────────────────────────────────────────┐       │
│  │  arquivo CSV local (nunca sai dessa máquina)         │       │
│  └──────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

**Tudo nesse diagrama roda na máquina do usuário.** Não há serviço remoto
nosso. O LLM mora dentro do cliente MCP (que o usuário já configurou e paga).

## Fluxo de uma análise

```
1. usuário: "carregue vendas.csv"
       │
       ▼
2. LLM no cliente decide chamar carregar_dataset(caminho="vendas.csv")
       │
       ▼ stdio JSON-RPC
3. MCP server:
   - lê CSV via pandas
   - extrai schema (sem valores)
   - detecta PII (2 camadas)
   - salva df em SESSION.df (memória)
       │
       ▼ schema dict
4. LLM recebe schema, apresenta ao usuário, pergunta autorizações
       │
       ▼
5. usuário confirma → LLM chama autorizar_colunas([...])
       │
       ▼
6. usuário pede análise → LLM gera código pandas + plotly
       │
       ▼
7. LLM chama executar_analise(codigo, descricao)
       │
       ▼
8. MCP server:
   a) validar_codigo()    → AST parser  → bloqueia ou aprova
   b) executar()          → namespace controlado → fig
   c) renderer            → PNG base64 + HTML self-contained
       │
       ▼
9. retorna [ImageContent, TextContent resumo, TextContent link]
       │
       ▼
10. cliente renderiza PNG inline + markdown + link clicável
```

## Por que MCP e não Streamlit / FastAPI / .exe

- **Sem UI própria.** O cliente MCP já é uma boa UI conversacional. Não
  reinventamos.
- **Padrão aberto.** Funciona em qualquer cliente compatível, sem lock-in.
- **Distribuição limpa.** `pip install` / `uvx` / `pyproject.toml` —
  ferramentas conhecidas, sem instalador custom.
- **Sem servidor nosso na nuvem.** Tudo local. Privacidade by architecture.
- **Sem chave de API nossa.** O LLM vem do cliente do usuário.

## Decisões não-negociáveis

Ver CLAUDE.md seção 2. As principais:

| Decisão | Escolha | Por quê |
|---|---|---|
| Tipo | MCP server | Padrão aberto, múltiplos clientes |
| Linguagem | Python 3.11+ | SDK MCP + pandas + plotly |
| LLM | O do cliente | Sem chave nossa, sem custo nosso |
| Validação | AST parser | Mais robusto que regex |
| Sandbox | namespace + safe builtins | Defesa em profundidade |
| Visualização | Plotly PNG + HTML | Multimodal: inline + interativo |

## Estrutura dos módulos

```
src/agente_dados_mcp/
├── server.py      ← entry point + registro das tools
├── prompts.py     ← tool descriptions (= system prompt do LLM)
├── state.py       ← SessionState (df + autorizações em memória)
├── schema.py      ← extrai estrutura do df (privacy invariant)
├── pii.py         ← detecção de PII (nome + regex)
├── validator.py   ← AST parser que bloqueia código perigoso
├── executor.py    ← exec() em namespace controlado
└── renderer.py    ← fig → PNG base64 + HTML + resumo markdown
```

Cada módulo é independente e tem teste. Acoplamento mínimo:

- `server` depende de todos.
- `schema` depende de `pii`.
- O resto não depende de ninguém (puro).
