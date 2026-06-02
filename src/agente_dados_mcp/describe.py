"""Estatísticas descritivas das colunas autorizadas, sem gerar código.

Por que existe (CLAUDE.md §1 — "diferenciais arquiteturais"):
analista júnior real começa com `df.describe()` antes de plotar
qualquer coisa. Esta tool dá esse ponto de partida pro LLM resumir em
linguagem natural sem precisar passar pelo `executar_analise` (e portanto
sem AST + render do Plotly) só pra ter um cabeçalho de exploração.

Privacy invariant:
  - Estatísticas numéricas são agregadas — mean, std, percentis — não
    expoem nenhum valor individual.
  - `top_categorias` aplica a regra k-anonymity (§7 item 6): só inclui
    categorias com pelo menos `MIN_K` (=10) ocorrências. Categorias com
    menos de 10 são contadas como "categorias_pequenas".
  - Colunas marcadas como PII na sessão só entram se o usuário tiver
    autorizado explicitamente. Se nenhuma autorização foi feita ainda,
    a tool roda sobre o complemento das PII (modo conservador).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pandas as pd


MIN_K = 10  # mesmo limiar de k-anonymity usado em executar_analise.


def _estatisticas_numericas(s: pd.Series) -> dict[str, Any]:
    s_clean = s.dropna()
    if s_clean.empty:
        return {
            "mean": None, "std": None,
            "min": None, "p25": None, "p50": None, "p75": None, "max": None,
            "nulls": int(s.isna().sum()),
        }
    q = s_clean.quantile([0.25, 0.50, 0.75])
    return {
        "mean": float(s_clean.mean()),
        "std": float(s_clean.std()) if len(s_clean) > 1 else 0.0,
        "min": float(s_clean.min()),
        "p25": float(q.loc[0.25]),
        "p50": float(q.loc[0.50]),
        "p75": float(q.loc[0.75]),
        "max": float(s_clean.max()),
        "nulls": int(s.isna().sum()),
    }


def _estatisticas_categoricas(s: pd.Series, top_n: int = 5) -> dict[str, Any]:
    counts = s.value_counts(dropna=True)
    # k-anonymity: corta categorias pequenas ANTES de pegar o top.
    seguras = counts[counts >= MIN_K]
    top = seguras.head(top_n)
    categorias_pequenas = int((counts < MIN_K).sum())

    return {
        "top_categorias": [[str(idx), int(val)] for idx, val in top.items()],
        "unique": int(counts.shape[0]),
        "nulls": int(s.isna().sum()),
        "categorias_pequenas_omitidas": categorias_pequenas,
        "limiar_k": MIN_K,
    }


def _escolher_colunas(
    df: pd.DataFrame,
    colunas_pii: list[str],
    colunas_autorizadas: list[str],
) -> tuple[list[str], list[str]]:
    """Retorna (cols_a_descrever, cols_omitidas_por_pii_nao_autorizada)."""
    if colunas_autorizadas:
        return list(colunas_autorizadas), []
    # Sem autorização: pega o complemento das PII.
    pii_set = set(colunas_pii)
    seguras = [c for c in df.columns if c not in pii_set]
    return seguras, sorted(pii_set)


def descrever(
    df: pd.DataFrame,
    colunas_pii: list[str],
    colunas_autorizadas: list[str],
) -> dict[str, Any]:
    """Retorna o dicionário documentado em DESC_DESCREVER (prompts.py).

    Decide automaticamente quais colunas tratar como numéricas vs.
    categóricas via `select_dtypes` — datetimes vão como categóricas pra
    não tentar tirar média de timestamp (faz pouco sentido descritivamente).
    """
    import numpy as np

    cols, omitidas = _escolher_colunas(df, colunas_pii, colunas_autorizadas)
    sub = df[cols] if cols else df.iloc[:, :0]

    num_cols = sub.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = [c for c in cols if c not in num_cols]

    numericas = {col: _estatisticas_numericas(sub[col]) for col in num_cols}
    categoricas = {col: _estatisticas_categoricas(sub[col]) for col in cat_cols}

    return {
        "ok": True,
        "numericas": numericas,
        "categoricas": categoricas,
        "colunas_descritas": cols,
        "colunas_omitidas_por_pii_nao_autorizada": omitidas,
        "total_linhas": int(len(df)),
        "limiar_k_anonimidade": MIN_K,
    }
