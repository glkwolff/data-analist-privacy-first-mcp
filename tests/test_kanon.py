"""Testes da validação de k-anonimidade pós-execução.

Cobre:
  - bloqueio estrito em pie / histogram / bar (de contagem)
  - PASSAGEM em bar com agregação não-contagem (ex.: mean)
  - PASSAGEM em scatter / box / line / heatmap (fora do escopo)
  - mensagem inclui rótulo truncado, limite de 10 violações reportadas
  - configuração de k diferente do padrão
"""

from __future__ import annotations

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import pytest

from agente_dados_mcp.kanon import K_PADRAO, MAX_VIOLACOES_REPORTADAS, verificar


# ---------------------------------------------------------------------------
# pie
# ---------------------------------------------------------------------------


def test_pie_com_fatia_pequena_bloqueia() -> None:
    fig = go.Figure(go.Pie(labels=["a", "b", "c"], values=[100, 50, 3]))
    ok, msg = verificar(fig)
    assert not ok
    assert "pizza" in msg
    assert "'c'" in msg
    assert "3" in msg


def test_pie_todas_fatias_ok_passa() -> None:
    fig = go.Figure(go.Pie(labels=["a", "b"], values=[100, 50]))
    ok, _ = verificar(fig)
    assert ok


def test_pie_com_zero_nao_e_bloqueado() -> None:
    """Bucket de tamanho 0 = categoria que não existe, não é leak."""
    fig = go.Figure(go.Pie(labels=["a", "b", "c"], values=[100, 50, 0]))
    ok, _ = verificar(fig)
    assert ok


def test_pie_via_px_com_labels_ndarray_nao_quebra() -> None:
    """Regressão: px.pie guarda labels/values como np.ndarray.

    O idioma `getattr(...) or []` forçava bool(ndarray) e levantava
    "truth value of an array ... is ambiguous". A verificação deve
    tratar arrays sem erro e aprovar quando todas as fatias têm >= K.
    """
    import pandas as pd

    dados = pd.DataFrame(
        {"cat": ["a", "b", "c"], "qtd": [100, 50, 30]}
    )
    fig = px.pie(dados, names="cat", values="qtd")
    assert isinstance(fig.data[0].labels, np.ndarray)  # pré-condição do bug
    ok, _ = verificar(fig)
    assert ok


def test_pie_com_labels_ndarray_e_fatia_pequena_bloqueia() -> None:
    """Mesmo com labels/values como ndarray, a regra de k ainda morde."""
    fig = go.Figure(
        go.Pie(labels=np.array(["a", "b", "c"]), values=np.array([100, 50, 3]))
    )
    ok, msg = verificar(fig)
    assert not ok
    assert "'c'" in msg


# ---------------------------------------------------------------------------
# bar
# ---------------------------------------------------------------------------


def test_bar_de_contagem_com_barra_pequena_bloqueia() -> None:
    fig = go.Figure(go.Bar(x=["x", "y", "z"], y=[50, 30, 2]))
    ok, msg = verificar(fig)
    assert not ok
    assert "barras" in msg
    assert "'z'" in msg


def test_bar_de_media_nao_e_bloqueado_mesmo_com_y_baixo() -> None:
    """Bar com média (não-inteiro) está fora do escopo desta camada."""
    fig = go.Figure(go.Bar(x=["a", "b", "c"], y=[3.7, 2.1, 4.2]))
    ok, _ = verificar(fig)
    assert ok


def test_bar_de_media_com_inteiros_baixos_e_legitimo() -> None:
    """Caso ambíguo: y são inteiros mas representam mediana / contagem real.

    Trade-off: tratamos como contagem (bloqueia). O LLM pode reagir
    devolvendo o gráfico em outra unidade ou agregando em faixas.
    """
    fig = go.Figure(go.Bar(x=["a", "b"], y=[5, 7]))
    ok, _ = verificar(fig)
    assert not ok


def test_bar_de_contagem_todas_ok_passa() -> None:
    fig = go.Figure(go.Bar(x=["a", "b", "c"], y=[40, 25, 18]))
    ok, _ = verificar(fig)
    assert ok


# ---------------------------------------------------------------------------
# histogram
# ---------------------------------------------------------------------------


def test_histograma_com_bin_pequeno_bloqueia() -> None:
    rng = np.random.default_rng(0)
    # cluster grande em torno de 50 + um único outlier longe -> bin pequeno
    valores = list(rng.normal(loc=50, scale=2, size=500)) + [10000.0]
    fig = px.histogram(x=valores)
    ok, msg = verificar(fig)
    assert not ok
    assert "histograma" in msg


def test_histograma_distribuicao_densa_passa() -> None:
    """Uniforme não tem cauda fina, então nenhum bin fica abaixo de k.

    Nota de design: distribuições com cauda longa (normal, exponencial)
    quase sempre vão ter bins pequenos nas caudas e DEVEM ser bloqueadas.
    Isso é correto: alguém na cauda longe de um histograma de idade é
    identificável. A saída do LLM é agregar em faixas maiores antes de
    plotar.
    """
    rng = np.random.default_rng(0)
    valores = list(rng.uniform(0, 100, size=10000))
    fig = px.histogram(x=valores)
    ok, _ = verificar(fig)
    assert ok


# ---------------------------------------------------------------------------
# Tipos fora do escopo: scatter, box, line, heatmap
# ---------------------------------------------------------------------------


def test_scatter_com_poucos_pontos_nao_e_bloqueado() -> None:
    """Scatter mostra pontos individuais por design — k-anonymity
    desse formato é responsabilidade do LLM seguir DESC_EXECUTAR.
    """
    fig = go.Figure(go.Scatter(x=[1, 2, 3], y=[10, 20, 30], mode="markers"))
    ok, _ = verificar(fig)
    assert ok


def test_box_plot_nao_e_bloqueado() -> None:
    fig = go.Figure(go.Box(y=[1, 2, 3, 4, 5]))
    ok, _ = verificar(fig)
    assert ok


def test_line_chart_nao_e_bloqueado() -> None:
    fig = go.Figure(go.Scatter(x=[1, 2, 3], y=[5, 7, 6], mode="lines"))
    ok, _ = verificar(fig)
    assert ok


def test_heatmap_nao_e_bloqueado() -> None:
    fig = go.Figure(go.Heatmap(z=[[1, 2], [3, 4]]))
    ok, _ = verificar(fig)
    assert ok


# ---------------------------------------------------------------------------
# Mensagem
# ---------------------------------------------------------------------------


def test_mensagem_trunca_rotulo_longo() -> None:
    rotulo_longo = "x" * 200
    fig = go.Figure(go.Bar(x=[rotulo_longo, "b"], y=[3, 50]))
    ok, msg = verificar(fig)
    assert not ok
    # Truncamento garante mensagem compacta — não logamos o rótulo inteiro.
    assert "x" * 200 not in msg


def test_mensagem_limita_quantidade_de_violacoes() -> None:
    # 20 fatias todas com count=1
    labels = [f"cat_{i}" for i in range(20)]
    values = [1] * 20
    fig = go.Figure(go.Pie(labels=labels, values=values))
    ok, msg = verificar(fig)
    assert not ok
    qtd_linhas = msg.count("  - ")
    assert qtd_linhas <= MAX_VIOLACOES_REPORTADAS
    assert "mais" in msg  # rodapé "... e mais N buckets pequenos"


def test_mensagem_indica_como_corrigir() -> None:
    fig = go.Figure(go.Bar(x=["a", "b"], y=[3, 50]))
    ok, msg = verificar(fig)
    assert not ok
    # Sugestão pragmática pro LLM agir, em vez de só "deu errado".
    for chave in ("faixas", "outros", "filtre"):
        assert chave in msg.lower()


# ---------------------------------------------------------------------------
# k configurável
# ---------------------------------------------------------------------------


def test_k_padrao_e_dez() -> None:
    assert K_PADRAO == 10


def test_k_configuravel_libera_buckets_menores() -> None:
    fig = go.Figure(go.Bar(x=["a", "b"], y=[5, 50]))
    ok_default, _ = verificar(fig)
    assert not ok_default
    ok_relaxado, _ = verificar(fig, k=3)
    assert ok_relaxado


# ---------------------------------------------------------------------------
# Figura vazia
# ---------------------------------------------------------------------------


def test_figura_sem_traces_passa() -> None:
    fig = go.Figure()
    ok, _ = verificar(fig)
    assert ok
