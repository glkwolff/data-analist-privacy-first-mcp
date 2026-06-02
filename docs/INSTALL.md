# Instalação em clientes MCP

## Pré-requisitos

- Python 3.11+ no PATH
- Acesso ao terminal pra editar config files
- Cliente MCP instalado (ver abaixo)

## Instalar o pacote

```bash
git clone https://github.com/aulaterca/agente-dados-mcp.git
cd agente-dados-mcp
pip install -e .

# valida que o entry point existe
which agente-dados-mcp
```

Quando publicarmos no PyPI:

```bash
pip install agente-dados-mcp
# ou, sem instalar permanente:
uvx agente-dados-mcp
```

## Claude Code (CLI)

Arquivo: `~/.claude/mcp.json` (ou `.mcp.json` na raiz do projeto).

```json
{
  "mcpServers": {
    "agente-dados": {
      "command": "agente-dados-mcp"
    }
  }
}
```

Reinicie o Claude Code. As tools devem aparecer com o prefixo
`mcp__agente_dados__`.

## Claude Desktop (app)

Arquivo de config:
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

Mesmo formato do Claude Code:

```json
{
  "mcpServers": {
    "agente-dados": {
      "command": "agente-dados-mcp"
    }
  }
}
```

Reinicie o app.

## Cursor

`~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "agente-dados": {
      "command": "agente-dados-mcp"
    }
  }
}
```

Ou via UI: Settings → Features → Model Context Protocol → Add server.

## Windsurf

Settings → Model Context Protocol → adicionar:
- Command: `agente-dados-mcp`
- Transport: stdio

## Testando

Em qualquer cliente, depois de configurado:

> Você consegue listar suas tools MCP?

O agente deve listar `carregar_dataset`, `autorizar_colunas`,
`executar_analise`, `limpar_sessao`.

Pra uma demo rápida:

> Carregue o arquivo exemplos/adult.csv e me mostre o schema.

## Troubleshooting

**Tool não aparece:**
- `which agente-dados-mcp` retorna path?
- Cliente reiniciado depois de editar config?
- JSON do config é válido? (cole em jsonlint.com)

**Erro ao carregar CSV:**
- Path está absoluto ou relativo a partir do CWD do cliente?
- Arquivo termina em `.csv`?
- Permissão de leitura?

**PNG não aparece, só texto:**
- Cliente pode não suportar `ImageContent`. Use o link HTML do retorno.
- Verifique se `kaleido` está instalado (`pip show kaleido`).
