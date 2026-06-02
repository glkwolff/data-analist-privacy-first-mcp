"""MCP server entry point.

Registra as quatro tools (carregar_dataset, autorizar_colunas, executar_analise,
limpar_sessao) via FastMCP e roda no transporte stdio.

Ver CLAUDE.md seção 7 — as tool descriptions estão em prompts.py e são parte
do entregável avaliado.
"""

from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ImageContent, TextContent

from . import prompts
from .describe import descrever
from .executor import executar
from .loader import carregar
from .renderer import fig_para_html, fig_para_png_base64, resumo_markdown
from .schema import extrair_schema
from .state import SESSION
from .validator import validar_codigo

mcp = FastMCP("agente-dados-mcp")


@mcp.tool(name="carregar_dataset", description=prompts.DESC_CARREGAR)
def carregar_dataset(caminho: str) -> dict[str, Any]:
    caminho_expandido = os.path.expanduser(caminho)

    df, erro = carregar(caminho_expandido)
    if erro is not None:
        return {"ok": False, "erro": erro}

    SESSION.reset()
    SESSION.df = df
    SESSION.caminho_atual = caminho_expandido
    schema = extrair_schema(df)
    SESSION.colunas_pii = schema["colunas_pii"]
    SESSION.schema_cache = schema

    return schema


@mcp.tool(name="autorizar_colunas", description=prompts.DESC_AUTORIZAR)
def autorizar_colunas(autorizadas: list[str]) -> dict[str, Any]:
    if not SESSION.carregado:
        return {
            "ok": False,
            "erro": "Nenhum dataset carregado. Chame `carregar_dataset` primeiro.",
        }

    cols_existentes = set(SESSION.df.columns) if SESSION.df is not None else set()
    validas = [c for c in autorizadas if c in cols_existentes]
    invalidas = [c for c in autorizadas if c not in cols_existentes]
    nao_autorizadas = sorted(cols_existentes - set(validas))

    SESSION.colunas_autorizadas = validas

    resposta: dict[str, Any] = {
        "ok": True,
        "autorizadas": validas,
        "nao_autorizadas": nao_autorizadas,
    }
    if invalidas:
        resposta["ignoradas_nao_existem"] = invalidas
    return resposta


@mcp.tool(name="descrever_dataset", description=prompts.DESC_DESCREVER)
def descrever_dataset() -> dict[str, Any]:
    if not SESSION.carregado:
        return {
            "ok": False,
            "erro": "Nenhum dataset carregado. Chame `carregar_dataset` primeiro.",
        }
    return descrever(
        SESSION.df,
        SESSION.colunas_pii,
        SESSION.colunas_autorizadas,
    )


@mcp.tool(name="executar_analise", description=prompts.DESC_EXECUTAR)
def executar_analise(codigo: str, descricao: str) -> list[Any]:
    if not SESSION.carregado:
        return [
            TextContent(
                type="text",
                text="ERRO: nenhum dataset carregado. Chame `carregar_dataset` primeiro.",
            )
        ]

    ok_val, msg_val = validar_codigo(codigo)
    if not ok_val:
        return [
            TextContent(
                type="text",
                text=(
                    "Código BLOQUEADO pelo validador AST.\n"
                    f"Motivo: {msg_val}\n\n"
                    "Reescreva usando apenas pandas, numpy e plotly."
                ),
            )
        ]

    ok_exec, fig, msg_exec = executar(codigo, SESSION.df)
    if not ok_exec:
        return [TextContent(type="text", text=msg_exec)]

    try:
        png_b64 = fig_para_png_base64(fig)
    except Exception as e:  # noqa: BLE001
        return [
            TextContent(
                type="text",
                text=(
                    f"Gráfico foi gerado mas a renderização do PNG falhou: "
                    f"{type(e).__name__}: {e}\n"
                    f"(Provável: falta o pacote `kaleido`.)"
                ),
            )
        ]

    try:
        caminho_html = fig_para_html(fig)
        link_html = f"[Abrir dashboard interativo](file://{caminho_html})"
    except Exception as e:  # noqa: BLE001
        link_html = f"(falhou ao gravar HTML: {e})"

    resumo = resumo_markdown(fig, descricao)

    return [
        ImageContent(type="image", data=png_b64, mimeType="image/png"),
        TextContent(type="text", text=resumo),
        TextContent(type="text", text=link_html),
    ]


@mcp.tool(name="limpar_sessao", description=prompts.DESC_LIMPAR)
def limpar_sessao() -> dict[str, Any]:
    SESSION.reset()
    return {"ok": True, "mensagem": "Sessão limpa"}


def main() -> None:
    """Entry point CLI — inicia o servidor MCP em stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
