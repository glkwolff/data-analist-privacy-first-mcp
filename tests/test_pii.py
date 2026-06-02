"""Testes da detecção de PII (duas camadas)."""

from __future__ import annotations

import pandas as pd

from agente_dados_mcp.pii import (
    colunas_suspeitas_por_nome,
    detectar_pii,
    detectar_pii_em_valores,
)


def test_nome_de_coluna_suspeito_pega_email_e_cpf():
    df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "email": ["a@x.com", "b@x.com", "c@x.com"],
            "cpf": ["111", "222", "333"],
            "valor": [10.0, 20.0, 30.0],
        }
    )
    suspeitas = colunas_suspeitas_por_nome(df)
    assert "email" in suspeitas
    assert "cpf" in suspeitas
    assert "valor" not in suspeitas
    assert "id" not in suspeitas


def test_nome_de_coluna_suspeito_normaliza_separadores_e_case():
    df = pd.DataFrame(
        {
            "Native-Country": ["BR", "US"],
            "Native Country": ["BR", "US"],
            "NATIVE_COUNTRY": ["BR", "US"],
        }
    )
    suspeitas = colunas_suspeitas_por_nome(df)
    # As três variantes devem cair em "native_country"
    assert len(suspeitas) == 3


def test_regex_detecta_cpf_em_amostra():
    df = pd.DataFrame({"doc": ["123.456.789-01", "outra coisa", "987.654.321-00"]})
    achados = detectar_pii_em_valores(df)
    assert "doc" in achados
    assert "cpf" in achados["doc"]


def test_regex_detecta_email_em_amostra():
    df = pd.DataFrame({"contato": ["foo@bar.com", "vazio", "outro@xy.io"]})
    achados = detectar_pii_em_valores(df)
    assert "contato" in achados
    assert "email" in achados["contato"]


def test_regex_nao_dispara_em_coluna_limpa():
    df = pd.DataFrame({"categoria": ["A", "B", "C"] * 10})
    achados = detectar_pii_em_valores(df)
    assert "categoria" not in achados


def test_detectar_pii_uniao_das_duas_camadas():
    df = pd.DataFrame(
        {
            "email": ["a@x.com", "b@x.com"],
            "outro": ["foo@bar.com", "qux@baz.com"],
            "categoria": ["A", "B"],
        }
    )
    achados = detectar_pii(df)
    assert "email" in achados  # nome + regex
    assert "outro" in achados  # só regex
    assert "categoria" not in achados


def test_adult_income_tipico():
    """Replica colunas do dataset UCI Adult — devem ser flaggeadas."""
    df = pd.DataFrame(
        {
            "age": [25, 30, 40],
            "race": ["White", "Black", "Asian"],
            "sex": ["Male", "Female", "Male"],
            "native-country": ["United-States", "Cuba", "Jamaica"],
            "income": [">50K", "<=50K", ">50K"],
            "education": ["Bachelors", "HS-grad", "Masters"],
        }
    )
    achados = detectar_pii(df)
    for esperada in ("age", "race", "sex", "native-country", "income"):
        assert esperada in achados, f"{esperada} deveria ser flaggeada"
