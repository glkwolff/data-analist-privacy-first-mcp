#!/usr/bin/env python3
"""Gera o diagrama de arquitetura Privacy-First — tema ESCURO, espacamento amplo.

SVG vetorial + PNG alta resolucao, fundo TRANSPARENTE (encaixa em slide escuro).
Fontes AJUSTADAS POR MEDICAO para nunca vazar das caixas; verificacao final
aborta se algum texto exceder seu container. Layout com bastante respiro.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle

# ---------------------------------------------------------------- paleta (tema escuro)
PANEL_M     = "#13243A"
CARD_M      = "#1B2E47"
BLUE        = "#5FA0DD"
PANEL_C     = "#20262F"
CARD_C      = "#272E38"
CLOUDT      = "#C4CCD6"
CLOUD_BORD  = "#8A95A6"
GREEN       = "#46C285"
GREEN_CARD  = "#143A28"
INK         = "#EAF1F9"
SUB         = "#AEB9C7"
WARN        = "#FF7A8A"
CHIP_FILL   = "#16273C"
CHIP_EDGE   = "#3A5573"
BADGE_RING  = "#0E1726"

plt.rcParams["font.family"] = "DejaVu Sans"

W, H = 1560, 1240
fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
fig.patch.set_alpha(0)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.axis("off")
ax.patch.set_alpha(0)
_R = fig.canvas.get_renderer()
_checks = []


def _w(s, size, weight, style):
    t = ax.text(0, 0, s, fontsize=size, fontweight=weight, fontstyle=style)
    w = t.get_window_extent(renderer=_R).width
    t.remove()
    return w


def fit(s, max_w, base, weight="normal", style="normal", min_size=10):
    size = base
    while size > min_size and _w(s, size, weight, style) > max_w:
        size -= 0.5
    return size


def box(x, y, w, h, *, fc, ec, lw=2.0, rounding=0.02, z=2):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={rounding * min(w, h)}",
        linewidth=lw, edgecolor=ec, facecolor=fc, zorder=z))


def text(x, y, s, *, size, color=INK, weight="normal", ha="center", va="center",
         z=5, style="normal"):
    ax.text(x, y, s, fontsize=size, color=color, fontweight=weight,
            ha=ha, va=va, zorder=z, fontstyle=style)


def fitted(cx, y, s, *, max_w, base, color, weight="bold", style="normal", z=5,
           ha="center", record=None):
    size = fit(s, max_w, base, weight, style)
    ax.text(cx, y, s, fontsize=size, color=color, fontweight=weight, ha=ha,
            va="center", zorder=z, fontstyle=style)
    if record is not None:
        _checks.append((record, _w(s, size, weight, style), max_w))


def chip(x, y, s, *, size=15, color=INK, z=7):
    ax.text(x, y, s, fontsize=size, color=color, fontweight="bold",
            ha="center", va="center", zorder=z,
            bbox=dict(boxstyle="round,pad=0.45", fc=CHIP_FILL, ec=CHIP_EDGE, lw=1.5))


def arrow(p0, p1, *, color, lw=3.2, z=4, rad=0.0):
    ax.add_patch(FancyArrowPatch(
        p0, p1, arrowstyle="-|>", mutation_scale=26,
        linewidth=lw, color=color, zorder=z,
        connectionstyle=f"arc3,rad={rad}", shrinkA=3, shrinkB=3))


def badge(x, y, n, *, color):
    ax.add_patch(Circle((x, y), 19, facecolor=color, edgecolor=BADGE_RING,
                         linewidth=3, zorder=10))
    text(x, y, str(n), size=20, color="#0E1726", weight="bold", z=11)


def annotation(cx, top, lines, *, pad_x=24, line_h=30, pad_y=18):
    widths = [_w(s, sz, "bold", st) for s, sz, st in lines]
    bw = max(widths) + 2 * pad_x
    bh = len(lines) * line_h + 2 * pad_y
    box(cx - bw / 2, top - bh, bw, bh, fc=GREEN_CARD, ec=GREEN, lw=2.0, z=6, rounding=0.05)
    for i, (s, sz, st) in enumerate(lines):
        text(cx, top - pad_y - line_h * (i + 0.5), s, size=sz, color=GREEN,
             weight="bold", style=st, z=7)


# ---------------------------------------------------------------- titulo
fitted(W / 2, 1192, "Arquitetura Privacy-First", max_w=1000, base=40, color=BLUE)
fitted(W / 2, 1142, "O código vai até o dado. O dado nunca sai da máquina.",
       max_w=1100, base=20, color=SUB, weight="normal", style="italic")

# ---------------------------------------------------------------- territorios
T1 = (40, 70, 1060, 1030)
box(*T1, fc=PANEL_M, ec=BLUE, lw=2.4, rounding=0.009, z=1)
text(T1[0] + 32, T1[1] + T1[3] - 38, "MÁQUINA DO USUÁRIO", size=22,
     color=BLUE, weight="bold", ha="left")
text(T1[0] + 32, T1[1] + T1[3] - 66, "tudo roda localmente", size=14,
     color=SUB, ha="left", style="italic")

T2 = (1250, 70, 310, 1030)
box(*T2, fc=PANEL_C, ec=CLOUD_BORD, lw=2.4, rounding=0.009, z=1)
text(T2[0] + T2[2] / 2, T2[1] + T2[3] - 38, "NUVEM (LLM)", size=22,
     color=CLOUDT, weight="bold")

# ---------------------------------------------------------------- fronteira
BX = 1175
ax.add_patch(Rectangle((BX - 20, 90), 40, 935, facecolor=WARN, alpha=0.10, zorder=1))
ax.plot([BX, BX], [95, 1022], color=WARN, lw=3.2, ls=(0, (9, 7)), zorder=3)
text(BX, 1058, "FRONTEIRA", size=15, color=WARN, weight="bold", z=9)
ax.text(BX, 340, "Os dados NUNCA cruzam esta fronteira",
        fontsize=16, color=WARN, fontweight="bold", ha="center", va="center",
        rotation=90, zorder=9,
        bbox=dict(boxstyle="round,pad=0.5", fc=CHIP_FILL, ec=WARN, lw=1.7))

# ---------------------------------------------------------------- MAQUINA: caixas
# CSV
CSV = (95, 865, 205, 150)
box(*CSV, fc=CARD_M, ec=BLUE, lw=2.4, z=3)
gx, gy, gw, gh = CSV[0] + 58, CSV[1] + 84, 90, 38
ax.add_patch(Rectangle((gx, gy), gw, gh, fill=False, edgecolor=BLUE, lw=1.8, zorder=4))
for i in range(1, 3):
    ax.plot([gx, gx + gw], [gy + i * gh / 3, gy + i * gh / 3], color=BLUE, lw=1.1, zorder=4)
for i in range(1, 3):
    ax.plot([gx + i * gw / 3, gx + i * gw / 3], [gy, gy + gh], color=BLUE, lw=1.1, zorder=4)
text(CSV[0] + CSV[2] / 2, CSV[1] + 40, "CSV", size=23, color=BLUE, weight="bold")
text(CSV[0] + CSV[2] / 2, CSV[1] + 17, "arquivo local", size=13, color=SUB)

# MCP Server
MCP = (95, 250, 560, 560)
box(*MCP, fc=CARD_M, ec=BLUE, lw=2.8, z=3)
text(MCP[0] + MCP[2] / 2, MCP[1] + MCP[3] - 34, "MCP Server", size=23,
     color=BLUE, weight="bold")
text(MCP[0] + MCP[2] / 2, MCP[1] + MCP[3] - 60, "agente-dados-mcp", size=14,
     color=SUB, style="italic")

sub_w, sub_h = 232, 132
sx0 = MCP[0] + 25
sx1 = sx0 + sub_w + 46
sy_top = MCP[1] + 216
sy_bot = MCP[1] + 28
subs = [
    ("extrair_schema",  "estrutura do CSV",    sx0, sy_top, BLUE),
    ("detectar_PII",    "regex + nomes susp.", sx1, sy_top, BLUE),
    ("validar_AST",     "bloqueia perigoso",   sx0, sy_bot, GREEN),
    ("executar_codigo", "pandas + plotly",     sx1, sy_bot, BLUE),
]
sub_xy = {}
inner_sub = sub_w - 22
for name, sub, sxx, syy, ec in subs:
    fcl = GREEN_CARD if ec == GREEN else PANEL_M
    box(sxx, syy, sub_w, sub_h, fc=fcl, ec=ec, lw=2.4, z=4)
    fitted(sxx + sub_w / 2, syy + sub_h - 44, name, max_w=inner_sub, base=19,
           color=ec, z=5, record=f"sub:{name}")
    fitted(sxx + sub_w / 2, syy + 34, sub, max_w=inner_sub, base=14,
           color=SUB, weight="normal", z=5, record=f"sub-sub:{name}")
    sub_xy[name] = (sxx, syy, sub_w, sub_h)

# Cliente MCP
CLI = (830, 600, 250, 200)
box(*CLI, fc=CARD_M, ec=BLUE, lw=2.6, z=3)
ci = CLI[2] - 24
fitted(CLI[0] + CLI[2] / 2, CLI[1] + CLI[3] - 46, "Cliente MCP", max_w=ci, base=22,
       color=BLUE, record="Cliente MCP")
fitted(CLI[0] + CLI[2] / 2, CLI[1] + 58, "Claude Code / Cursor /", max_w=ci, base=14,
       color=SUB, weight="normal", record="cli-sub1")
fitted(CLI[0] + CLI[2] / 2, CLI[1] + 33, "Windsurf / Cline ...", max_w=ci, base=14,
       color=SUB, weight="normal", record="cli-sub2")

# Dashboard HTML
DASH = (830, 205, 250, 190)
box(*DASH, fc=CARD_M, ec=BLUE, lw=2.6, z=3)
bx0, by0 = DASH[0] + DASH[2] / 2 - 42, DASH[1] + 100
for i, bh in enumerate([24, 46, 34, 58]):
    ax.add_patch(Rectangle((bx0 + i * 19, by0), 13, bh, facecolor=BLUE,
                           edgecolor="none", zorder=4))
ax.plot([bx0 - 8, bx0 + 84], [by0, by0], color=BLUE, lw=2, zorder=4)
di = DASH[2] - 24
fitted(DASH[0] + DASH[2] / 2, DASH[1] + 46, "Dashboard HTML", max_w=di, base=20,
       color=BLUE, record="Dashboard HTML")
fitted(DASH[0] + DASH[2] / 2, DASH[1] + 22, "PNG inline + interativo", max_w=di,
       base=14, color=SUB, weight="normal", record="dash-sub")

# ---------------------------------------------------------------- NUVEM: LLM
LLM = (1290, 615, 235, 215)
box(*LLM, fc=CARD_C, ec=CLOUD_BORD, lw=2.8, z=3)
text(LLM[0] + LLM[2] / 2, LLM[1] + LLM[3] - 54, "LLM", size=30,
     color=CLOUDT, weight="bold")
text(LLM[0] + LLM[2] / 2, LLM[1] + 60, "Claude / GPT /", size=16, color=SUB)
text(LLM[0] + LLM[2] / 2, LLM[1] + 35, "Gemini", size=16, color=SUB)

# ---------------------------------------------------------------- setas + rotulos
# 1) CSV -> MCP
xm = CSV[0] + CSV[2] / 2
arrow((xm, CSV[1]), (xm, MCP[1] + MCP[3]), color=BLUE)
badge(xm, (CSV[1] + MCP[1] + MCP[3]) / 2, 1, color=BLUE)
chip(xm + 118, (CSV[1] + MCP[1] + MCP[3]) / 2, "carregar\ndataset", color=BLUE)

laneA = (MCP[0] + MCP[2] + CLI[0]) / 2
# 7) MCP -> Dashboard
arrow((MCP[0] + MCP[2], 340), (DASH[0], 320), color=BLUE, rad=0.16)
badge(laneA, 342, 7, color=BLUE)
chip(laneA, 266, "PNG +\nHTML", color=BLUE)
# 5) Cliente MCP -> MCP
arrow((CLI[0], 622), (MCP[0] + MCP[2], 548), color=BLUE, rad=0.22)
badge(laneA, 560, 5, color=BLUE)
chip(laneA, 484, "executar\ncódigo", color=BLUE)
# 2) MCP -> Cliente MCP
arrow((MCP[0] + MCP[2], 612), (CLI[0], 692), color=BLUE, rad=0.22)
badge(laneA, 668, 2, color=BLUE)
chip(laneA, 744, "schema +\ncolunas PII", color=BLUE)

# 3) Cliente MCP -> LLM  (cruza fronteira)
arrow((CLI[0] + CLI[2], 700), (LLM[0], 675), color=CLOUDT, rad=0.16, lw=3.4)
badge(1232, 690, 3, color=CLOUDT)
chip(1236, 766, "schema +\npergunta", color=CLOUDT)
# 4) LLM -> Cliente MCP  (cruza fronteira)
arrow((LLM[0], 628), (CLI[0] + CLI[2], 652), color=CLOUDT, rad=0.16, lw=3.4)
badge(1120, 640, 4, color=CLOUDT)
chip(998, 566, "código Python\ngerado", color=CLOUDT)

# 6) validar_AST interna (self-loop verde)
vx, vy, vw, vh = sub_xy["validar_AST"]
cx = vx + vw / 2
arrow((cx - 52, vy + vh), (cx + 52, vy + vh), color=GREEN, rad=-1.25, lw=3.2)
badge(cx, vy + vh + 40, 6, color=GREEN)

# ---------------------------------------------------------------- anotacoes (verdes, auto-dimensionadas)
annotation(905, 1088, [
    ("Só ESTRUTURA atravessa:", 15, "normal"),
    ("nomes de colunas e tipos.", 15, "normal"),
    ("Nenhum valor real.", 15, "italic"),
])
annotation((95 + 655) / 2, 238, [
    ("Validar AST bloqueia código perigoso:", 15, "normal"),
    ("import os, eval, exec, open, __import__ ...", 14, "italic"),
])

# ---------------------------------------------------------------- legenda (na nuvem)
lx, ly = 1290, 430
text(lx, ly + 56, "Legenda", size=16, color=INK, weight="bold", ha="left")
items = [(BLUE, "Máquina do usuário"), (CLOUDT, "IA / nuvem (LLM)"),
         (GREEN, "Segurança / validação")]
leg_maxw = T2[0] + T2[2] - (lx + 33) - 14
for i, (c, lab) in enumerate(items):
    yy = ly + 8 - i * 40
    ax.add_patch(Rectangle((lx, yy), 22, 17, facecolor=c, edgecolor="none", zorder=5))
    fitted(lx + 33, yy + 8.5, lab, max_w=leg_maxw, base=14, color=INK,
           weight="normal", ha="left")

# ---------------------------------------------------------------- verificacao anti-vazamento
leaks = [(d, tw, aw) for (d, tw, aw) in _checks if tw > aw + 0.5]
if leaks:
    for d, tw, aw in leaks:
        print(f"LEAK {d}: {tw:.0f} > {aw:.0f}")
    raise SystemExit("Texto vazando — abortado.")

# ---------------------------------------------------------------- export
fig.savefig("docs/diagrama_arquitetura.svg", format="svg", transparent=True)
fig.savefig("docs/diagrama_arquitetura.png", format="png", dpi=200, transparent=True)
print("OK — sem vazamentos. Salvo docs/diagrama_arquitetura.svg + .png (3120x2480, transparente)")
