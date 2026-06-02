"""Testes do módulo quality.

Cobre:
  - detecção de nulos (contagem + fração)
  - detecção de duplicatas
  - outliers via regra IQR de Tukey (1.5*IQR)
  - distribuições anômalas: constante, quase-constante, assimetria,
    cardinalidade alta
  - escolha de colunas (autorizadas vs PII)
  - bordas: poucos pontos, IQR=0, dataframe vazio
  - privacy: o retorno NÃO contém valores individuais.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from agente_dados_mcp.quality import (
    CARDINALIDADE_ALTA_FRACAO,
    DOMINANCIA_LIMIAR,
    SKEW_LIMIAR,
    analisar,
)


@pytest.fixture
def df_limpo() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    n = 200
    return pd.DataFrame(
        {
            # `valor` é float aleatório — colisão por acaso é improvável.
            "valor": rng.normal(loc=50, scale=10, size=n),
            "age": rng.integers(20, 60, size=n),
            "category": rng.choice(["a", "b", "c"], size=n, p=[0.5, 0.3, 0.2]),
        }
    )


def test_dataframe_limpo_nao_acusa_nulos_nem_duplicatas(df_limpo: pd.DataFrame) -> None:
    r = analisar(df_limpo, colunas_pii=[], colunas_autorizadas=[])
    assert r["nulos"] == {}
    assert r["duplicatas"]["linhas_duplicadas"] == 0


def test_detecta_nulos_com_fracao() -> None:
    df = pd.DataFrame({"x": [1, 2, None, 4, None, None]})
    r = analisar(df, colunas_pii=[], colunas_autorizadas=[])
    assert "x" in r["nulos"]
    assert r["nulos"]["x"]["nulos"] == 3
    assert r["nulos"]["x"]["fracao"] == 0.5


def test_detecta_duplicatas_exatas() -> None:
    df = pd.DataFrame(
        {"a": [1, 1, 2, 3, 3, 3], "b": ["x", "x", "y", "z", "z", "z"]}
    )
    r = analisar(df, colunas_pii=[], colunas_autorizadas=[])
    # (1,'x') aparece 2x -> 1 dup; (3,'z') aparece 3x -> 2 dups. Total: 3.
    assert r["duplicatas"]["linhas_duplicadas"] == 3
    assert r["duplicatas"]["fracao"] == 0.5


def test_outliers_iqr_detecta_pontos_fora_de_tukey() -> None:
    # Distribuição uniforme + 3 valores extremos.
    rng = np.random.default_rng(0)
    valores = list(rng.normal(loc=50, scale=5, size=100)) + [1000, 1001, 1002]
    df = pd.DataFrame({"x": valores})
    r = analisar(df, colunas_pii=[], colunas_autorizadas=[])
    assert "x" in r["outliers_iqr"]
    out = r["outliers_iqr"]["x"]
    assert out["n_outliers"] >= 3
    # O retorno NÃO inclui a lista de valores que vazaram — privacy.
    assert "valores" not in out
    assert "amostra" not in out


def test_outliers_iqr_pula_coluna_com_iqr_zero() -> None:
    df = pd.DataFrame({"x": [5] * 50})  # quartis iguais -> IQR=0
    r = analisar(df, colunas_pii=[], colunas_autorizadas=[])
    assert "x" not in r["outliers_iqr"]


def test_outliers_iqr_pula_coluna_com_poucos_pontos() -> None:
    df = pd.DataFrame({"x": [1, 2, 3]})  # < 4 pontos -> não confia
    r = analisar(df, colunas_pii=[], colunas_autorizadas=[])
    assert "x" not in r["outliers_iqr"]


def test_distribuicao_constante_numerica() -> None:
    df = pd.DataFrame({"x": [7] * 50, "outra": list(range(50))})
    r = analisar(df, colunas_pii=[], colunas_autorizadas=[])
    assert "x" in r["distribuicoes_anomalas"]
    assert "constante" in r["distribuicoes_anomalas"]["x"]["achados"]


def test_distribuicao_assimetrica_e_marcada_como_skew() -> None:
    # Distribuição exponencial é fortemente assimétrica (skew > 2).
    rng = np.random.default_rng(7)
    df = pd.DataFrame({"renda": rng.exponential(scale=1000, size=500)})
    r = analisar(df, colunas_pii=[], colunas_autorizadas=[])
    achados = r["distribuicoes_anomalas"].get("renda", {}).get("achados", [])
    assert any("assimetria" in a for a in achados)


def test_categorica_constante_e_marcada() -> None:
    df = pd.DataFrame({"cat": ["x"] * 100})
    r = analisar(df, colunas_pii=[], colunas_autorizadas=[])
    achados = r["distribuicoes_anomalas"]["cat"]["achados"]
    assert "constante" in achados


def test_categorica_quase_constante() -> None:
    df = pd.DataFrame({"cat": ["x"] * 98 + ["y", "z"]})
    r = analisar(df, colunas_pii=[], colunas_autorizadas=[])
    achados = r["distribuicoes_anomalas"]["cat"]["achados"]
    assert any("quase_constante" in a for a in achados)


def test_categorica_cardinalidade_alta_parece_id() -> None:
    df = pd.DataFrame({"id": [f"u{i}" for i in range(200)]})
    r = analisar(df, colunas_pii=[], colunas_autorizadas=[])
    achados = r["distribuicoes_anomalas"]["id"]["achados"]
    assert any("cardinalidade_alta" in a for a in achados)


def test_omite_colunas_pii_sem_autorizacao() -> None:
    df = pd.DataFrame({"age": [30] * 30, "name": ["a"] * 30})
    r = analisar(df, colunas_pii=["name"], colunas_autorizadas=[])
    assert "age" in r["colunas_analisadas"]
    assert "name" not in r["colunas_analisadas"]
    assert r["colunas_omitidas_por_pii_nao_autorizada"] == ["name"]


def test_colunas_autorizadas_vence_pii() -> None:
    df = pd.DataFrame({"age": [30] * 30, "name": ["a"] * 30})
    r = analisar(df, colunas_pii=["name", "age"], colunas_autorizadas=["age"])
    assert r["colunas_analisadas"] == ["age"]
    # Autorização explícita zera o relato de "omitidas".
    assert r["colunas_omitidas_por_pii_nao_autorizada"] == []


def test_dataframe_vazio_nao_quebra() -> None:
    df = pd.DataFrame({"x": [], "y": []})
    r = analisar(df, colunas_pii=[], colunas_autorizadas=[])
    assert r["nulos"] == {}
    assert r["duplicatas"]["linhas_duplicadas"] == 0
    assert r["outliers_iqr"] == {}


def test_limiares_expostos_no_retorno() -> None:
    """Os números que o detector usa entram no retorno pra transparência."""
    df = pd.DataFrame({"x": list(range(50))})
    r = analisar(df, colunas_pii=[], colunas_autorizadas=[])
    assert r["limiares"]["skew_forte"] == SKEW_LIMIAR
    assert r["limiares"]["dominancia_quase_constante"] == DOMINANCIA_LIMIAR
    assert r["limiares"]["fracao_cardinalidade_alta"] == CARDINALIDADE_ALTA_FRACAO
