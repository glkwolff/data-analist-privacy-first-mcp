"""Extração de schema do DataFrame para retornar ao LLM.

NUNCA inclui valores individuais — só estrutura, contagens e cardinalidade.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .pii import detectar_pii

if TYPE_CHECKING:
    import pandas as pd


def extrair_schema(df: pd.DataFrame, amostra_pii: int = 200) -> dict:
    """Retorna dict no formato documentado em DESC_CARREGAR (prompts.py).

    Privacy invariant: nada que sai daqui inclui valores de células.
    """
    pii_map = detectar_pii(df, amostra=amostra_pii)
    pii_cols = set(pii_map.keys())

    schema: dict[str, dict] = {}
    for col in df.columns:
        dtype = str(df[col].dtype)
        try:
            nulos = int(df[col].isna().sum())
        except Exception:
            nulos = 0
        try:
            cardinalidade = int(df[col].nunique(dropna=True))
        except Exception:
            cardinalidade = 0

        tipos_pii = pii_map.get(col, [])
        schema[str(col)] = {
            "dtype": dtype,
            "nulos": nulos,
            "cardinalidade": cardinalidade,
            "is_pii_suspeita": col in pii_cols,
            "tipos_pii_detectados": tipos_pii or None,
        }

    return {
        "ok": True,
        "schema": schema,
        "total_linhas": int(len(df)),
        "total_colunas": int(len(df.columns)),
        "amostra_pii_usada": amostra_pii,
        "colunas_pii": sorted(pii_cols),
    }
