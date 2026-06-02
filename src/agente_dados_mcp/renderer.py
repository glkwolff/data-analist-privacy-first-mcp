"""Renderização do Plotly Figure: PNG base64 + HTML interativo + resumo markdown.

CLAUDE.md seção 8 — retorno multimodal. Sempre retornamos os três blocos
(image + text + link), graceful degradation se cliente não suportar imagem.
"""

from __future__ import annotations

import base64
import io
import os
import tempfile
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import plotly.graph_objects as go


def fig_para_png_base64(fig: go.Figure, largura: int = 900, altura: int = 600) -> str:
    buffer = io.BytesIO()
    fig.write_image(buffer, format="png", width=largura, height=altura)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def fig_para_html(fig: go.Figure, dir_saida: str | None = None) -> str:
    """Escreve HTML self-contained (Plotly via CDN). Retorna caminho absoluto."""
    if dir_saida is None:
        dir_saida = os.path.join(tempfile.gettempdir(), "agente_dados_mcp")
    os.makedirs(dir_saida, exist_ok=True)
    nome = f"dashboard_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.html"
    caminho = os.path.abspath(os.path.join(dir_saida, nome))
    fig.write_html(caminho, include_plotlyjs="cdn", full_html=True)
    return caminho


def resumo_markdown(fig: go.Figure, descricao: str, max_linhas: int = 10) -> str:
    """Resumo textual compacto do conteúdo do gráfico.

    Tenta extrair dados agregados das traces do fig. NUNCA dumpa o df —
    só usa o que já está no Figure (resultado de agregações).
    """
    linhas: list[str] = [f"**Análise:** {descricao}", ""]

    if not fig.data:
        linhas.append("_Gráfico sem dados._")
        return "\n".join(linhas)

    for i, trace in enumerate(fig.data):
        nome_trace = getattr(trace, "name", None) or f"trace {i}"
        x = getattr(trace, "x", None)
        y = getattr(trace, "y", None)

        if x is None or y is None:
            linhas.append(f"- **{nome_trace}**: ({type(trace).__name__})")
            continue

        try:
            x_list = list(x)[:max_linhas]
            y_list = list(y)[:max_linhas]
        except Exception:
            continue

        linhas.append(f"**{nome_trace}** (primeiros {len(x_list)} pontos):")
        linhas.append("")
        linhas.append("| x | y |")
        linhas.append("|---|---|")
        for xv, yv in zip(x_list, y_list, strict=False):
            linhas.append(f"| {xv} | {yv} |")
        linhas.append("")

    titulo = getattr(fig.layout, "title", None)
    if titulo and getattr(titulo, "text", None):
        linhas.insert(2, f"_Título do gráfico:_ {titulo.text}")
        linhas.insert(3, "")

    return "\n".join(linhas)
