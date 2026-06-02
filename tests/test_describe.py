"""Testes do módulo describe.

Cobre:
  - estatísticas numéricas (mean/std/percentis/nulls)
  - estatísticas categóricas com k-anonymity (>=10)
  - escolha de colunas: autorizadas vence; sem autorização cai pro
    complemento das PII
  - dataframe vazio / sem coluna numérica / sem coluna categórica
  - colunas datetime caem em categóricas (não numéricas)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from agente_dados_mcp.describe import MIN_K, descrever


@pytest.fixture
def adult_like() -> pd.DataFrame:
    """Mini imitação do UCI Adult — uma numérica e uma categórica de cauda longa."""
    rng = np.random.default_rng(42)
    n = 300
    age = rng.integers(17, 90, size=n)
    education = rng.choice(
        ["HS-grad", "Some-college", "Bachelors", "Masters", "raras"],
        size=n,
        # 5 valores; 'raras' tem prob baixa pra produzir < 10 ocorrências.
        p=[0.45, 0.30, 0.15, 0.08, 0.02],
    )
    return pd.DataFrame({"age": age, "education": education})


def test_numerica_devolve_todas_estatisticas(adult_like: pd.DataFrame) -> None:
    r = descrever(adult_like, colunas_pii=[], colunas_autorizadas=[])
    assert "age" in r["numericas"]
    stats = r["numericas"]["age"]
    for chave in ("mean", "std", "min", "p25", "p50", "p75", "max", "nulls"):
        assert chave in stats
    assert 17 <= stats["min"] <= stats["p25"] <= stats["p50"] <= stats["p75"] <= stats["max"] <= 90


def test_categorica_corta_categorias_abaixo_do_k(adult_like: pd.DataFrame) -> None:
    r = descrever(adult_like, colunas_pii=[], colunas_autorizadas=[])
    educ = r["categoricas"]["education"]
    # Nenhuma categoria devolvida pode ter menos de MIN_K ocorrências.
    for _valor, contagem in educ["top_categorias"]:
        assert contagem >= MIN_K
    # E o resumo nos diz quantas a gente cortou — em vez de "esconder
    # silenciosamente".
    assert educ["categorias_pequenas_omitidas"] >= 0
    assert educ["limiar_k"] == MIN_K


def test_unique_total_ignora_corte_de_k(adult_like: pd.DataFrame) -> None:
    """`unique` é cardinalidade real — não afetada pelo filtro k>=10."""
    r = descrever(adult_like, colunas_pii=[], colunas_autorizadas=[])
    educ = r["categoricas"]["education"]
    assert educ["unique"] == adult_like["education"].nunique()


def test_colunas_autorizadas_tem_precedencia_sobre_pii() -> None:
    df = pd.DataFrame({"age": [25, 30, 35] * 5, "name": ["a", "b", "c"] * 5})
    # PII detectada em 'name' E em 'age', mas usuário autorizou só 'age'.
    r = descrever(df, colunas_pii=["name", "age"], colunas_autorizadas=["age"])
    assert "age" in r["numericas"]
    assert "name" not in r["categoricas"]
    # `omitidas` fica vazio porque a autorização explícita "ganha do default".
    assert r["colunas_omitidas_por_pii_nao_autorizada"] == []


def test_sem_autorizacao_omite_colunas_pii() -> None:
    df = pd.DataFrame({"age": [25, 30, 35] * 5, "name": ["a", "b", "c"] * 5})
    r = descrever(df, colunas_pii=["name"], colunas_autorizadas=[])
    # 'age' não-PII entra; 'name' fica de fora e é listada como omitida.
    assert "age" in r["numericas"]
    assert "name" not in r["categoricas"]
    assert r["colunas_omitidas_por_pii_nao_autorizada"] == ["name"]


def test_serie_so_com_nulos_devolve_stats_nulas() -> None:
    df = pd.DataFrame({"x": [None, None, None]})
    df["x"] = df["x"].astype(float)
    r = descrever(df, colunas_pii=[], colunas_autorizadas=[])
    stats = r["numericas"]["x"]
    assert stats["mean"] is None
    assert stats["nulls"] == 3


def test_dataframe_sem_coluna_numerica() -> None:
    df = pd.DataFrame({"cat": ["a"] * 30 + ["b"] * 30})
    r = descrever(df, colunas_pii=[], colunas_autorizadas=[])
    assert r["numericas"] == {}
    assert "cat" in r["categoricas"]


def test_dataframe_sem_coluna_categorica() -> None:
    df = pd.DataFrame({"x": list(range(50)), "y": [float(i) for i in range(50)]})
    r = descrever(df, colunas_pii=[], colunas_autorizadas=[])
    assert set(r["numericas"]) == {"x", "y"}
    assert r["categoricas"] == {}


def test_datetime_cai_em_categorica_e_nao_em_numerica() -> None:
    df = pd.DataFrame(
        {
            "data": pd.date_range("2024-01-01", periods=30, freq="D"),
            "valor": list(range(30)),
        }
    )
    r = descrever(df, colunas_pii=[], colunas_autorizadas=[])
    assert "data" not in r["numericas"]  # não tiramos média de timestamp
    assert "data" in r["categoricas"]
    assert "valor" in r["numericas"]


def test_total_linhas_reflete_dataframe_inteiro_nao_subset() -> None:
    df = pd.DataFrame({"a": list(range(40)), "b": ["x"] * 40})
    r = descrever(df, colunas_pii=["a"], colunas_autorizadas=[])
    # 'a' foi omitida da descrição, mas o total continua sendo o df inteiro.
    assert r["total_linhas"] == 40
