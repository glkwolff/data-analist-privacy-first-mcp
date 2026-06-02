"""Tema visual compartilhado pra todos os gráficos do agente.

Existe pra dar consistência estética entre análises e entre sessões/LLMs
diferentes. Não decide TIPO de gráfico — só padroniza visual.

Uso típico no código gerado pelo LLM:

    import plotly.express as px
    from agente_dados_mcp import theme

    fig = px.bar(df_agregado, x='cat', y='valor',
                 color_discrete_sequence=theme.PALETTE)
    theme.apply_layout(fig, titulo='Vendas por região', subtitulo='2024')

Bloco único de responsabilidade: paleta + layout. Sem helpers de chart
type — esses ficam por conta do LLM.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import plotly.graph_objects as go


PALETTE = [
    "#2E86AB",
    "#A23B72",
    "#F18F01",
    "#3B7A57",
    "#6A4C93",
    "#C73E1D",
    "#5B8E7D",
    "#BC4749",
]

PALETTE_SEQUENTIAL = "Viridis"
PALETTE_DIVERGING = "RdBu"

_FONT_FAMILY = "Inter, -apple-system, system-ui, sans-serif"


def apply_layout(
    fig: "go.Figure",
    titulo: str | None = None,
    subtitulo: str | None = None,
    fonte_dados: str | None = None,
) -> "go.Figure":
    """Aplica o layout padrão. Modifica e retorna o fig pra encadear chamadas.

    - titulo: título principal (sobrescreve o que já estiver no fig)
    - subtitulo: linha menor abaixo do título
    - fonte_dados: nota de rodapé tipo 'UCI Adult Income (n=32.561)'
    """
    titulo_html = None
    if titulo is not None:
        if subtitulo:
            titulo_html = (
                f"<b>{titulo}</b><br>"
                f"<span style='font-size:12px;color:#666'>{subtitulo}</span>"
            )
        else:
            titulo_html = f"<b>{titulo}</b>"

    layout_updates: dict = {
        "font": {"family": _FONT_FAMILY, "size": 13, "color": "#222"},
        "plot_bgcolor": "white",
        "paper_bgcolor": "white",
        "margin": {"l": 60, "r": 30, "t": 80 if titulo_html else 40, "b": 80},
        "xaxis": {
            "showgrid": False,
            "showline": True,
            "linecolor": "#cccccc",
            "ticks": "outside",
            "tickcolor": "#cccccc",
        },
        "yaxis": {
            "showgrid": True,
            "gridcolor": "#eeeeee",
            "showline": False,
            "zeroline": False,
        },
        "colorway": PALETTE,
    }
    if titulo_html:
        layout_updates["title"] = {
            "text": titulo_html,
            "x": 0.02,
            "xanchor": "left",
            "font": {"size": 17},
        }

    fig.update_layout(**layout_updates)

    if fonte_dados:
        fig.add_annotation(
            text=f"<i>Fonte: {fonte_dados}</i>",
            xref="paper",
            yref="paper",
            x=0,
            y=-0.18,
            showarrow=False,
            font={"size": 10, "color": "#888"},
            xanchor="left",
        )

    return fig
