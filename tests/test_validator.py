"""Testes do validador AST.

CLAUDE.md seção 9 lista os casos obrigatórios — esta suite cobre todos.
"""

from __future__ import annotations

import pytest

from agente_dados_mcp.validator import validar_codigo

CASOS_VALIDOS = [
    "import pandas as pd\nfig = pd.DataFrame()",
    "import plotly.express as px\nfig = px.bar(df, x='a')",
    "fig = df.groupby('x').mean().reset_index()",
    "import pandas as pd\nimport plotly.express as px\nresumo = df.groupby('cat').size().reset_index(name='n')\nfig = px.bar(resumo, x='cat', y='n')",
    "import numpy as np\nimport plotly.graph_objects as go\nfig = go.Figure(data=[go.Bar(x=[1, 2, 3], y=[4, 5, 6])])",
    "from plotly import express as px\nfig = px.line(df, x='a', y='b')",
    "fig = df.dropna().groupby('cat').agg({'val': 'mean'}).reset_index()",
]


CASOS_BLOQUEADOS = [
    ("import os", "Módulo proibido"),
    ("import sys", "Módulo proibido"),
    ("import subprocess", "Módulo proibido"),
    ("import requests", "Módulo proibido"),
    ("import urllib", "Módulo proibido"),
    ("import socket", "Módulo proibido"),
    ("from os import path", "Módulo proibido"),
    ("from pathlib import Path", "Módulo proibido"),
    ("__import__('os')", "Função proibida"),
    ("eval('print(1)')", "Função proibida"),
    ("exec('x = 1')", "Função proibida"),
    ("open('/etc/passwd').read()", "Função proibida"),
    ("df.__class__.__bases__", "dunder proibido"),
    ("().__class__.__bases__[0].__subclasses__()", "dunder proibido"),
    ("globals()", "Função proibida"),
    ("locals()", "Função proibida"),
    ("import sklearn", "não permitida"),
    ("compile('1+1', '<x>', 'eval')", "Função proibida"),
]


@pytest.mark.parametrize("codigo", CASOS_VALIDOS)
def test_codigo_valido_passa(codigo: str) -> None:
    ok, msg = validar_codigo(codigo)
    assert ok, f"Esperava aprovação mas validador disse: {msg!r}"


@pytest.mark.parametrize("codigo,esperado", CASOS_BLOQUEADOS)
def test_codigo_perigoso_bloqueado(codigo: str, esperado: str) -> None:
    ok, msg = validar_codigo(codigo)
    assert not ok, f"Código deveria ser bloqueado mas passou: {codigo!r}"
    assert esperado.lower() in msg.lower(), (
        f"Mensagem {msg!r} não menciona {esperado!r}"
    )


def test_syntax_error_e_bloqueado() -> None:
    ok, msg = validar_codigo("fig = (")
    assert not ok
    assert "não é Python válido" in msg


def test_codigo_vazio_e_valido_mas_inutil() -> None:
    # String vazia parsea (sem statements) — validador passa.
    # O executor é quem vai reclamar que `fig` não foi criado.
    ok, _ = validar_codigo("")
    assert ok
