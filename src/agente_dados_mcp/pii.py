"""Detecção de PII em duas camadas: nome de coluna + regex em amostra.

Sem Presidio (overkill pro escopo — ver CLAUDE.md seção 6).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


COLUNAS_SUSPEITAS = {
    "cpf", "cnpj", "rg", "email", "e-mail", "mail",
    "telefone", "celular", "phone", "fone",
    "nome", "name", "sobrenome", "surname", "fullname",
    "endereco", "endereço", "address", "rua", "cep", "zip", "postal",
    "data_nascimento", "birthdate", "dob", "nascimento",
    "idade", "age",
    "gender", "sexo", "sex",
    "race", "raca", "raça", "etnia", "ethnicity",
    "religiao", "religião", "religion",
    "salario", "salário", "salary", "income", "renda", "wage",
    "usuario", "usuário", "username", "user_id", "customer_id",
    "native_country", "native-country",
}


PADROES_REGEX = {
    "cpf": re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"),
    "cnpj": re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b"),
    "email": re.compile(r"\b[\w\.-]+@[\w\.-]+\.\w+\b"),
    "telefone_br": re.compile(r"\(?\d{2}\)?\s?9?\d{4}-?\d{4}"),
}


def _normalizar(nome: str) -> str:
    return nome.lower().strip().replace(" ", "_").replace("-", "_")


def colunas_suspeitas_por_nome(df: pd.DataFrame) -> list[str]:
    return [col for col in df.columns if _normalizar(str(col)) in COLUNAS_SUSPEITAS]


def detectar_pii_em_valores(df: pd.DataFrame, amostra: int = 200) -> dict[str, list[str]]:
    """Retorna {coluna: [tipos_detectados]} para colunas object com padrão match."""
    encontrados: dict[str, list[str]] = {}
    cols_texto = df.select_dtypes(include=["object", "string"]).columns
    for col in cols_texto:
        try:
            valores = df[col].dropna().astype(str).head(amostra).tolist()
        except Exception:
            continue
        tipos: list[str] = []
        for tipo, padrao in PADROES_REGEX.items():
            if any(padrao.search(v) for v in valores):
                tipos.append(tipo)
        if tipos:
            encontrados[col] = tipos
    return encontrados


def detectar_pii(df: pd.DataFrame, amostra: int = 200) -> dict[str, list[str]]:
    """União das duas camadas. Retorna {coluna: [tipos]} onde tipos pode
    incluir 'nome_suspeito' quando só o nome bateu.
    """
    resultado: dict[str, list[str]] = {}
    for col in colunas_suspeitas_por_nome(df):
        resultado.setdefault(col, []).append("nome_suspeito")
    for col, tipos in detectar_pii_em_valores(df, amostra).items():
        resultado.setdefault(col, []).extend(tipos)
    return resultado
