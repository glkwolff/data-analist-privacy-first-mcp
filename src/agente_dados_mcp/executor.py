"""Execução sandboxed do código aprovado pelo validador.

Roda em namespace controlado: apenas df, pd, np, px, go disponíveis.
Builtins reduzidos a um subconjunto seguro.

Pré-condição: código JÁ passou pelo validator. Este módulo NÃO revalida —
chame validar_codigo() antes de chamar executar().
"""

from __future__ import annotations

from typing import Any

_SAFE_NAMES = (
    "abs", "all", "any", "bool", "dict", "enumerate", "filter", "float",
    "int", "isinstance", "issubclass", "len", "list", "map", "max", "min",
    "range", "reversed", "round", "set", "slice", "sorted", "str", "sum",
    "tuple", "type", "zip", "True", "False", "None",
    "ValueError", "TypeError", "KeyError", "IndexError", "Exception",
    "print", "repr", "format", "iter", "next",
    # __import__ é necessário pra `import` statements funcionarem dentro do exec.
    # Bibliotecas perigosas já foram bloqueadas pelo AST validator antes
    # de chegar aqui, e chamadas diretas a __import__() também são bloqueadas.
    "__import__",
)


def _resolver_builtins() -> dict:
    src = __builtins__ if isinstance(__builtins__, dict) else vars(__builtins__)
    return {nome: src[nome] for nome in _SAFE_NAMES if nome in src}


_SAFE_BUILTINS = _resolver_builtins()


def executar(codigo: str, df) -> tuple[bool, Any, str]:
    """Executa o código contra df num namespace controlado.

    Retorna (ok, fig_ou_None, mensagem).
    - ok=True: fig é objeto Plotly Figure (validar antes de renderizar)
    - ok=False: mensagem explica o erro
    """
    import numpy as np
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go

    namespace: dict[str, Any] = {
        "__builtins__": _SAFE_BUILTINS,
        "df": df,
        "pd": pd,
        "np": np,
        "px": px,
        "go": go,
    }

    try:
        exec(codigo, namespace)
    except Exception as e:  # noqa: BLE001 — runtime do código do LLM, queremos pegar tudo
        return False, None, f"Erro na execução: {type(e).__name__}: {e}"

    fig = namespace.get("fig")
    if fig is None:
        return False, None, "O código executou mas não criou a variável `fig`."

    if not isinstance(fig, go.Figure):
        return False, None, (
            f"A variável `fig` não é um objeto Plotly Figure "
            f"(é {type(fig).__name__}). Reescreva usando plotly.express ou plotly.graph_objects."
        )

    return True, fig, "OK"
