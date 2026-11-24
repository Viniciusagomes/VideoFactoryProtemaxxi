"""Gera os cenários 2D (1920x1080, estilo cartoon) da Video Factory Protemaxxi.

Uso:  python ferramentas/gerar_cenarios.py

Saída: cenarios/svg/<slug>.svg e cenarios/folha.html.
Cada cenário tem a linha do chão (CHAO_Y em cenarios.json) onde os pés dos
personagens devem ficar. Os elementos ficam em grupos nomeados (fundo,
moveis, frente) para dar para colocar personagens entre o fundo e a frente.
"""
from __future__ import annotations

import html
import json
import math
import pathlib
import random
import re

RAIZ = pathlib.Path(__file__).resolve().parents[1]
SAIDA = RAIZ / "cenarios" / "svg"
W, H = 1920, 1080

VERDE = "#1FAE5A"
VERDE_CAIXA = "#2E9E50"
AZUL = "#2B7BB9"
MARINHO = "#22374B"


def _d_do_svg(nome: str) -> str:
    texto = (RAIZ / "assets" / "marca" / nome).read_text(encoding="utf-8")
    return re.search(r'\sd="([^"]+)"', texto).group(1)


ICONE_D = _d_do_svg("icone.svg")
LOGO_D = _d_do_svg("logotipo.svg")


# ------------------------------------------------------------------ utilidades
def esc(cor: str, f: float = 0.8) -> str:
    cor = cor.lstrip("#")
    r, g, b = (int(cor[i : i + 2], 16) for i in (0, 2, 4))
    if f <= 1:
        r, g, b = (int(v * f) for v in (r, g, b))
    else:
        r, g, b = (int(v + (255 - v) * (f - 1)) for v in (r, g, b))
    return "#{:02X}{:02X}{:02X}".format(r, g, b)


def R(x, y, w, h, cor, rx=0, linha=None, lw=3, extra=""):
    s = f' stroke="{linha}" stroke-width="{lw}"' if linha else ""
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{cor}"{s} {extra}/>'


def P(d, cor, linha=None, lw=3, extra=""):
    s = f' stroke="{linha}" stroke-width="{lw}"' if linha else ""
    return f'<path d="{d}" fill="{cor}"{s} {extra}/>'


def logo(x, y, w, cor="#FFFFFF", tipo="icone"):
    vb_w, vb_h = (244, 225) if tipo == "icone" else (591, 150)
    return f'<use href="#{tipo}" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{w * vb_h / vb_w:.1f}" fill="{cor}"/>'


def texto(x, y, t, tam=28, cor="#FFF", peso=700, ancora="middle", extra=""):
    return (f'<text x="{x}" y="{y}" font-family="Arial, Helvetica, sans-serif" font-size="{tam}" '
            f'font-weight="{peso}" fill="{cor}" text-anchor="{ancora}" {extra}>{html.escape(t)}</text>')


def caixa(x, y, w, h, cor=VERDE_CAIXA, tipo="gravador"):
    """Caixa de produto: frente colorida, faixa clara em cima e foto do produto."""
    out = [R(x, y, w, h, cor, 2, esc(cor, 0.62), 2)]
    out.append(R(x + 2, y + 2, w - 4, h * 0.16, esc(cor, 1.18)))
    out.append(R(x + w * 0.08, y + h * 0.06, w * 0.34, h * 0.06, "#FFF", 1, extra='opacity="0.9"'))
    if tipo == "gravador":
        out.append(R(x + w * 0.14, y + h * 0.5, w * 0.72, h * 0.22, "#26292D", 3))
        out.append(R(x + w * 0.2, y + h * 0.56, w * 0.2, h * 0.04, "#3E8EDB"))
    elif tipo == "camera":
        cx, cy = x + w * 0.5, y + h * 0.58
        out.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{w * 0.18:.1f}" ry="{h * 0.2:.1f}" fill="#F4F6F8" stroke="#9AA5B1" stroke-width="2"/>')
        out.append(f'<circle cx="{cx:.1f}" cy="{cy + h * 0.06:.1f}" r="{min(w, h) * 0.07:.1f}" fill="#26292D"/>')
    elif tipo == "simples":
        out.append(R(x + w * 0.2, y + h * 0.45, w * 0.6, h * 0.35, esc(cor, 1.3), 3))
    if cor == VERDE_CAIXA:
        dx, dy = x + w * 0.82, y + h * 0.34
        out.append(f'<path d="M{dx:.1f} {dy - 8:.1f} l8 8 l-8 8 l-8 -8 Z" fill="#F2A33A"/>')
    return "".join(out)


def caixa_papelao(x, y, w, h):
    return (R(x, y, w, h, "#C99A64", 2, "#8A6438", 2)
            + R(x + w * 0.42, y, w * 0.16, h, "#D9B07E")
            + R(x + w * 0.1, y + h * 0.55, w * 0.3, h * 0.2, "#F3EBDD", 1))


def spot(x, y, r=10):
    return (f'<ellipse cx="{x}" cy="{y + 40}" rx="{r * 7}" ry="{r * 5}" fill="url(#luz)" opacity="0.5"/>'
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="#2B2B2B"/><circle cx="{x}" cy="{y}" r="{r * 0.55}" fill="#FFF8DC"/>')


def piso(y0, cor="#E8E5E0", linha="#D3CFC8", fuga=(960, 420), passos=7):
    """Piso de porcelanato com perspectiva simples."""
    out = [R(0, y0, W, H - y0, cor)]
    fx, fy = fuga
    for i in range(-14, 15):
        x = 960 + i * 170
        # reta do ponto de fuga até a base
        t0 = (y0 - fy) / (H - fy)
        xa = fx + (x - fx) * t0
        out.append(f'<path d="M{xa:.1f} {y0} L{x:.1f} {H}" stroke="{linha}" stroke-width="2"/>')
    y, dy = y0, 16
    for _ in range(passos):
        y += dy
        dy *= 1.55
        if y > H:
            break
        out.append(f'<path d="M0 {y:.1f} H{W}" stroke="{linha}" stroke-width="2"/>')
    return "".join(out)


def nuvem(x, y, s=1.0):
    c = [(0, 0, 60), (55, -20, 70), (120, 0, 58), (60, 20, 60)]
    return "".join(f'<circle cx="{x + dx * s:.0f}" cy="{y + dy * s:.0f}" r="{r * s:.0f}" fill="#FFF"/>' for dx, dy, r in c)


def planta(x, y, s=1.0, vaso="#E8E2D8"):
    folhas = []
    for i, ang in enumerate((-60, -35, -12, 12, 35, 60, -80, 80)):
        a = math.radians(ang - 90)
        L = (90 if i < 6 else 60) * s
        ex, ey = x + math.cos(a) * L, y + math.sin(a) * L
        folhas.append(f'<path d="M{x:.0f} {y:.0f} Q{(x + ex) / 2 - 14 * s:.0f} {(y + ey) / 2:.0f} {ex:.0f} {ey:.0f} '
                      f'Q{(x + ex) / 2 + 14 * s:.0f} {(y + ey) / 2:.0f} {x:.0f} {y:.0f} Z" fill="{"#3E9B57" if i % 2 else "#2F8546"}"/>')
    return "".join(folhas) + P(f"M{x - 34 * s:.0f} {y:.0f} H{x + 34 * s:.0f} L{x + 26 * s:.0f} {y + 60 * s:.0f} H{x - 26 * s:.0f} Z", vaso, esc(vaso, 0.7), 2)


def camera_bullet(x, y, s=1.0, cor="#F4F6F8", led=False):
    """Câmera bullet de parede, apontando para a esquerda."""
    return (R(x, y - 6 * s, 14 * s, 40 * s, "#DADFE4", 3, "#9AA5B1", 2)
            + P(f"M{x + 6 * s:.0f} {y + 10 * s:.0f} L{x - 20 * s:.0f} {y + 6 * s:.0f}", "none", "#9AA5B1", 8 * s)
            + R(x - 90 * s, y - 14 * s, 80 * s, 34 * s, cor, 12 * s, "#9AA5B1", 2)
            + R(x - 96 * s, y - 18 * s, 30 * s, 42 * s, "#26292D", 8 * s)
            + f'<circle cx="{x - 84 * s:.0f}" cy="{y + 3 * s:.0f}" r="{9 * s:.0f}" fill="#4A6FA5"/>'
            + (f'<circle cx="{x - 30 * s:.0f}" cy="{y + 3 * s:.0f}" r="{4 * s:.0f}" fill="#3E8EFF"/>' if led else ""))


def camera_dome(x, y, s=1.0):
    return (f'<ellipse cx="{x}" cy="{y}" rx="{34 * s}" ry="{10 * s}" fill="#E9EDF1" stroke="#9AA5B1" stroke-width="2"/>'
            f'<path d="M{x - 26 * s} {y} A{26 * s} {24 * s} 0 0 0 {x + 26 * s} {y} Z" fill="#2E3238" opacity="0.85"/>'
            f'<circle cx="{x}" cy="{y + 12 * s}" r="{6 * s}" fill="#4A6FA5"/>')


def tela_cameras(x, y, w, h, moldura="#1C1E21"):
    """Monitor com mosaico de 4 câmeras."""
    out = [R(x, y, w, h, moldura, 8)]
    ix, iy, iw, ih = x + 10, y + 10, w - 20, h - 20
    cores = (("#8FA3B8", "#C8B79A"), ("#7E9A84", "#D9D2C4"), ("#A0A8B2", "#6B5B4A"), ("#9DB4C8", "#E2D9CC"))
    for k, (c1, c2) in enumerate(cores):
        qx = ix + (k % 2) * iw / 2
        qy = iy + (k // 2) * ih / 2
        out.append(R(qx + 2, qy + 2, iw / 2 - 4, ih / 2 - 4, c1))
        out.append(R(qx + 2, qy + ih / 4, iw / 2 - 4, ih / 4 - 2, c2))
        out.append(R(qx + iw / 8, qy + ih / 10, iw / 10, ih / 3, esc(c1, 0.7)))
        out.append(R(qx + 8, qy + 8, 26, 8, "#FF4D4D", 2))
    return "".join(out)


def svg(slug, titulo, camadas, defs=""):
    corpo = "\n".join(camadas)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<title>{titulo}</title>
<defs>
<symbol id="icone" viewBox="0 0 244 225"><path fill-rule="evenodd" clip-rule="evenodd" d="{ICONE_D}"/></symbol>
<symbol id="logotipo" viewBox="0 0 591 150"><path fill-rule="evenodd" clip-rule="evenodd" d="{LOGO_D}"/></symbol>
<radialGradient id="luz"><stop offset="0" stop-color="#FFF6D8"/><stop offset="1" stop-color="#FFF6D8" stop-opacity="0"/></radialGradient>
<linearGradient id="ceu" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4E9BE0"/><stop offset="1" stop-color="#BFE0F7"/></linearGradient>
<linearGradient id="vidro" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#D8EEF8" stop-opacity="0.55"/><stop offset="1" stop-color="#A8CFE6" stop-opacity="0.35"/></linearGradient>
{defs}
</defs>
<g id="{slug}" stroke-linejoin="round" stroke-linecap="round">
{corpo}
</g>
</svg>
"""


# ------------------------------------------------------------------ cenários
def loja_interior():
    random.seed(1)
    c = ['<g id="fundo">']
    c.append(R(0, 0, W, H, "#F4F2EE"))
    # teto com sanca e fita de LED
    c.append(R(0, 0, W, 70, "#FFFFFF"))
    c.append(P("M120 70 L1800 70", "none", "#FFF3C4", 8))
    for x in (300, 700, 1220, 1620):
        c.append(spot(x, 40, 9))
    # estante branca de fundo: parte de cima branca, parte de baixo nichos pretos
    x0, x1 = 60, 1860
    c.append(R(x0, 90, x1 - x0, 380, "#FFFFFF", 0, "#E2DED6", 3))
    c.append(R(x0, 470, x1 - x0, 300, "#1E1F22"))
    tipos = ("gravador", "gravador", "camera", "gravador", "simples")
    for linha, (ytopo, alt) in enumerate(((100, 110), (230, 110), (360, 100))):
        x = x0 + 14
        while x < x1 - 120:
            w = random.choice((110, 130, 150))
            hh = alt - random.choice((0, 10, 20))
            cor = random.choice((VERDE_CAIXA, VERDE_CAIXA, VERDE_CAIXA, "#F4F6F8", "#2E9E50"))
            tipo = random.choice(tipos)
            if random.random() < 0.12:
                c.append(caixa_papelao(x, ytopo + (alt - hh), w, hh))
            else:
                c.append(caixa(x, ytopo + (alt - hh), w, hh, cor, tipo))
            x += w + random.choice((6, 10, 24))
    for y in (220, 350, 470):
        c.append(R(x0, y, x1 - x0, 12, "#FFFFFF", 0, "#E2DED6", 2))
    for x in range(x0, x1 + 1, 360):
        c.append(R(x - 6, 90, 12, 680, "#FFFFFF", 0, "#E2DED6", 2))
    # nichos pretos com caixinhas
    for linha, y in enumerate((500, 640)):
        x = x0 + 30
        while x < x1 - 80:
            w = random.choice((40, 50, 60))
            hh = random.choice((50, 60, 70))
            cor = random.choice((VERDE_CAIXA, "#F4F6F8", "#C99A64", VERDE_CAIXA))
            c.append(caixa(x, y + 90 - hh, w, hh, cor, "simples"))
            x += w + random.choice((4, 8, 30))
        c.append(R(x0, y + 90, x1 - x0, 10, "#FFFFFF"))
    c.append("</g>")
    # balcão de madeira ripada
    c.append('<g id="moveis">')
    c.append(R(360, 640, 1200, 30, "#1B1C1E", 4))
    c.append(R(380, 670, 1160, 230, "#6B4A35"))
    for x in range(392, 1540, 22):
        c.append(R(x, 670, 10, 230, "#7E5A42"))
    c.append(R(380, 670, 1160, 14, "#000", 0, extra='opacity="0.18"'))
    # notebooks e impressora no balcão
    for x in (620, 1060):
        c.append(P(f"M{x} 640 L{x + 20} 560 H{x + 160} L{x + 180} 640 Z", "#2A2C30"))
        c.append(R(x + 40, 572, 120, 56, "#3A4A5E"))
        c.append(logo(x + 84, 582, 30, "#9FD3F5"))
    c.append(R(1330, 590, 110, 50, "#E9ECEF", 6, "#B9C0C7", 2))
    c.append("</g>")
    c.append('<g id="chao">' + piso(900) + "</g>")
    # expositor de vidro na frente, à esquerda
    c.append('<g id="frente">')
    c.append(R(40, 760, 260, 300, "url(#vidro)", 4, "#C9D6DF", 3))
    for y in (840, 930):
        c.append(R(40, y, 260, 6, "#DDE5EA"))
    for i, (x, y) in enumerate(((60, 790), (130, 790), (200, 800), (60, 880), (150, 875), (230, 880), (70, 970), (170, 965))):
        c.append(caixa(x, y, 60, 48 if i % 2 else 56, (VERDE_CAIXA, "#F4F6F8", "#3E7CC0")[i % 3], "simples"))
    c.append(R(40, 1040, 260, 20, "#F4F6F8", 3, "#C9D6DF", 2))
    c.append("</g>")
    return svg("loja-interior", "Loja Protemaxxi — interior e balcão", c)


def loja_painel():
    c = ['<g id="fundo">', R(0, 0, W, H, "#F1EBDD")]
    # ar-condicionado
    c.append(R(760, 60, 400, 110, "#F7F7F5", 18, "#D0CEC8", 3) + R(800, 140, 320, 10, "#C9C7C1", 4))
    # painel de madeira ripada
    c.append(R(300, 220, 1320, 560, "#5A3B28", 6))
    for x in range(312, 1610, 20):
        c.append(R(x, 220, 9, 560, "#6E4A33"))
    c.append(R(290, 206, 1340, 22, "#4A2F20", 4))
    # alarmes e sensores na linha de cima
    for i, x in enumerate((380, 520, 640)):
        c.append(R(x, 260, 90 if i == 0 else 70, 110 if i == 0 else 70, "#F6F7F8", 10, "#B9C0C7", 2))
    for x in (790, 880):
        c.append(R(x, 255, 40, 70, "#F6F7F8", 14, "#B9C0C7", 2) + f'<circle cx="{x + 20}" cy="282" r="12" fill="#E3E7EB"/>')
    c.append(R(970, 270, 16, 34, "#F6F7F8", 4, "#B9C0C7", 2) + R(990, 270, 10, 34, "#F6F7F8", 4, "#B9C0C7", 2))
    # caixas metálicas à direita
    c.append(R(1340, 250, 230, 140, "#2A2C30", 8) + R(1380, 280, 120, 40, "#3E4247", 4))
    c.append(R(1370, 410, 170, 190, "#2E3034", 6))
    # câmeras bullet em duas fileiras
    for fila, y in enumerate((430, 530)):
        for k in range(4 if fila == 0 else 4):
            c.append(camera_bullet(500 + k * 150, y, 1.0, "#F4F6F8" if (k + fila) % 2 == 0 else "#2A2C30", led=(fila == 0 and k == 2)))
    # interfone, vídeo porteiro e controle de acesso
    c.append(R(920, 610, 150, 100, "#F6F7F8", 10, "#B9C0C7", 2) + R(934, 624, 100, 70, "#1E2933", 4))
    c.append(R(1110, 600, 56, 100, "#26292D", 12) + f'<circle cx="1138" cy="630" r="12" fill="#3E4247"/>')
    # gravadores e switch
    c.append(R(380, 640, 140, 110, "#1E1F22", 6) + R(560, 640, 140, 110, "#1E1F22", 6))
    c.append(R(400, 600, 100, 30, "#2A2C30", 4))
    # monitor com câmeras
    c.append(tela_cameras(1220, 610, 330, 190))
    c.append("</g>")
    # bancada branca com produtos
    c.append('<g id="moveis">')
    c.append(R(250, 800, 1420, 26, "#FFFFFF", 6, "#DCD6CA", 2))
    c.append(R(270, 826, 1380, 150, "#FFFFFF", 0, "#DCD6CA", 2))
    c.append(R(300, 840, 1320, 120, "#1E1F22"))
    for x, w, cor in ((320, 90, "#F4F6F8"), (420, 120, "#C0392B"), (560, 260, "#2F6DB5"), (840, 260, "#2F6DB5"), (1120, 140, "#2A2C30"), (1280, 120, VERDE_CAIXA), (1420, 180, "#2A2C30")):
        c.append(caixa(x, 870, w - 10, 90, cor, "gravador" if w > 200 else "simples"))
    c.append("</g>")
    c.append('<g id="chao">' + piso(976, "#E9E6E1") + "</g>")
    return svg("loja-painel", "Loja Protemaxxi — painel de demonstração", c)


def estoque_expedicao():
    c = ['<g id="fundo">', R(0, 0, W, H, "#3E4247")]
    # teto metálico
    c.append(R(0, 0, W, 130, "#C9CDD2"))
    for x in range(0, W, 160):
        c.append(R(x, 0, 14, 130, "#AEB4BA"))
    c.append(R(0, 120, W, 16, "#9AA1A8"))
    c.append(R(700, 60, 520, 14, "#F4F6F8", 7) + f'<ellipse cx="960" cy="140" rx="380" ry="80" fill="url(#luz)" opacity="0.4"/>')
    # paredes de painel cinza escuro
    c.append(R(260, 150, 1400, 620, "#4A4F56", 0, "#3A3E44", 3))
    for x in range(260, 1660, 280):
        c.append(R(x, 150, 4, 620, "#3A3E44"))
    # relógio digital vermelho e TV
    c.append(R(560, 190, 170, 80, "#151515", 6) + texto(645, 248, "11:35", 46, "#FF3B30", 700))
    c.append(R(760, 180, 520, 300, "#111214", 8, "#2A2C30", 4) + R(776, 196, 488, 268, "#1B2430"))
    c.append(logo(940, 260, 150, "#2A3A4D"))
    # prateleira com miudezas
    c.append(R(820, 540, 400, 12, "#F2F2F2") + R(840, 552, 8, 30, "#DADADA") + R(1190, 552, 8, 30, "#DADADA"))
    c.append(R(860, 500, 40, 40, "#2A2C30", 4) + R(920, 490, 60, 50, "#C99A64", 3) + R(1000, 505, 30, 35, "#9AA5B1", 4) + R(1060, 495, 50, 45, "#1E1F22", 4) + R(1140, 505, 34, 35, "#F4F6F8", 4))
    # expositor de ferramentas à esquerda
    c.append(R(300, 400, 190, 240, "#2A2C30", 6))
    for y in (430, 500, 570):
        for k in range(5):
            c.append(R(312 + k * 34, y, 24, 50, "#F2C230", 4, "#8A6A10", 2))
    # estantes de aço com caixas nas laterais
    for xe in (20, 1680):
        c.append(R(xe, 160, 220, 760, "#7D858E", 4))
        for y in (300, 470, 640, 810):
            c.append(R(xe, y, 220, 12, "#A7AFB8"))
            x = xe + 10
            while x < xe + 200:
                w = 60 if (x // 10) % 2 else 80
                c.append(caixa_papelao(x, y - 90, w - 6, 90) if (x // 7) % 3 else caixa(x, y - 90, w - 6, 90, VERDE_CAIXA, "simples"))
                x += w
    c.append("</g>")
    # bancada de expedição cinza com fitas amarelas
    c.append('<g id="moveis">')
    c.append(P("M420 700 H1500 L1640 900 H280 Z", "#7B7F84", "#55595E", 3))
    c.append(P("M960 700 L960 900", "none", "#F2C230", 14) + P("M350 800 H1570", "none", "#F2C230", 14))
    c.append(R(280, 900, 1360, 40, "#6A6E73", 0, "#55595E", 3))
    c.append(R(300, 940, 1320, 140, "#2E3134"))
    for x in (420, 760, 1100, 1400):
        c.append(f'<ellipse cx="{x}" cy="1010" rx="110" ry="60" fill="#E6E9EC" stroke="#B9C0C7" stroke-width="3"/><ellipse cx="{x}" cy="1010" rx="40" ry="22" fill="#9AA5B1"/>')
    # objetos na bancada
    c.append(R(600, 640, 70, 60, "#2A2C30", 6) + R(612, 610, 46, 30, "#3A3E44", 4))
    c.append(R(820, 610, 34, 90, "#1E5FB8", 10) + R(826, 596, 22, 18, "#F4F6F8", 4))
    c.append(R(700, 690, 60, 18, "#E07A1A", 6))
    c.append(R(1050, 650, 140, 50, "#26292D", 4) + R(1060, 640, 60, 20, "#F4F6F8", 4))
    c.append(R(1250, 680, 120, 70, "#C99A64", 3, "#8A6438", 2))
    c.append(R(1390, 730, 150, 110, "#26292D", 4, "#111", 2) + R(1400, 700, 90, 50, "#C99A64", 3, "#8A6438", 2))
    c.append(P("M520 760 l70 -8", "none", "#111", 7))
    c.append("</g>")
    c.append('<g id="chao">' + R(0, 940, W, 140, "#3A3D41") + "</g>")
    return svg("estoque-expedicao", "Estoque e expedição", c)


def fachada():
    c = ['<g id="fundo">', R(0, 0, W, 720, "url(#ceu)")]
    for x, y, s in ((140, 120, 1.1), (520, 70, 0.9), (1180, 110, 1.3), (1640, 60, 0.9), (1720, 300, 1.0)):
        c.append(nuvem(x, y, s))
    # muros vizinhos
    c.append(R(0, 360, 330, 420, "#A9ADB1") + R(1600, 420, 320, 360, "#B9A898"))
    for y in range(440, 780, 34):
        c.append(P(f"M1600 {y} H1920", "none", "#A49383", 2))
    # postes e fios
    c.append(R(60, 200, 22, 600, "#8F949A") + R(1720, 200, 22, 600, "#8F949A"))
    c.append(P("M70 230 Q960 330 1730 230 M70 260 Q960 380 1730 260", "none", "#2A2C30", 3))
    # prédio
    c.append(R(380, 240, 1180, 540, "#3A3D42"))
    c.append(R(360, 180, 1220, 160, "#1E9E52"))
    c.append(R(360, 180, 1220, 14, "#26B862"))
    c.append(logo(430, 205, 470, "#F4F6F8", "logotipo"))
    c.append(P("M1260 270 H1530", "none", "#E8F5EC", 3))
    c.append(texto(1395, 255, "Revenda autorizada", 30, "#F4F6F8", 600))
    c.append(texto(1395, 312, "Segurança eletrônica", 36, "#FFFFFF", 700))
    for k in range(6):
        c.append(R(520 + k * 80, 380, 40, 110, "#D9E6EF", 2, "#2A2C30", 4))
    for x in (500, 790):
        c.append(R(x, 560, 200, 110, "#2E3135", 2))
        for gx in range(x + 14, x + 200, 24):
            c.append(R(gx, 560, 6, 110, "#1E2023"))
    # porta de vidro com produtos ao fundo
    c.append(R(1080, 400, 320, 380, "#1E2124", 2, "#111", 6))
    c.append(R(1094, 470, 292, 310, "#2C3A45"))
    for y in (520, 600, 680):
        c.append(R(1100, y, 280, 8, "#556673"))
        for k in range(6):
            c.append(R(1106 + k * 46, y - 34, 38, 34, VERDE_CAIXA if (k + y) % 3 else "#E9ECEF", 2))
    c.append(R(1094, 470, 292, 310, "url(#vidro)"))
    c.append(texto(1240, 452, "ENTRE, AQUI VOCÊ É BEM-VINDO!", 20, "#FFFFFF", 700))
    c.append(R(1450, 640, 70, 140, "#2A2C30", 2))
    # banners laterais
    for x, ang in ((200, -4), (1610, 4)):
        c.append(f'<g transform="rotate({ang} {x + 75} 560)">' + R(x, 400, 150, 330, "#1FAE5A", 6, "#178B47", 3)
                 + R(x + 12, 420, 126, 40, "#FFFFFF", 4) + texto(x + 75, 448, "CÂMERAS", 20, "#178B47")
                 + texto(x + 75, 500, "A SEGURANÇA", 18) + texto(x + 75, 524, "DO FUTURO", 18)
                 + R(x + 30, 550, 90, 90, "#F4F6F8", 45) + f'<circle cx="{x + 75}" cy="595" r="22" fill="#26292D"/>'
                 + R(x + 14, 666, 122, 40, "#11202F", 4) + texto(x + 75, 693, "ENTRE E TESTE", 16) + "</g>")
    # câmeras na fachada
    c.append(camera_bullet(500, 380, 0.7) + camera_bullet(1060, 380, 0.7))
    c.append("</g>")
    # estacionamento de bloquetes com faixas amarelas
    c.append('<g id="chao">')
    c.append(R(0, 780, W, 300, "#9C9690"))
    for y in range(790, 1080, 26):
        off = 0 if (y // 26) % 2 else 22
        for x in range(-40 + off, W, 44):
            c.append(R(x, y, 40, 22, "#A8A29B", 3))
    for x in (520, 860, 1200, 1540):
        c.append(P(f"M{x} 790 L{x - 60} 1000", "none", "#F2C230", 12))
    c.append(R(0, 1040, W, 40, "#7E7974"))
    c.append("</g>")
    c.append('<g id="frente">' + R(1180, 690, 22, 120, "#F2C230", 6) + R(1300, 690, 22, 120, "#F2C230", 6) + "</g>")
    return svg("fachada", "Fachada da loja Protemaxxi", c)


def casa_fernanda():
    c = ['<g id="fundo">', R(0, 0, W, H, "#DCE7E3")]
    # janela grande com vista da cidade
    c.append(R(1160, 120, 620, 560, "#F7FAF9", 8, "#C9D6D1", 6))
    c.append(R(1180, 140, 580, 520, "url(#ceu)"))
    for x, h in ((1200, 220), (1270, 320), (1350, 260), (1430, 380), (1520, 240), (1590, 340), (1680, 280)):
        c.append(R(x, 660 - h, 70, h, "#8FA9BF"))
        for wy in range(660 - h + 20, 650, 40):
            c.append(R(x + 14, wy, 14, 18, "#C9D9E6") + R(x + 40, wy, 14, 18, "#C9D9E6"))
    c.append(R(1466, 140, 8, 520, "#F7FAF9"))
    c.append(R(1140, 680, 660, 24, "#F7FAF9", 4, "#C9D6D1", 3))
    # prateleira com câmera wi-fi e livros
    c.append(R(260, 300, 420, 16, "#C79A6A", 4))
    c.append(R(290, 230, 26, 70, "#E76F51", 2) + R(320, 240, 22, 60, "#2A9D8F", 2) + R(346, 226, 24, 74, "#F4B942", 2))
    c.append(R(560, 250, 56, 50, "#FFFFFF", 18, "#B9C0C7", 2) + f'<circle cx="588" cy="272" r="12" fill="#26292D"/><circle cx="588" cy="272" r="5" fill="#4A6FA5"/>')
    c.append(planta(440, 300, 0.55))
    # quadro
    c.append(R(760, 180, 240, 170, "#FFFFFF", 4, "#C79A6A", 8) + P("M780 330 L860 240 L920 300 L960 260 L980 330 Z", "#2A9D8F") + f'<circle cx="940" cy="220" r="18" fill="#F4B942"/>')
    c.append("</g>")
    c.append('<g id="moveis">')
    # rack com TV
    c.append(R(200, 420, 560, 320, "#1C1E21", 10) + R(214, 434, 532, 292, "#2B3440"))
    c.append(logo(430, 520, 110, "#3E4E62"))
    c.append(R(160, 760, 640, 120, "#D9B98E", 8, "#B08A5C", 3) + R(180, 790, 180, 70, "#C9A777", 4) + R(380, 790, 180, 70, "#C9A777", 4) + R(580, 790, 200, 70, "#C9A777", 4))
    # sofá
    c.append(R(980, 640, 760, 140, "#8B98A6", 30, "#6C7886", 3))
    c.append(R(940, 700, 90, 200, "#7C8997", 30, "#6C7886", 3) + R(1690, 700, 90, 200, "#7C8997", 30, "#6C7886", 3))
    c.append(R(1010, 760, 700, 120, "#9AA7B5", 24, "#6C7886", 3))
    c.append(R(1060, 650, 160, 120, "#F4B942", 30) + R(1500, 650, 160, 120, "#2A9D8F", 30))
    c.append(planta(1840, 800, 1.2, "#F7FAF9"))
    c.append("</g>")
    c.append('<g id="chao">' + R(0, 880, W, 200, "#C79A6A"))
    for y in (920, 980, 1050):
        c.append(P(f"M0 {y} H{W}", "none", "#B5875A", 3))
    c.append(f'<ellipse cx="1000" cy="990" rx="560" ry="60" fill="#EFE6DA"/>' + "</g>")
    return svg("casa-fernanda", "Casa da Fernanda — sala", c)


def casa_antonio():
    defs = ('<pattern id="papel" width="60" height="60" patternUnits="userSpaceOnUse"><rect width="60" height="60" fill="#EADBC0"/>'
            '<circle cx="30" cy="30" r="6" fill="#DCC7A4"/><circle cx="0" cy="0" r="4" fill="#DCC7A4"/><circle cx="60" cy="60" r="4" fill="#DCC7A4"/></pattern>')
    c = ['<g id="fundo">', R(0, 0, W, H, "url(#papel)")]
    c.append(R(0, 640, W, 240, "#B98B5E") + R(0, 630, W, 14, "#8E6440"))
    # janela com cortina
    c.append(R(1240, 140, 420, 360, "url(#ceu)", 4, "#8E6440", 12) + R(1446, 140, 10, 360, "#8E6440"))
    c.append(P("M1200 110 Q1250 330 1210 560 H1300 Q1280 330 1320 110 Z", "#B5413A") + P("M1700 110 Q1650 330 1690 560 H1600 Q1620 330 1580 110 Z", "#B5413A"))
    c.append(R(1180, 96, 540, 18, "#6B4A35", 6))
    # quadro, relógio e câmera dome no canto
    c.append(R(380, 170, 300, 210, "#F2EAD8", 4, "#8E6440", 12) + P("M400 360 Q470 250 540 320 Q600 260 660 360 Z", "#7E9A84") + f'<circle cx="610" cy="220" r="22" fill="#F2C230"/>')
    c.append(f'<circle cx="900" cy="230" r="60" fill="#FBF7EE" stroke="#6B4A35" stroke-width="8"/>' + P("M900 230 V190 M900 230 H930", "none", "#2A2C30", 6))
    c.append(camera_dome(1880, 70, 1.1))
    c.append("</g>")
    c.append('<g id="moveis">')
    # rack de madeira com TV antiga
    c.append(R(220, 600, 520, 260, "#7A5236", 6, "#5A3B26", 3) + R(250, 640, 210, 180, "#6A4630", 4) + R(500, 640, 210, 180, "#6A4630", 4))
    c.append(R(260, 380, 420, 230, "#3A3A3A", 20) + R(290, 405, 300, 180, "#55636E", 12) + f'<circle cx="630" cy="450" r="14" fill="#777"/><circle cx="630" cy="500" r="14" fill="#777"/>')
    # poltrona e mesinha com rádio
    c.append(R(1220, 620, 360, 230, "#8C4A2F", 40, "#6A3420", 3) + R(1180, 700, 90, 200, "#7A3F27", 30, "#6A3420", 3) + R(1530, 700, 90, 200, "#7A3F27", 30, "#6A3420", 3))
    c.append(R(1250, 760, 300, 110, "#9C5639", 26, "#6A3420", 3))
    c.append(R(1680, 720, 160, 20, "#6B4A35", 4) + R(1700, 740, 14, 140, "#6B4A35") + R(1806, 740, 14, 140, "#6B4A35"))
    c.append(R(1700, 660, 120, 60, "#C9A777", 10, "#8E6440", 3) + f'<circle cx="1730" cy="690" r="16" fill="#6B4A35"/>')
    c.append("</g>")
    c.append('<g id="chao">' + R(0, 870, W, 210, "#9A6B45"))
    for x in range(0, W, 120):
        c.append(P(f"M{x} 870 V1080", "none", "#875C3A", 3))
    c.append(f'<ellipse cx="960" cy="980" rx="520" ry="60" fill="#A33B33" opacity="0.85"/><ellipse cx="960" cy="980" rx="460" ry="44" fill="none" stroke="#E2C48A" stroke-width="6"/></g>')
    return svg("casa-antonio", "Casa do Seu Antônio — sala", c, defs)


def campo_instalador():
    c = ['<g id="fundo">', R(0, 0, W, 760, "url(#ceu)")]
    for x, y, s in ((200, 100, 1.0), (900, 70, 1.2), (1500, 130, 0.9)):
        c.append(nuvem(x, y, s))
    # casa do cliente
    c.append(R(200, 260, 1100, 520, "#F3E2B3"))
    c.append(P("M160 270 L750 90 L1340 270 Z", "#B5563A", "#8E3F28", 4))
    c.append(R(260, 360, 220, 200, "#BFE0F7", 4, "#FFFFFF", 12) + R(366, 360, 8, 200, "#FFFFFF") + R(260, 456, 220, 8, "#FFFFFF"))
    c.append(R(620, 380, 160, 400, "#8E6440", 4, "#6B4A35", 4) + f'<circle cx="760" cy="590" r="8" fill="#E2C48A"/>')
    # portão da garagem
    c.append(R(880, 420, 380, 360, "#5E6670", 4, "#454C55", 4))
    for y in range(440, 780, 30):
        c.append(R(880, y, 380, 6, "#4D545D"))
    # câmera sendo instalada no canto da casa, com cabo
    c.append(camera_bullet(1290, 300, 0.9, led=True))
    c.append(P("M1290 330 Q1310 420 1296 600", "none", "#1E1F22", 4))
    # muro e calçada
    c.append(R(1300, 520, 620, 260, "#E9E2D3") + R(1300, 510, 620, 16, "#D9D0BE"))
    c.append(camera_dome(1610, 540, 0.9))
    c.append("</g>")
    c.append('<g id="chao">' + R(0, 780, W, 300, "#BDB7AE"))
    for x in range(0, W, 180):
        c.append(P(f"M{x} 780 L{x - 40} 1080", "none", "#AAA49A", 3))
    c.append(R(0, 780, W, 18, "#D8D2C8") + "</g>")
    c.append('<g id="moveis">')
    # escada encostada na parede
    c.append(P("M1180 860 L1250 330 M1270 860 L1330 330", "none", "#C0C6CC", 14))
    for k in range(8):
        y = 820 - k * 62
        t = (860 - y) / 530
        c.append(P(f"M{1180 + 70 * t:.0f} {y} L{1270 + 60 * t:.0f} {y}", "none", "#AEB5BC", 10))
    # caixa de ferramentas e rolo de cabo
    c.append(R(1420, 880, 170, 80, "#D9362B", 8, "#9E2219", 3) + R(1470, 862, 70, 22, "#9E2219", 6))
    c.append(f'<circle cx="1680" cy="910" r="50" fill="#2E3134"/><circle cx="1680" cy="910" r="20" fill="#9AA5B1"/>')
    # van da Protemaxxi
    c.append(R(1620, 640, 320, 260, "#F7F9FB", 30, "#B9C0C7", 4))
    c.append(R(1620, 760, 320, 50, "#1FAE5A"))
    c.append(logo(1680, 670, 200, "#22374B", "logotipo"))
    c.append(f'<circle cx="1700" cy="910" r="44" fill="#26292D"/><circle cx="1700" cy="910" r="18" fill="#9AA5B1"/>')
    c.append("</g>")
    return svg("campo-instalador", "Campo — casa do cliente com instalação", c)


def suporte_tecnico():
    c = ['<g id="fundo">', R(0, 0, W, H, "#23272D")]
    c.append(R(0, 0, W, 60, "#1B1E23") + P("M100 60 H1820", "none", "#1FAE5A", 6, 'opacity="0.8"'))
    # logo grande na parede, como letreiro
    c.append(logo(1200, 170, 560, "#2F363F", "logotipo"))
    # prateleira com equipamentos
    c.append(R(160, 300, 600, 14, "#3A414A"))
    c.append(R(190, 240, 120, 60, "#1A1C1F", 6) + R(330, 250, 60, 50, "#F4F6F8", 18) + f'<circle cx="360" cy="272" r="10" fill="#26292D"/>' + R(410, 230, 140, 70, VERDE_CAIXA, 3) + R(570, 245, 160, 55, "#1A1C1F", 6))
    c.append(planta(1760, 640, 0.9, "#3A414A"))
    c.append("</g>")
    c.append('<g id="moveis">')
    # mesa com dois monitores
    c.append(R(300, 700, 1320, 30, "#C9A777", 6, "#8E6440", 3) + R(340, 730, 24, 250, "#2A2C30") + R(1556, 730, 24, 250, "#2A2C30"))
    c.append(tela_cameras(420, 380, 520, 300))
    c.append(R(650, 680, 60, 20, "#2A2C30") + R(980, 680, 60, 20, "#2A2C30"))
    c.append(R(760, 380, 0, 0, "#000"))
    c.append(R(1000, 390, 500, 290, "#1C1E21", 8) + R(1010, 400, 480, 270, "#F4F7FA"))
    c.append(R(1010, 400, 480, 40, "#1FAE5A") + logo(1024, 406, 30))
    for k, y in enumerate((460, 510, 560, 610)):
        c.append(R(1030, y, 300, 30, "#E3E9EF", 6) + R(1350, y, 120, 30, "#2B7BB9" if k == 2 else "#C9D3DD", 6))
    # teclado, mouse, caneca
    c.append(R(700, 690, 300, 14, "#3A3E44", 4) + f'<ellipse cx="1060" cy="696" rx="22" ry="10" fill="#3A3E44"/>')
    c.append(R(1300, 640, 44, 60, "#1FAE5A", 6) + P("M1344 655 q22 0 22 20 q0 18 -22 18", "none", "#1FAE5A", 6))
    c.append("</g>")
    c.append('<g id="chao">' + R(0, 900, W, 180, "#2C3138") + P("M0 900 H1920", "none", "#3A414A", 4) + "</g>")
    return svg("suporte-tecnico", "Central de suporte técnico", c)


CENARIOS = {
    "loja-interior": loja_interior,
    "loja-painel": loja_painel,
    "estoque-expedicao": estoque_expedicao,
    "fachada": fachada,
    "casa-fernanda": casa_fernanda,
    "casa-antonio": casa_antonio,
    "campo-instalador": campo_instalador,
    "suporte-tecnico": suporte_tecnico,
}


def folha():
    dados = json.loads((RAIZ / "cenarios" / "cenarios.json").read_text(encoding="utf-8"))
    cartoes = "".join(
        f'<article><img src="{c["arquivo"]}" alt="{html.escape(c["nome"])}"><h2>{html.escape(c["nome"])}</h2>'
        f'<p>{html.escape(c["descricao"])}</p><p class="uso"><b>Personagens:</b> {html.escape(", ".join(c["personagens"]))}</p></article>'
        for c in dados["cenarios"]
    )
    pagina = f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cenários Protemaxxi</title>
<style>
body{{margin:0;font-family:system-ui,sans-serif;background:#EEF3F8;color:#11202F}}
header{{background:#11202F;color:#fff;padding:20px 24px}} h1{{margin:0;font-size:22px}}
main{{display:grid;grid-template-columns:repeat(auto-fill,minmax(420px,1fr));gap:18px;padding:20px}}
article{{background:#fff;border-radius:14px;padding:14px;box-shadow:0 2px 8px #0001}}
img{{width:100%;aspect-ratio:16/9;border-radius:8px}} h2{{margin:10px 0 4px}} p{{font-size:14px;line-height:1.4;margin:4px 0}}
.uso{{color:#5F7488}}
</style></head><body><header><h1>Video Factory Protemaxxi · Cenários</h1></header>
<main>{cartoes}</main></body></html>
"""
    (RAIZ / "cenarios" / "folha.html").write_text(pagina, encoding="utf-8")


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    for slug, fn in CENARIOS.items():
        (SAIDA / f"{slug}.svg").write_text(fn(), encoding="utf-8")
        print("ok", slug)
    folha()
    print("ok folha.html")


if __name__ == "__main__":
    main()
