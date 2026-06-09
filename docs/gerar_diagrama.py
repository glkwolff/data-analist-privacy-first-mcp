#!/usr/bin/env python3
"""Gera o diagrama de arquitetura Privacy-First — tema ESCURO, formato compacto.

SVG vetorial + PNG alta resolucao, fundo TRANSPARENTE (encaixa em slide escuro).
Layout em territorios separados por uma fronteira, setas numeradas, rotulos em
"chips" de alto contraste e anotacoes destacadas.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle

# ---------------------------------------------------------------- paleta (tema escuro)
PANEL_M     = "#13243A"   # painel MAQUINA DO USUARIO
CARD_M      = "#1B2E47"   # cartoes internos da maquina
BLUE        = "#5FA0DD"   # acento maquina (bordas, titulos, setas)
PANEL_C     = "#20262F"   # painel NUVEM
CARD_C      = "#272E38"   # cartao LLM
CLOUDT      = "#C4CCD6"   # acento nuvem (texto/borda)
CLOUD_BORD  = "#8A95A6"
GREEN       = "#46C285"   # seguranca / validacao
GREEN_CARD  = "#143A28"   # fill verde escuro
INK         = "#EAF1F9"   # texto principal (quase branco)
SUB         = "#AEB9C7"   # texto secundario
WARN        = "#FF7A8A"   # acento esparso: a fronteira (coral)
CHIP_FILL   = "#16273C"   # fundo dos chips de rotulo
CHIP_EDGE   = "#3A5573"
BADGE_RING  = "#0E1726"

plt.rcParams["font.family"] = "DejaVu Sans"

W, H = 1480, 1080
fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
fig.patch.set_alpha(0)                      # fundo transparente
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.axis("off")
ax.patch.set_alpha(0)


def box(x, y, w, h, *, fc, ec, lw=2.0, rounding=0.02, z=2):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={rounding * min(w, h)}",
        linewidth=lw, edgecolor=ec, facecolor=fc, zorder=z))


def text(x, y, s, *, size, color=INK, weight="normal", ha="center", va="center",
         z=5, style="normal"):
    ax.text(x, y, s, fontsize=size, color=color, fontweight=weight,
            ha=ha, va=va, zorder=z, fontstyle=style)


def chip(x, y, s, *, size=15, color=INK, z=7, fc=CHIP_FILL, ec=CHIP_EDGE):
    ax.text(x, y, s, fontsize=size, color=color, fontweight="bold",
            ha="center", va="center", zorder=z,
            bbox=dict(boxstyle="round,pad=0.42", fc=fc, ec=ec, lw=1.5))


def arrow(p0, p1, *, color, lw=3.2, z=4, rad=0.0):
    ax.add_patch(FancyArrowPatch(
        p0, p1, arrowstyle="-|>", mutation_scale=26,
        linewidth=lw, color=color, zorder=z,
        connectionstyle=f"arc3,rad={rad}", shrinkA=3, shrinkB=3))


def badge(x, y, n, *, color):
    ax.add_patch(Circle((x, y), 19, facecolor=color, edgecolor=BADGE_RING,
                         linewidth=3, zorder=10))
    text(x, y, str(n), size=20, color="#0E1726", weight="bold", z=11)


# ---------------------------------------------------------------- titulo
text(W / 2, 1035, "Arquitetura Privacy-First", size=40, color=BLUE, weight="bold")
text(W / 2, 989, "O código vai até o dado. O dado nunca sai da máquina.",
     size=21, color=SUB, style="italic")

# ---------------------------------------------------------------- territorios
T1 = (35, 70, 1000, 850)
box(*T1, fc=PANEL_M, ec=BLUE, lw=2.6, rounding=0.010, z=1)
text(T1[0] + 28, T1[1] + T1[3] - 32, "MÁQUINA DO USUÁRIO", size=23,
     color=BLUE, weight="bold", ha="left")
text(T1[0] + 28, T1[1] + T1[3] - 60, "tudo roda localmente", size=15,
     color=SUB, ha="left", style="italic")

T2 = (1175, 70, 270, 850)
box(*T2, fc=PANEL_C, ec=CLOUD_BORD, lw=2.6, rounding=0.010, z=1)
text(T2[0] + T2[2] / 2, T2[1] + T2[3] - 32, "NUVEM (LLM)", size=23,
     color=CLOUDT, weight="bold")

# ---------------------------------------------------------------- fronteira
BX = 1105
ax.add_patch(Rectangle((BX - 22, 80), 44, 830, facecolor=WARN, alpha=0.10, zorder=1))
ax.plot([BX, BX], [85, 910], color=WARN, lw=3.4, ls=(0, (9, 7)), zorder=3)
text(BX, 845, "FRONTEIRA", size=16, color=WARN, weight="bold", z=9)
ax.text(BX, 300, "Os dados NUNCA cruzam esta fronteira",
        fontsize=20, color=WARN, fontweight="bold", ha="center", va="center",
        rotation=90, zorder=9,
        bbox=dict(boxstyle="round,pad=0.6", fc=CHIP_FILL, ec=WARN, lw=1.8))

# ---------------------------------------------------------------- MAQUINA: caixas
# CSV
CSV = (90, 685, 180, 140)
box(*CSV, fc=CARD_M, ec=BLUE, lw=2.4, z=3)
gx, gy, gw, gh = CSV[0] + 48, CSV[1] + 78, 90, 38
ax.add_patch(Rectangle((gx, gy), gw, gh, fill=False, edgecolor=BLUE, lw=1.8, zorder=4))
for i in range(1, 3):
    ax.plot([gx, gx + gw], [gy + i * gh / 3, gy + i * gh / 3], color=BLUE, lw=1.1, zorder=4)
for i in range(1, 3):
    ax.plot([gx + i * gw / 3, gx + i * gw / 3], [gy, gy + gh], color=BLUE, lw=1.1, zorder=4)
text(CSV[0] + CSV[2] / 2, CSV[1] + 38, "CSV", size=24, color=BLUE, weight="bold")
text(CSV[0] + CSV[2] / 2, CSV[1] + 15, "arquivo local", size=14, color=SUB)

# MCP Server
MCP = (90, 165, 520, 455)
box(*MCP, fc=CARD_M, ec=BLUE, lw=2.8, z=3)
text(MCP[0] + MCP[2] / 2, MCP[1] + MCP[3] - 30, "MCP Server", size=24,
     color=BLUE, weight="bold")
text(MCP[0] + MCP[2] / 2, MCP[1] + MCP[3] - 56, "agente-dados-mcp", size=14,
     color=SUB, style="italic")

sub_w, sub_h = 216, 104
sx0 = MCP[0] + 24
sx1 = sx0 + sub_w + 40
sy_top = MCP[1] + 160
sy_bot = MCP[1] + 14
subs = [
    ("extrair_schema",  "estrutura do CSV",    sx0, sy_top, BLUE),
    ("detectar_PII",    "regex + nomes susp.", sx1, sy_top, BLUE),
    ("validar_AST",     "bloqueia perigoso",   sx0, sy_bot, GREEN),
    ("executar_codigo", "pandas + plotly",     sx1, sy_bot, BLUE),
]
sub_xy = {}
for name, sub, sxx, syy, ec in subs:
    fcl = GREEN_CARD if ec == GREEN else PANEL_M
    box(sxx, syy, sub_w, sub_h, fc=fcl, ec=ec, lw=2.4, z=4)
    text(sxx + sub_w / 2, syy + sub_h - 36, name, size=20, color=ec, weight="bold", z=5)
    text(sxx + sub_w / 2, syy + 28, sub, size=14, color=SUB, z=5)
    sub_xy[name] = (sxx, syy, sub_w, sub_h)

# Cliente MCP
CLI = (795, 590, 215, 185)
box(*CLI, fc=CARD_M, ec=BLUE, lw=2.6, z=3)
text(CLI[0] + CLI[2] / 2, CLI[1] + CLI[3] - 40, "Cliente MCP", size=22,
     color=BLUE, weight="bold")
text(CLI[0] + CLI[2] / 2, CLI[1] + 50, "Claude Code / Cursor /", size=14, color=SUB)
text(CLI[0] + CLI[2] / 2, CLI[1] + 28, "Windsurf / Cline ...", size=14, color=SUB)

# Dashboard HTML
DASH = (795, 180, 215, 175)
box(*DASH, fc=CARD_M, ec=BLUE, lw=2.6, z=3)
bx0, by0 = DASH[0] + 72, DASH[1] + 92
for i, bh in enumerate([24, 46, 34, 58]):
    ax.add_patch(Rectangle((bx0 + i * 19, by0), 13, bh, facecolor=BLUE,
                           edgecolor="none", zorder=4))
ax.plot([bx0 - 8, bx0 + 84], [by0, by0], color=BLUE, lw=2, zorder=4)
text(DASH[0] + DASH[2] / 2, DASH[1] + 42, "Dashboard HTML", size=20,
     color=BLUE, weight="bold")
text(DASH[0] + DASH[2] / 2, DASH[1] + 19, "PNG inline + interativo", size=14, color=SUB)

# ---------------------------------------------------------------- NUVEM: LLM
LLM = (1205, 540, 220, 200)
box(*LLM, fc=CARD_C, ec=CLOUD_BORD, lw=2.8, z=3)
text(LLM[0] + LLM[2] / 2, LLM[1] + LLM[3] - 48, "LLM", size=30,
     color=CLOUDT, weight="bold")
text(LLM[0] + LLM[2] / 2, LLM[1] + 56, "Claude / GPT /", size=17, color=SUB)
text(LLM[0] + LLM[2] / 2, LLM[1] + 32, "Gemini", size=17, color=SUB)

# ---------------------------------------------------------------- setas + rotulos
# 1) CSV -> MCP
xm = CSV[0] + CSV[2] / 2
arrow((xm, CSV[1]), (xm, MCP[1] + MCP[3]), color=BLUE)
badge(xm, (CSV[1] + MCP[1] + MCP[3]) / 2, 1, color=BLUE)
chip(xm + 112, (CSV[1] + MCP[1] + MCP[3]) / 2, "carregar\ndataset", color=BLUE)

# 2) MCP -> Cliente MCP  (lane A, bow up)
arrow((MCP[0] + MCP[2], 600), (CLI[0], 680), color=BLUE, rad=0.22)
badge(702, 654, 2, color=BLUE)
chip(702, 730, "schema +\ncolunas PII", color=BLUE)

# 5) Cliente MCP -> MCP  (lane A, bow down)
arrow((CLI[0], 612), (MCP[0] + MCP[2], 545), color=BLUE, rad=0.22)
badge(702, 552, 5, color=BLUE)
chip(702, 478, "executar\ncódigo", color=BLUE)

# 3) Cliente MCP -> LLM  (lane B, cruza fronteira, bow up)
arrow((CLI[0] + CLI[2], 655), (LLM[0], 635), color=CLOUDT, rad=0.16, lw=3.4)
badge(1150, 645, 3, color=CLOUDT)
chip(1152, 718, "schema +\npergunta", color=CLOUDT)

# 4) LLM -> Cliente MCP  (lane B, cruza fronteira, bow down)
arrow((LLM[0], 585), (CLI[0] + CLI[2], 605), color=CLOUDT, rad=0.16, lw=3.4)
badge(1062, 595, 4, color=CLOUDT)
chip(1000, 508, "código Python\ngerado", color=CLOUDT)

# 6) validacao AST interna (verde, self-loop sobre validar_AST)
vx, vy, vw, vh = sub_xy["validar_AST"]
cx = vx + vw / 2
arrow((cx - 50, vy + vh), (cx + 50, vy + vh), color=GREEN, rad=-1.25, lw=3.2)
badge(cx, vy + vh + 38, 6, color=GREEN)

# 7) MCP -> Dashboard HTML
arrow((MCP[0] + MCP[2], 320), (DASH[0], 300), color=BLUE, rad=0.16)
badge(702, 322, 7, color=BLUE)
chip(702, 250, "PNG +\nHTML", color=BLUE)

# ---------------------------------------------------------------- anotacoes (destaque verde)
# perto da seta 3 (schema saindo)
ann1 = (752, 793, 258, 112)
box(*ann1, fc=GREEN_CARD, ec=GREEN, lw=2.0, z=6, rounding=0.05)
text(ann1[0] + ann1[2] / 2, ann1[1] + 82, "Só ESTRUTURA atravessa:",
     size=15, color=GREEN, weight="bold", z=7)
text(ann1[0] + ann1[2] / 2, ann1[1] + 56, "nomes de colunas e tipos.",
     size=15, color=GREEN, weight="bold", z=7)
text(ann1[0] + ann1[2] / 2, ann1[1] + 26, "Nenhum valor real.",
     size=15, color=GREEN, weight="bold", z=7, style="italic")

# perto da seta 6 (validacao AST)
ann2 = (90, 92, 520, 60)
box(*ann2, fc=GREEN_CARD, ec=GREEN, lw=2.0, z=6, rounding=0.06)
text(ann2[0] + ann2[2] / 2, ann2[1] + 39,
     "Validar AST bloqueia código perigoso:", size=15, color=GREEN, weight="bold", z=7)
text(ann2[0] + ann2[2] / 2, ann2[1] + 18,
     "import os, eval, exec, open, __import__ ...", size=14, color=GREEN,
     weight="bold", z=7, style="italic")

# ---------------------------------------------------------------- legenda (na nuvem)
lx, ly = 1205, 360
text(lx, ly + 116, "Legenda", size=16, color=INK, weight="bold", ha="left")
items = [(BLUE, "Máquina do usuário"), (CLOUDT, "IA / nuvem (LLM)"),
         (GREEN, "Segurança / validação")]
for i, (c, lab) in enumerate(items):
    yy = ly + 78 - i * 36
    ax.add_patch(Rectangle((lx, yy), 24, 18, facecolor=c, edgecolor="none", zorder=5))
    text(lx + 36, yy + 9, lab, size=14, color=INK, ha="left", z=5)

# ---------------------------------------------------------------- export
fig.savefig("docs/diagrama_arquitetura.svg", format="svg", transparent=True)
fig.savefig("docs/diagrama_arquitetura.png", format="png", dpi=200, transparent=True)
print("salvo: docs/diagrama_arquitetura.svg + .png (tema escuro, fundo transparente, 2960x2160)")
