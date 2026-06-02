"""Validação de k-anonimidade do `Figure` produzido pelo executor.

Defesa em profundidade contra leak por grupo pequeno (CLAUDE.md §13.5).
A regra de groupby >= 10 já é orientada ao LLM em DESC_EXECUTAR, mas o
LLM pode esquecer, especialmente em filtragens em cadeia. Esta camada
inspeciona o `Figure` ANTES de virar PNG/HTML — se algum grupo aparece
com menos de K indivíduos, retornamos um erro estruturado pro LLM em
vez do gráfico.

O que é, e o que NÃO é, validado:

  Bloqueio estrito (count inequívoco):
    - pie:        cada `values[i]` < K -> falha
    - histogram:  binning dos `x` (np.histogram auto) -> bin count < K -> falha

  Bloqueio condicional:
    - bar:        SOMENTE se todos os y forem inteiros não-negativos
                  (assinatura clássica de value_counts). Bar com média/
                  mediana não dispara (esses agregados são k-anônimos
                  desde que o grupo seja >= K — invariante delegada ao LLM).

  Não validado (cada ponto/segmento é por design 1 indivíduo, sem aglutinação):
    - scatter, box, violin, line, heatmap, table

  Privacy do retorno:
    - Mensagem de erro inclui o RÓTULO do bucket violador, truncado em 40
      chars. Esse rótulo apareceria no gráfico se ele tivesse renderizado,
      então o erro não vaza nada que o sucesso já não vazaria. Limitamos a
      contagem reportada a 10 violadores e indicamos "+N outros" pra
      mensagem caber numa resposta.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import plotly.graph_objects as go


K_PADRAO = 10
MAX_VIOLACOES_REPORTADAS = 10
TAMANHO_MAX_LABEL = 40


def _truncar(rotulo: object, n: int = TAMANHO_MAX_LABEL) -> str:
    txt = str(rotulo)
    return txt if len(txt) <= n else txt[: n - 1] + "…"


def _eh_contagem_inteira(v: object) -> bool:
    """Heurística: o valor parece uma contagem (inteiro não-negativo)?

    Aceita int e float que é exatamente inteiro (1.0, 2.0). Rejeita
    negativos, NaNs e floats com parte fracionária.
    """
    if v is None:
        return False
    try:
        x = float(v)
    except (TypeError, ValueError):
        return False
    if x != x:  # NaN
        return False
    if x < 0:
        return False
    return x == int(x)


def _violacoes_pie(trace: go.Scatter, k: int) -> list[str]:
    labels = list(getattr(trace, "labels", None) or [])
    values = list(getattr(trace, "values", None) or [])
    out: list[str] = []
    for label, val in zip(labels, values, strict=False):
        if val is None:
            continue
        try:
            v = float(val)
        except (TypeError, ValueError):
            continue
        if 0 < v < k:
            out.append(f"pizza: fatia '{_truncar(label)}' com {int(v)} indivíduos (< {k})")
    # Pizza sem labels mas com values (raro) ainda é checada.
    if not labels and values:
        for i, val in enumerate(values):
            try:
                v = float(val)
            except (TypeError, ValueError):
                continue
            if 0 < v < k:
                out.append(f"pizza: fatia #{i} com {int(v)} indivíduos (< {k})")
    return out


def _violacoes_histogram(trace: go.Histogram, k: int) -> list[str]:
    import numpy as np

    raw_x = getattr(trace, "x", None)
    if raw_x is None:
        return []
    valores = np.asarray(list(raw_x))
    if valores.size == 0:
        return []
    # Plotly histogram bin auto: numpy 'auto' é uma aproximação razoável.
    try:
        valores_numericos = valores[~_is_nan_mask(valores)]
        if valores_numericos.size == 0:
            return []
        counts, bordas = np.histogram(valores_numericos, bins="auto")
    except (TypeError, ValueError):
        # Histograma de categóricas — cai no caminho do plotly que faz
        # value_counts internamente. Tratamos como contagem por valor único.
        unique, contagens = np.unique(valores, return_counts=True)
        out = []
        for u, c in zip(unique, contagens, strict=False):
            if 0 < int(c) < k:
                out.append(f"histograma: bucket '{_truncar(u)}' com {int(c)} indivíduos (< {k})")
        return out

    out: list[str] = []
    for i, c in enumerate(counts):
        if 0 < int(c) < k:
            faixa = f"[{bordas[i]:.4g}, {bordas[i + 1]:.4g})"
            out.append(f"histograma: faixa {faixa} com {int(c)} indivíduos (< {k})")
    return out


def _is_nan_mask(arr):
    import numpy as np

    try:
        return np.isnan(arr.astype(float))
    except (TypeError, ValueError):
        return np.zeros(arr.shape, dtype=bool)


def _violacoes_bar(trace: go.Bar, k: int) -> list[str]:
    """Só bloqueia se y parecer claramente contagem (inteiros >= 0)."""
    y_raw = getattr(trace, "y", None)
    if y_raw is None:
        return []
    y_vals = list(y_raw)
    if not y_vals:
        return []
    if not all(_eh_contagem_inteira(v) for v in y_vals):
        # Bar com média / mediana / etc. — fora do escopo desta camada.
        return []
    x_vals = list(getattr(trace, "x", None) or [])
    out: list[str] = []
    for i, y in enumerate(y_vals):
        v = float(y)
        if 0 < v < k:
            rotulo = _truncar(x_vals[i]) if i < len(x_vals) else f"#{i}"
            out.append(f"barras: '{rotulo}' com {int(v)} indivíduos (< {k})")
    return out


def verificar(fig: go.Figure, k: int = K_PADRAO) -> tuple[bool, str]:
    """Retorna (ok, mensagem).

    ok=False => bloquear o retorno do gráfico e devolver mensagem ao LLM.
    Mensagem é segura pra mostrar ao usuário (sem internals do servidor).
    """
    todas: list[str] = []
    if not getattr(fig, "data", None):
        return True, "OK"

    for trace in fig.data:
        tipo = getattr(trace, "type", "") or ""
        if tipo == "pie":
            todas.extend(_violacoes_pie(trace, k))
        elif tipo == "histogram":
            todas.extend(_violacoes_histogram(trace, k))
        elif tipo == "bar":
            todas.extend(_violacoes_bar(trace, k))
        # Demais tipos: cada ponto/segmento já é por construção uma unidade —
        # k-anonymity desse formato fica fora do escopo desta camada e
        # depende do LLM seguir as regras de DESC_EXECUTAR.

    if not todas:
        return True, "OK"

    cabecalho = (
        f"Gráfico BLOQUEADO por k-anonimidade (k={k}).\n"
        f"Algum bucket representa menos de {k} indivíduos — o gráfico, se "
        f"renderizado, identificaria pessoas individualmente.\n\n"
        f"Buckets violadores:"
    )
    primeiros = todas[:MAX_VIOLACOES_REPORTADAS]
    corpo = "\n".join(f"  - {v}" for v in primeiros)
    rodape = ""
    if len(todas) > MAX_VIOLACOES_REPORTADAS:
        rodape = f"\n  ... e mais {len(todas) - MAX_VIOLACOES_REPORTADAS} buckets pequenos."
    sugestao = (
        "\n\nRefaça a análise: (a) agregue em faixas maiores; (b) agrupe "
        "categorias raras em 'outros'; ou (c) filtre o universo antes do "
        "groupby pra subir o tamanho mínimo do grupo."
    )
    return False, f"{cabecalho}\n{corpo}{rodape}{sugestao}"
