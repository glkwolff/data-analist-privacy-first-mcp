"""Testes do executor sandboxed."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from agente_dados_mcp.executor import executar


def _df_simples() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "categoria": ["A", "B", "A", "B", "C"],
            "valor": [10, 20, 30, 40, 50],
        }
    )


def test_executa_groupby_simples():
    codigo = (
        "import plotly.express as px\n"
        "resumo = df.groupby('categoria')['valor'].sum().reset_index()\n"
        "fig = px.bar(resumo, x='categoria', y='valor')\n"
    )
    ok, fig, msg = executar(codigo, _df_simples())
    assert ok, msg
    assert isinstance(fig, go.Figure)


def test_falha_se_fig_nao_for_criada():
    codigo = "x = 1 + 1"
    ok, fig, msg = executar(codigo, _df_simples())
    assert not ok
    assert fig is None
    assert "fig" in msg.lower()


def test_falha_se_fig_for_tipo_errado():
    codigo = "fig = 42"
    ok, fig, msg = executar(codigo, _df_simples())
    assert not ok
    assert "Plotly Figure" in msg


def test_erro_runtime_e_capturado():
    codigo = "fig = df['inexistente'].sum()"
    ok, fig, msg = executar(codigo, _df_simples())
    assert not ok
    assert "Erro na execução" in msg


def test_builtins_perigosos_nao_acessiveis():
    """Mesmo se o validador deixar passar algo, o namespace não tem builtins ruins."""
    codigo = "fig = open('/etc/passwd')"
    ok, fig, msg = executar(codigo, _df_simples())
    assert not ok
    # Falha em runtime porque open() não está nos _SAFE_BUILTINS
