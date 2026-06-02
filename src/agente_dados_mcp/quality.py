"""Análise de qualidade do dataset — nulos, duplicatas, outliers, anomalias.

Por que existe (CLAUDE.md §1 — "diferenciais"):
ser bom analista é saber QUE perguntas fazer ANTES do gráfico. Esta
tool entrega o "checklist do júnior" de graça pro LLM: o que está
faltando, o que repete, o que destoa.

Privacy invariant:
  - Tudo o que sai daqui é contagem ou percentil — nunca o valor que
    causou a anomalia. Quando reportamos "20 outliers em 'idade'",
    NÃO incluímos a lista de idades exatas — só a contagem e o limite
    IQR (que é função dos quartis, agregado seguro).
  - Mesma regra de seleção de colunas do describe.py: respeita
    `colunas_autorizadas`; sem autorização, opera sobre o complemento
    das PII.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pandas as pd


# Limiares — exposto pro LLM relatar de forma transparente.
SKEW_LIMIAR = 2.0  # |skew| > 2 já é "muito assimétrico"
DOMINANCIA_LIMIAR = 0.95  # se uma categoria sozinha tem >= 95%, é quase-constante
CARDINALIDADE_ALTA_FRACAO = 0.5  # >= 50% das linhas distintas = parece ID disfarçado


def _detectar_nulos(df: pd.DataFrame) -> dict[str, dict[str, Any]]:
    total = len(df)
    if total == 0:
        return {}
    out: dict[str, dict[str, Any]] = {}
    for col in df.columns:
        n = int(df[col].isna().sum())
        if n > 0:
            out[str(col)] = {
                "nulos": n,
                "fracao": round(n / total, 4),
            }
    return out


def _detectar_duplicatas(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {"linhas_duplicadas": 0, "fracao": 0.0}
    mask = df.duplicated(keep="first")
    n = int(mask.sum())
    return {
        "linhas_duplicadas": n,
        "fracao": round(n / len(df), 4) if len(df) else 0.0,
    }


def _outliers_iqr(s: pd.Series) -> dict[str, Any] | None:
    """Conta outliers pela regra clássica de Tukey (1.5 * IQR).

    Retorna None pra colunas com menos de 4 valores não-nulos — não dá
    pra confiar nos quartis com tão poucos pontos.
    """
    s_clean = s.dropna()
    if len(s_clean) < 4:
        return None
    q1 = float(s_clean.quantile(0.25))
    q3 = float(s_clean.quantile(0.75))
    iqr = q3 - q1
    if iqr == 0:
        # Variação zero entre Q1 e Q3 — toda detecção viraria ruído.
        return None
    lim_inf = q1 - 1.5 * iqr
    lim_sup = q3 + 1.5 * iqr
    n_out = int(((s_clean < lim_inf) | (s_clean > lim_sup)).sum())
    return {
        "n_outliers": n_out,
        "fracao": round(n_out / len(s_clean), 4),
        "limite_inferior": lim_inf,
        "limite_superior": lim_sup,
        "iqr": iqr,
    }


def _distribuicao_numerica_anomala(s: pd.Series) -> dict[str, Any] | None:
    s_clean = s.dropna()
    if len(s_clean) < 4:
        return None
    achados = []
    if s_clean.nunique() == 1:
        achados.append("constante")
    try:
        skew = float(s_clean.skew())
        if abs(skew) > SKEW_LIMIAR:
            achados.append(f"assimetria_forte (skew={round(skew, 2)})")
    except Exception:
        skew = None
    if not achados:
        return None
    return {"achados": achados, "skew": skew}


def _distribuicao_categorica_anomala(s: pd.Series, total: int) -> dict[str, Any] | None:
    s_clean = s.dropna()
    if s_clean.empty:
        return None
    counts = s_clean.value_counts()
    achados = []
    # Constante / quase-constante: uma categoria domina.
    fracao_top = float(counts.iloc[0]) / float(len(s_clean))
    if counts.shape[0] == 1:
        achados.append("constante")
    elif fracao_top >= DOMINANCIA_LIMIAR:
        achados.append(
            f"quase_constante ({round(fracao_top * 100, 1)}% em uma categoria)"
        )
    # Cardinalidade muito alta — provável identificador, não categoria.
    if counts.shape[0] >= max(50, int(total * CARDINALIDADE_ALTA_FRACAO)):
        achados.append(
            f"cardinalidade_alta ({counts.shape[0]} valores distintos)"
        )
    if not achados:
        return None
    return {"achados": achados}


def _escolher_colunas(
    df: pd.DataFrame,
    colunas_pii: list[str],
    colunas_autorizadas: list[str],
) -> tuple[list[str], list[str]]:
    if colunas_autorizadas:
        return list(colunas_autorizadas), []
    pii_set = set(colunas_pii)
    seguras = [c for c in df.columns if c not in pii_set]
    return seguras, sorted(pii_set)


def analisar(
    df: pd.DataFrame,
    colunas_pii: list[str],
    colunas_autorizadas: list[str],
) -> dict[str, Any]:
    """Retorna o dicionário documentado em DESC_QUALIDADE (prompts.py)."""
    import numpy as np

    total = len(df)
    cols, omitidas = _escolher_colunas(df, colunas_pii, colunas_autorizadas)
    sub = df[cols] if cols else df.iloc[:, :0]
    num_cols = sub.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = [c for c in cols if c not in num_cols]

    outliers = {}
    for col in num_cols:
        info = _outliers_iqr(sub[col])
        if info is not None and info["n_outliers"] > 0:
            outliers[col] = info

    anomalias: dict[str, dict[str, Any]] = {}
    for col in num_cols:
        info = _distribuicao_numerica_anomala(sub[col])
        if info:
            anomalias[col] = info
    for col in cat_cols:
        info = _distribuicao_categorica_anomala(sub[col], total)
        if info:
            anomalias[col] = info

    return {
        "ok": True,
        "total_linhas": total,
        "nulos": _detectar_nulos(sub),
        "duplicatas": _detectar_duplicatas(sub),
        "outliers_iqr": outliers,
        "distribuicoes_anomalas": anomalias,
        "colunas_analisadas": cols,
        "colunas_omitidas_por_pii_nao_autorizada": omitidas,
        "limiares": {
            "skew_forte": SKEW_LIMIAR,
            "dominancia_quase_constante": DOMINANCIA_LIMIAR,
            "fracao_cardinalidade_alta": CARDINALIDADE_ALTA_FRACAO,
        },
    }
