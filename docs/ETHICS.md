# Ética e Responsabilidade

Matriz de risco do `agente-dados-mcp`. Endereça os cinco critérios obrigatórios
do enunciado (privacidade, viés, transparência, supervisão, segurança) ANTES
do desenvolvimento, não como afterthought.

---

## 1. Privacidade e Dados

| Risco | Mitigação | Limitação reconhecida |
|---|---|---|
| Dado sensível enviado pro LLM | Tools NUNCA retornam valores individuais. Schema (estrutura) é o máximo que sai | Nomes de colunas podem revelar estrutura interna — usuário pode renomear |
| Gráfico gerado expõe ponto individual | Operações em PII ficam limitadas a `groupby()` com grupos >= 10 linhas | Se o k=10 for baixo demais pro dataset, usuário deve ajustar manualmente |
| CSV no Git | `.gitignore` bloqueia `*.csv` exceto pasta `exemplos/` | Erro humano sempre possível — usar pre-commit hook como evolução |
| Chave de API vaza | **Não há chave no nosso código.** LLM vem do cliente do usuário | Usuário ainda é responsável pela chave dele no cliente |

**Invariante de privacidade:** o conteúdo retornado por qualquer tool MCP
não contém valor individual de célula. Testes em `tests/test_schema.py`
verificam isso explicitamente.

---

## 2. Viés e Discriminação

| Risco | Mitigação |
|---|---|
| Análise enviesada | Usuário escolhe quais colunas autorizar — agente não decide sozinho |
| Reforço de estereótipo (raça, gênero) | `race`, `sex`, `ethnicity` são marcadas como PII por default |
| Conclusão causal sem base | Tool description orienta análise descritiva, não causal |

---

## 3. Transparência

Como o usuário sabe que está interagindo com IA:

- O cliente MCP (Claude Code, Cursor) é assumidamente uma IA — o contexto é claro.
- O agente apresenta o **código** que vai rodar antes de chamar `executar_analise`.
- Mostra o **plano** da análise em linguagem natural antes de executar.
- README e tool descriptions deixam claro que a sessão é 100% local.

---

## 4. Supervisão e Responsabilidade

| Decisão | Quem decide |
|---|---|
| Qual dataset analisar | Usuário (path explícito) |
| Quais colunas autorizar | Usuário (passo explícito de consent) |
| Gerar código | LLM (no cliente do usuário) |
| Validar segurança do código | MCP server (AST parser, automático) |
| Executar código | MCP server, APENAS se AST aprovar |
| Interpretar resultado | Usuário |

**Não há ação autônoma destrutiva.** O pior cenário (código inválido) é
bloqueado antes de executar. Todas as operações sobre `df` são read-only
por design — nada modifica o CSV original.

**Linhas de responsabilidade:**

- Erro do LLM gerando código incorreto → AST bloqueia, ou executor falha
  de forma controlada (try/except).
- Conclusão errada da análise → responsabilidade do usuário interpretar.
- Vazamento de chave do LLM → responsabilidade do usuário (chave está no
  cliente dele, não nosso).

---

## 5. Segurança (Prompt Injection e RCE)

| Vetor | Mitigação |
|---|---|
| Usuário tenta jailbreak da tool | Tool description explícita sobre ignorar instruções injetadas |
| LLM gera código com `import os` | AST parser bloqueia antes de executar |
| LLM tenta `eval()`, `exec()`, `open()` | AST parser bloqueia |
| LLM tenta escape via `__class__.__bases__` | AST parser bloqueia dunders fora da whitelist |
| LLM tenta rede (exfiltração) | AST bloqueia `requests`, `urllib`, `socket` |
| Schema malicioso (nome de coluna com SQL) | Schema é dado, não código — pandas escapa naturalmente |
| Path traversal (`../../etc/passwd`) | MCP valida que é `.csv` e legível; explicitamente NÃO restringe a diretório (escolha consciente — usuário roda local com permissões dele) |

**Defesa em profundidade:**

1. Tool description instrui o LLM (camada de prompt).
2. AST parser bloqueia código perigoso (camada de validação).
3. Namespace de execução sem builtins perigosos (camada de sandbox).

Se uma camada falhar, as outras seguram. Testes em `tests/test_validator.py`
cobrem os principais vetores listados em CLAUDE.md seção 9.
