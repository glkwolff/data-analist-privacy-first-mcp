"""Testes da extração de schema — privacy invariant central."""

from __future__ import annotations

import pandas as pd

from agente_dados_mcp.schema import extrair_schema


def test_schema_nao_contem_valores_individuais():
    """Privacy invariant: schema NUNCA deve conter valor de célula."""
    df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "email": ["a@x.com", "b@x.com", "c@x.com", "d@x.com", "e@x.com"],
            "valor": [100.5, 200.7, 300.1, 400.9, 500.0],
        }
    )
    result = extrair_schema(df)

    payload = str(result)
    for valor_proibido in ("a@x.com", "b@x.com", "100.5", "200.7", "300.1"):
        assert valor_proibido not in payload, (
            f"Schema vazou valor: {valor_proibido}"
        )


def test_schema_estrutura_esperada():
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", None]})
    result = extrair_schema(df)

    assert result["ok"] is True
    assert result["total_linhas"] == 3
    assert "a" in result["schema"]
    assert "b" in result["schema"]
    assert result["schema"]["a"]["nulos"] == 0
    assert result["schema"]["b"]["nulos"] == 1
    assert result["schema"]["a"]["cardinalidade"] == 3
    assert result["schema"]["b"]["cardinalidade"] == 2


def test_schema_marca_pii_corretamente():
    df = pd.DataFrame(
        {
            "email": ["a@x.com", "b@x.com"],
            "valor": [1.0, 2.0],
        }
    )
    result = extrair_schema(df)
    assert result["schema"]["email"]["is_pii_suspeita"] is True
    assert result["schema"]["valor"]["is_pii_suspeita"] is False
    assert "email" in result["colunas_pii"]
    assert "valor" not in result["colunas_pii"]
