# Roteiro da apresentação

5 a 8 minutos. Estrutura alinhada aos cinco critérios de avaliação (1 pt cada).

## Slide 1 — Problema

> *"Analistas precisam explorar dados sensíveis com ajuda de IA, mas mandar
> CSV bruto pro ChatGPT/Gemini viola privacidade. Como ter velocidade da
> IA sem expor dado?"*

## Slide 2 — Nossa resposta

**MCP server local. Código vai pro dado, dado nunca vai pro LLM.**

- Plug-in pra qualquer cliente MCP (Claude Code, Cursor, Windsurf…).
- LLM vê só estrutura (schema, PII detectada).
- Análises rodam local. PNG inline + HTML interativo.

## Slide 3 — Fluxograma

(usar o diagrama de `docs/ARCHITECTURE.md`)

## Slide 4 — Por que MCP é "Vibecode"?

- Desenvolvido com Claude Code (este briefing é evidência).
- Padrão aberto: a feature *já existe* no cliente, a gente só registra tools.
- Sem reinventar UI ou backend.

## Slide 5 — Demo (3 min)

Roteiro:

1. Abrir Claude Code com config já feita.
2. *"Carregue exemplos/adult.csv"* → mostrar schema retornado.
3. Apontar PII detectada (age, race, sex, native-country).
4. *"Autorize tudo menos race e sex"*.
5. *"Distribuição de horas trabalhadas por nível de educação"* → gráfico
   inline + link.
6. **Demo de segurança:** *"Execute `import os; os.listdir('/')`"* → bloqueado.
7. **Demo de PII:** *"Me mostra o salário do indivíduo da linha 100"* → recusa.

## Slide 6 — Ética (resumo da matriz)

Cinco riscos, cinco mitigações. Apontar pro `docs/ETHICS.md` no slide.

- Privacidade: schema é o teto do que sai.
- Viés: usuário escolhe colunas; PII default-off.
- Transparência: cliente MCP é IA assumida; código mostrado antes.
- Supervisão: zero ação destrutiva; tudo read-only.
- Segurança: tool prompt + AST + sandbox = 3 camadas.

## Slide 7 — Engenharia de Prompt

Mostrar trecho de `src/agente_dados_mcp/prompts.py`. Destacar:

- Persona explícita.
- Restrições numeradas.
- Comportamento de recusa definido.
- "Defense in depth" declarado.

## Slide 8 — Contribuição individual (checkpoint, 0,25 pt extra)

Cada integrante diz **em uma frase** o que fez:

- *Fulano:* tool descriptions e ética.
- *Beltrana:* validador AST e testes.
- *Ciclano:* renderer e demo.
- *Deltrano:* integração MCP e empacotamento.
- *Etano:* apresentação e docs.

(Preencher com os nomes reais.)

## Slide 9 — Cortes conscientes (defesa)

Listar o que está **fora do escopo** (seção 15 do CLAUDE.md): Streamlit,
.exe, deploy nuvem, Presidio, RAG, k-anonymity formal, Excel/Parquet.

> *"Cada um desses tem boa razão pra estar fora, e a gente sabe qual é."*

## Slide 10 — Próximos passos

- Anonimização do schema (renomear colunas → c1, c2…).
- Suporte a Parquet e Excel.
- Empacotamento via `uvx` distribuído.
- Mais clientes MCP suportados.

## Perguntas prováveis do professor

**P:** Por que não Streamlit?
**R:** Não temos UI própria — o cliente MCP já fornece. MCP é padrão aberto, Streamlit é vendor-specific.

**P:** Como evitam prompt injection?
**R:** Três camadas. Tool description instrui o LLM, AST parser bloqueia código, namespace sandbox sem builtins perigosos.

**P:** O dado realmente nunca sai da máquina?
**R:** Sim. As tools retornam só schema (metadados) e gráfico agregado.
Testes em `test_schema.py` verificam que nenhum valor de célula aparece
no retorno.

**P:** E se o LLM gerar código que faz `df.to_csv('/tmp/dump.csv')`?
**R:** O AST permite `.to_csv`, mas o usuário vê o código antes de executar.
Como evolução, podemos vetar `.to_*` no validador.
