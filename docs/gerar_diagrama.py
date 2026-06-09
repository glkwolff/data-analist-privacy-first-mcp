#!/usr/bin/env python3
"""Gera o diagrama de arquitetura Privacy-First (SVG vetorial + PNG alta resolucao).

Usa apenas matplotlib (sem binarios externos). Layout em territorios separados por
uma fronteira, com setas numeradas, rotulos em "chips" de alto contraste e
anotacoes destacadas. Pensado para leitura em projecao de slide.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle

# ---------------------------------------------------------------- paleta (3 cores principais)
NAVY        = "#1C3A5E"   # MAQUINA DO USUARIO
NAVY_LIGHT  = "#E8EFF7"
CLOUD       = "#4D5663"   # IA / NUVEM
CLOUD_LIGHT = "#ECEEF1"
GREEN       = "#1F7A47"   # SEGURANCA / VALIDACAO
GREEN_LIGHT = "#E1F1E8"
INK         = "#172029"   # texto principal (alto contraste)
SUB         = "#3C434F"   # texto secundario (ainda alto contraste)
WARN        = "#B23A48"   # acento esparso: a fronteira
CHIP_EDGE   = "#C7CDD6"   # borda dos chips de rotulo
WHITE       = "#FFFFFF"

plt.rcParams["font.family"] = "DejaVu Sans"

W, H = 1920, 1080
fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.axis("off")
fig.patch.set_facecolor(WHITE)


def box(x, y, w, h, *, fc, ec, lw=2.0, rounding=0.02, z=2):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={rounding * min(w, h)}",
        linewidth=lw, edgecolor=ec, facecolor=fc, zorder=z))


def text(x, y, s, *, size, color=INK, weight="normal", ha="center", va="center",
         z=5, style="normal"):
    ax.text(x, y, s, fontsize=size, color=color, fontweight=weight,
            ha=ha, va=va, zorder=z, fontstyle=style)


def chip(x, y, s, *, size=16, color=INK, z=7):
    """Rotulo de seta num retangulo branco com borda — separa do fundo e das linhas."""
    ax.text(x, y, s, fontsize=size, color=color, fontweight="bold",
            ha="center", va="center", zorder=z,
            bbox=dict(boxstyle="round,pad=0.4", fc=WHITE, ec=CHIP_EDGE, lw=1.4))


def arrow(p0, p1, *, color, lw=3.4, z=4, rad=0.0, style="-|>"):
    ax.add_patch(FancyArrowPatch(
        p0, p1, arrowstyle=style, mutation_scale=28,
        linewidth=lw, color=color, zorder=z,
        connectionstyle=f"arc3,rad={rad}", shrinkA=3, shrinkB=3))


def badge(x, y, n, *, color):
    ax.add_patch(Circle((x, y), 20, facecolor=color, edgecolor=WHITE,
                         linewidth=3, zorder=10))
    text(x, y, str(n), size=21, color=WHITE, weight="bold", z=11)


# ---------------------------------------------------------------- titulo
text(W / 2, 1032, "Arquitetura Privacy-First", size=44, color=NAVY, weight="bold")
text(W / 2, 982, "O código vai até o dado. O dado nunca sai da máquina.",
     size=23, color=SUB, style="italic")

# ---------------------------------------------------------------- territorios
T1 = (48, 90, 1232, 820)            # MAQUINA DO USUARIO
box(*T1, fc=NAVY_LIGHT, ec=NAVY, lw=3.2, rounding=0.010, z=1)
text(T1[0] + 30, T1[1] + T1[3] - 34, "MÁQUINA DO USUÁRIO", size=25,
     color=NAVY, weight="bold", ha="left")
text(T1[0] + 30, T1[1] + T1[3] - 64, "tudo roda localmente", size=16,
     color=SUB, ha="left", style="italic")

T2 = (1570, 90, 302, 820)           # NUVEM (LLM)
box(*T2, fc=CLOUD_LIGHT, ec=CLOUD, lw=3.2, rounding=0.010, z=1)
text(T2[0] + T2[2] / 2, T2[1] + T2[3] - 34, "NUVEM (LLM)", size=25,
     color=CLOUD, weight="bold")

# ---------------------------------------------------------------- fronteira
BX = 1425
ax.add_patch(Rectangle((BX - 24, 100), 48, 810, facecolor=WARN, alpha=0.06, zorder=1))
ax.plot([BX, BX], [105, 905], color=WARN, lw=3.6, ls=(0, (9, 7)), zorder=3)
text(BX, 878, "FRONTEIRA", size=17, color=WARN, weight="bold", z=9)
ax.text(BX, 345, "Os dados NUNCA cruzam esta fronteira",
        fontsize=21, color=WARN, fontweight="bold", ha="center", va="center",
        rotation=90, zorder=9,
        bbox=dict(boxstyle="round,pad=0.6", fc=WHITE, ec=WARN, lw=1.8))

# ---------------------------------------------------------------- MAQUINA: caixas
# CSV
CSV = (110, 690, 205, 150)
box(*CSV, fc=WHITE, ec=NAVY, lw=2.6, z=3)
gx, gy, gw, gh = CSV[0] + 53, CSV[1] + 82, 100, 42
ax.add_patch(Rectangle((gx, gy), gw, gh, fill=False, edgecolor=NAVY, lw=2, zorder=4))
for i in range(1, 3):
    ax.plot([gx, gx + gw], [gy + i * gh / 3, gy + i * gh / 3], color=NAVY, lw=1.2, zorder=4)
for i in range(1, 3):
    ax.plot([gx + i * gw / 3, gx + i * gw / 3], [gy, gy + gh], color=NAVY, lw=1.2, zorder=4)
text(CSV[0] + CSV[2] / 2, CSV[1] + 40, "CSV", size=25, color=NAVY, weight="bold")
text(CSV[0] + CSV[2] / 2, CSV[1] + 15, "arquivo local", size=15, color=SUB)

# MCP Server (caixa grande)
MCP = (110, 175, 560, 445)
box(*MCP, fc=WHITE, ec=NAVY, lw=3.2, z=3)
text(MCP[0] + MCP[2] / 2, MCP[1] + MCP[3] - 32, "MCP Server", size=26,
     color=NAVY, weight="bold")
text(MCP[0] + MCP[2] / 2, MCP[1] + MCP[3] - 60, "agente-dados-mcp", size=16,
     color=SUB, style="italic")

# sub-componentes 2x2
sub_w, sub_h = 232, 108
sx0 = MCP[0] + 26
sx1 = sx0 + sub_w + 44
sy_top = MCP[1] + 170
sy_bot = MCP[1] + 12
subs = [
    ("extrair_schema",  "estrutura do CSV",    sx0, sy_top, NAVY),
    ("detectar_PII",    "regex + nomes susp.", sx1, sy_top, NAVY),
    ("validar_AST",     "bloqueia perigoso",   sx0, sy_bot, GREEN),
    ("executar_codigo", "pandas + plotly",     sx1, sy_bot, NAVY),
]
sub_xy = {}
for name, sub, sxx, syy, ec in subs:
    fcl = GREEN_LIGHT if ec == GREEN else NAVY_LIGHT
    box(sxx, syy, sub_w, sub_h, fc=fcl, ec=ec, lw=2.6, z=4)
    text(sxx + sub_w / 2, syy + sub_h - 38, name, size=21, color=ec, weight="bold", z=5)
    text(sxx + sub_w / 2, syy + 30, sub, size=15, color=SUB, z=5)
    sub_xy[name] = (sxx, syy, sub_w, sub_h)

# Cliente MCP
CLI = (880, 600, 320, 185)
box(*CLI, fc=WHITE, ec=NAVY, lw=2.8, z=3)
text(CLI[0] + CLI[2] / 2, CLI[1] + CLI[3] - 44, "Cliente MCP", size=24,
     color=NAVY, weight="bold")
text(CLI[0] + CLI[2] / 2, CLI[1] + 54, "Claude Code / Cursor /", size=16, color=SUB)
text(CLI[0] + CLI[2] / 2, CLI[1] + 30, "Windsurf / Cline ...", size=16, color=SUB)

# Dashboard HTML
DASH = (880, 175, 320, 175)
box(*DASH, fc=WHITE, ec=NAVY, lw=2.8, z=3)
bx0, by0 = DASH[0] + 124, DASH[1] + 92
for i, bh in enumerate([26, 50, 36, 62]):
    ax.add_patch(Rectangle((bx0 + i * 20, by0), 14, bh, facecolor=NAVY,
                           edgecolor="none", zorder=4))
ax.plot([bx0 - 8, bx0 + 92], [by0, by0], color=NAVY, lw=2, zorder=4)
text(DASH[0] + DASH[2] / 2, DASH[1] + 42, "Dashboard HTML", size=22,
     color=NAVY, weight="bold")
text(DASH[0] + DASH[2] / 2, DASH[1] + 18, "PNG inline + interativo", size=15, color=SUB)

# ---------------------------------------------------------------- NUVEM: LLM
LLM = (1600, 545, 252, 200)
box(*LLM, fc=WHITE, ec=CLOUD, lw=3.0, z=3)
text(LLM[0] + LLM[2] / 2, LLM[1] + LLM[3] - 50, "LLM", size=32,
     color=CLOUD, weight="bold")
text(LLM[0] + LLM[2] / 2, LLM[1] + 58, "Claude / GPT /", size=18, color=SUB)
text(LLM[0] + LLM[2] / 2, LLM[1] + 33, "Gemini", size=18, color=SUB)

# ---------------------------------------------------------------- setas + rotulos
# 1) CSV -> MCP
xm = CSV[0] + CSV[2] / 2
arrow((xm, CSV[1]), (xm, MCP[1] + MCP[3]), color=NAVY)
badge(xm, (CSV[1] + MCP[1] + MCP[3]) / 2, 1, color=NAVY)
chip(xm + 118, (CSV[1] + MCP[1] + MCP[3]) / 2, "carregar\ndataset", color=NAVY)

# 2) MCP -> Cliente MCP  (lane A, bow up)
arrow((MCP[0] + MCP[2], 600), (CLI[0], 690), color=NAVY, rad=0.22)
badge(775, 662, 2, color=NAVY)
chip(775, 745, "schema +\ncolunas PII", color=NAVY)

# 5) Cliente MCP -> MCP  (lane A, bow down)
arrow((CLI[0], 620), (MCP[0] + MCP[2], 545), color=NAVY, rad=0.22)
badge(775, 560, 5, color=NAVY)
chip(775, 478, "executar\ncódigo", color=NAVY)

# 3) Cliente MCP -> LLM  (lane B, cruza fronteira, bow up)
arrow((CLI[0] + CLI[2], 665), (LLM[0], 640), color=CLOUD, rad=0.16, lw=3.6)
badge(1488, 648, 3, color=CLOUD)
chip(1500, 730, "schema +\npergunta", color=CLOUD)

# 4) LLM -> Cliente MCP  (lane B, cruza fronteira, bow down)
arrow((LLM[0], 590), (CLI[0] + CLI[2], 615), color=CLOUD, rad=0.16, lw=3.6)
badge(1322, 600, 4, color=CLOUD)
chip(1300, 512, "código Python\ngerado", color=CLOUD)

# 6) validacao AST interna (verde, self-loop sobre validar_AST)
vx, vy, vw, vh = sub_xy["validar_AST"]
cx = vx + vw / 2
arrow((cx - 52, vy + vh), (cx + 52, vy + vh), color=GREEN, rad=-1.25, lw=3.4)
badge(cx, vy + vh + 40, 6, color=GREEN)

# 7) MCP -> Dashboard HTML
arrow((MCP[0] + MCP[2], 320), (DASH[0], 300), color=NAVY, rad=0.16)
badge(775, 322, 7, color=NAVY)
chip(775, 250, "PNG +\nHTML", color=NAVY)

# ---------------------------------------------------------------- anotacoes (destaque verde)
# perto da seta 3 (schema saindo) — junto a fronteira
ann1 = (838, 800, 362, 100)
box(*ann1, fc=GREEN_LIGHT, ec=GREEN, lw=2.0, z=6, rounding=0.05)
text(ann1[0] + ann1[2] / 2, ann1[1] + 70, "Só ESTRUTURA atravessa:",
     size=16, color=GREEN, weight="bold", z=7)
text(ann1[0] + ann1[2] / 2, ann1[1] + 46, "nomes de colunas e tipos.",
     size=16, color=GREEN, weight="bold", z=7)
text(ann1[0] + ann1[2] / 2, ann1[1] + 22, "Nenhum valor real.",
     size=16, color=GREEN, weight="bold", z=7, style="italic")

# perto da seta 6 (validacao AST) — abaixo do MCP
ann2 = (110, 100, 560, 64)
box(*ann2, fc=GREEN_LIGHT, ec=GREEN, lw=2.0, z=6, rounding=0.06)
text(ann2[0] + ann2[2] / 2, ann2[1] + 42,
     "Validar AST bloqueia código perigoso:", size=16, color=GREEN, weight="bold", z=7)
text(ann2[0] + ann2[2] / 2, ann2[1] + 19,
     "import os, eval, exec, open, __import__ ...", size=15, color=GREEN,
     weight="bold", z=7, style="italic")

# ---------------------------------------------------------------- legenda (na nuvem, area livre)
lx, ly = 1600, 230
text(lx, ly + 120, "Legenda", size=17, color=INK, weight="bold", ha="left")
items = [(NAVY, "Máquina do usuário"), (CLOUD, "IA / nuvem (LLM)"),
         (GREEN, "Segurança / validação")]
for i, (c, lab) in enumerate(items):
    yy = ly + 80 - i * 38
    ax.add_patch(Rectangle((lx, yy), 26, 20, facecolor=c, edgecolor="none", zorder=5))
    text(lx + 38, yy + 10, lab, size=15, color=INK, ha="left", z=5)

# ---------------------------------------------------------------- export
fig.savefig("docs/diagrama_arquitetura.svg", format="svg")
fig.savefig("docs/diagrama_arquitetura.png", format="png", dpi=200)  # 3840x2160
print("salvo: docs/diagrama_arquitetura.svg (vetorial) + docs/diagrama_arquitetura.png (3840x2160)")
