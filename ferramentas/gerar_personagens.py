"""Gera os SVGs 2D (estilo cartoon) dos personagens da Video Factory Protemaxxi.

Uso:  python ferramentas/gerar_personagens.py

Cada personagem sai em personagens/svg/<slug>.svg, com grupos nomeados
(braco-esq, braco-dir, tronco, cabeca, olhos, sobrancelhas, boca...) para
animar depois (piscar, sincronia labial, gestos). Também gera
personagens/folha.html para revisão.

Estilo: cabeça grande (~3,5 cabeças de altura), contorno fino na cor de
cada peça, sombreado chapado, olhos de cartoon, braços afinando até a mão.
"""
from __future__ import annotations

import html
import json
import math
import pathlib
import re

RAIZ = pathlib.Path(__file__).resolve().parents[1]
SAIDA = RAIZ / "personagens" / "svg"

AZUL = "#2B7BB9"
VERDE = "#1FAE5A"
MARINHO = "#22374B"
TINTA = "#2A1E1A"  # olhos e linhas do rosto


def _d_do_svg(nome: str) -> str:
    texto = (RAIZ / "assets" / "marca" / nome).read_text(encoding="utf-8")
    return re.search(r'\sd="([^"]+)"', texto).group(1)


ICONE_D = _d_do_svg("icone.svg")
LOGO_D = _d_do_svg("logotipo.svg")


# ------------------------------------------------------------------ utilidades
def esc(cor: str, f: float = 0.8) -> str:
    """Escurece (f < 1) ou clareia (f > 1) uma cor #RRGGBB."""
    cor = cor.lstrip("#")
    r, g, b = (int(cor[i : i + 2], 16) for i in (0, 2, 4))
    if f <= 1:
        r, g, b = (int(v * f) for v in (r, g, b))
    else:
        r, g, b = (int(v + (255 - v) * (f - 1)) for v in (r, g, b))
    return "#{:02X}{:02X}{:02X}".format(r, g, b)


def forma(d: str, cor: str, linha: str | None = None, w: float = 3.5, extra: str = "") -> str:
    linha = linha or esc(cor, 0.55)
    return f'<path d="{d}" fill="{cor}" stroke="{linha}" stroke-width="{w}" {extra}/>'


def logo(x, y, w, cor="#FFFFFF", tipo="icone") -> str:
    vb_w, vb_h = (244, 225) if tipo == "icone" else (591, 150)
    return f'<use href="#{tipo}" x="{x}" y="{y}" width="{w}" height="{w * vb_h / vb_w:.1f}" fill="{cor}"/>'


def espelho(d: str) -> str:
    """Espelha um path horizontalmente em torno de x = 200 (só comandos absolutos M L C Q H V Z)."""
    out, cmd, idx = [], "", 0
    for tok in re.findall(r"[MLCQHVZ]|-?\d+\.?\d*", d):
        if tok.isalpha():
            cmd, idx = tok, 0
            out.append(tok)
            continue
        v = float(tok)
        if cmd == "H" or (cmd in "MLCQ" and idx % 2 == 0):
            v = 400 - v
        out.append(f"{v:g}")
        idx += 1
    return " ".join(out)


# curva quadrática
def _b(s, e, w, t):
    return tuple((1 - t) ** 2 * a + 2 * (1 - t) * t * b + t * t * c for a, b, c in zip(s, e, w))


def _db(s, e, w, t):
    return tuple(2 * (1 - t) * (b - a) + 2 * t * (c - b) for a, b, c in zip(s, e, w))


def faixa(pts, t0, t1, w0, w1, extra=0.0, n=18) -> str:
    """Polígono de um trecho do membro, afinando de w0 (ombro) a w1 (pulso)."""
    s, e, w = pts
    esq, dir_ = [], []
    for i in range(n + 1):
        t = t0 + (t1 - t0) * i / n
        x, y = _b(s, e, w, t)
        dx, dy = _db(s, e, w, t)
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        hw = (w0 + (w1 - w0) * t) / 2 + extra
        esq.append((x + nx * hw, y + ny * hw))
        dir_.append((x - nx * hw, y - ny * hw))
    p = esq + dir_[::-1]
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in p) + " Z"


# ------------------------------------------------------------------ corpo
BRACO_E = ((104, 374), (80, 486), (74, 590))
BRACO_D = ((296, 374), (320, 486), (326, 590))


def mao(x, y, cor, lado, linha=None):
    """Mão em luva de cartoon com polegar apontando para o corpo."""
    linha = linha or esc(cor, 0.6)
    s = 1 if lado == "e" else -1
    return (
        f'<ellipse cx="{x}" cy="{y + 18}" rx="23" ry="27" fill="{cor}" stroke="{linha}" stroke-width="3.5"/>'
        f'<ellipse cx="{x + 18 * s}" cy="{y + 9}" rx="9" ry="15" transform="rotate({-28 * s} {x + 18 * s} {y + 9})" '
        f'fill="{cor}" stroke="{linha}" stroke-width="3.5"/>'
        f'<path d="M{x - 10 * s} {y + 34} q{6 * s} 6 {15 * s} 4" fill="none" stroke="{linha}" stroke-width="2.5" stroke-linecap="round"/>'
    )


def braco(id_, pele, pts, lado, manga=None, ate=0.42, w0=44, w1=34, cor_mao=None, punho=None,
          relogio=None, contas=None, frente=False):
    out = [f'<g id="{id_}">']
    sx, sy = pts[0]
    tampa = manga if (manga and ate > 0) else pele
    linha_t = (esc(tampa, 0.55) if tampa.startswith("#") else "#5A1E1A")
    out.append(f'<circle cx="{sx}" cy="{sy}" r="{w0 / 2 + 4}" fill="{tampa}" stroke="{linha_t}" stroke-width="3.5"/>')
    out.append(forma(faixa(pts, 0, 1, w0, w1), pele, esc(pele, 0.62)))
    if manga and ate > 0:
        linha = esc(manga, 0.55) if manga.startswith("#") else "#5A1E1A"
        out.append(forma(faixa(pts, 0, ate, w0, w1, extra=4), manga, linha))
        if punho:
            out.append(forma(faixa(pts, ate - 0.06, ate, w0, w1, extra=4), punho, esc(punho, 0.6)))
        x, y = pts[0]
        out.append(f'<circle cx="{x}" cy="{y}" r="{w0 / 2 + 2}" fill="{manga}"/>')
    if relogio:
        pulseira, visor = relogio
        out.append(forma(faixa(pts, 0.85, 0.92, w0, w1, extra=1), pulseira, esc(pulseira, 0.6), 2.5))
        x, y = _b(*pts, 0.885)
        out.append(f'<rect x="{x - 10:.1f}" y="{y - 10:.1f}" width="20" height="20" rx="6" fill="{visor}" stroke="{esc(pulseira, 0.6)}" stroke-width="3"/>')
    if contas:
        x, y = _b(*pts, 0.9)
        for dx in range(-14, 16, 6):
            out.append(f'<circle cx="{x + dx:.1f}" cy="{y + abs(dx) * 0.08:.1f}" r="3.2" fill="{contas}"/>')
    x, y = pts[2]
    out.append(mao(x, y, cor_mao or pele, lado))
    out.append("</g>")
    return "\n".join(out)


def tronco_d(ombro=112, cintura=96, topo=345, base=610, barriga=0):
    lo, lc, b = ombro, cintura, barriga
    return (
        f"M{200 - lo + 26} {topo} Q200 {topo - 10} {200 + lo - 26} {topo} "
        f"Q{200 + lo} {topo + 4} {200 + lo} {topo + 46} "
        f"L{200 + lc + b} {base - 60} Q{200 + lc + b + 6} {base} {200 + lc - 24} {base} "
        f"L{200 - lc + 24} {base} Q{200 - lc - b - 6} {base} {200 - lc - b} {base - 60} "
        f"L{200 - lo} {topo + 46} Q{200 - lo} {topo + 4} {200 - lo + 26} {topo} Z"
    )


def tronco(id_clip, cor, linha=None, sombra_cor=None, **kw):
    d = tronco_d(**kw)
    sombra_cor = sombra_cor or (esc(cor, 0.86) if cor.startswith("#") else "#000")
    op = 1 if cor.startswith("#") else 0.15
    return (
        f'<clipPath id="{id_clip}"><path d="{d}"/></clipPath>'
        + forma(d, cor, linha or (esc(cor, 0.55) if cor.startswith("#") else "#5A1E1A"), extra='id="tronco"')
        + f'<g clip-path="url(#{id_clip})"><path d="M262 330 Q300 470 268 640 L340 640 L340 330 Z" fill="{sombra_cor}" opacity="{op}"/></g>'
    )


def pescoco(pele, larg=46):
    x = 200 - larg / 2
    return (
        f'<rect x="{x}" y="296" width="{larg}" height="64" rx="16" fill="{pele}" stroke="{esc(pele, 0.62)}" stroke-width="3.5"/>'
        f'<path d="M{x + 2} 318 Q200 340 {x + larg - 2} 318 L{x + larg - 2} 300 L{x + 2} 300 Z" fill="{esc(pele, 0.85)}"/>'
    )


def calca(cor, cintura=588):
    d = f"M106 {cintura} H294 L284 840 H210 L200 668 L190 840 H116 Z"
    return (
        forma(d, cor, extra='id="calca"')
        + f'<path d="M200 {cintura + 50} V668" stroke="{esc(cor, 0.55)}" stroke-width="3"/>'
        + f'<path d="M258 {cintura + 20} L270 836" stroke="{esc(cor, 0.85)}" stroke-width="16" opacity="0.6"/>'
    )


SAPATO_E = "M110 852 Q106 826 134 824 H170 Q196 824 198 846 V858 Q198 864 192 864 H114 Q106 864 110 852 Z"


def sapatos(cor, sola="#3A3A3A", bico=None, detalhe=None):
    out = ['<g id="sapatos">']
    for d in (SAPATO_E, espelho(SAPATO_E)):
        out.append(forma(d, cor))
    out.append(f'<rect x="104" y="856" width="98" height="13" rx="6.5" fill="{sola}" stroke="{esc(sola, 0.6)}" stroke-width="3"/>')
    out.append(f'<rect x="198" y="856" width="98" height="13" rx="6.5" fill="{sola}" stroke="{esc(sola, 0.6)}" stroke-width="3"/>')
    if bico:
        out.append(f'<path d="M112 852 Q110 832 132 830 H148 V856 H112 Z" fill="{bico}"/>')
        out.append(f'<path d="M288 852 Q290 832 268 830 H252 V856 H288 Z" fill="{bico}"/>')
    if detalhe:
        out.append(f'<path d="M140 846 L176 834 M260 846 L224 834" stroke="{detalhe}" stroke-width="6" stroke-linecap="round"/>')
    out.append("</g>")
    return "\n".join(out)


def sombra_chao():
    return '<ellipse cx="200" cy="872" rx="128" ry="13" fill="#000" opacity="0.12"/>'


# ------------------------------------------------------------------ rosto
def rosto_d(w=96, topo=105, queixo=322, mand=0.55):
    my = 214
    a = my + (queixo - my) * mand
    return (
        f"M200 {topo} C{200 + w * 0.62} {topo} {200 + w} {topo + 42} {200 + w} {my} "
        f"C{200 + w} {a:.0f} {200 + w * 0.5:.0f} {queixo} 200 {queixo} "
        f"C{200 - w * 0.5:.0f} {queixo} {200 - w} {a:.0f} {200 - w} {my} "
        f"C{200 - w} {topo + 42} {200 - w * 0.62} {topo} 200 {topo} Z"
    )


def cabeca(pele, w=96, queixo=322, mand=0.55, extra_rosto=""):
    """Orelhas + rosto + sombra lateral. extra_rosto é desenhado recortado no rosto."""
    d = rosto_d(w, queixo=queixo, mand=mand)
    linha = esc(pele, 0.62)
    ox = 200 - w
    return (
        f'<g id="orelhas">'
        f'<ellipse cx="{ox + 2}" cy="230" rx="16" ry="22" fill="{pele}" stroke="{linha}" stroke-width="3.5"/>'
        f'<ellipse cx="{400 - ox - 2}" cy="230" rx="16" ry="22" fill="{pele}" stroke="{linha}" stroke-width="3.5"/>'
        f'<path d="M{ox} 222 q8 6 2 16 M{400 - ox} 222 q-8 6 -2 16" fill="none" stroke="{esc(pele, 0.78)}" stroke-width="4" stroke-linecap="round"/>'
        f"</g>"
        f'<clipPath id="clip-rosto"><path d="{d}"/></clipPath>'
        + forma(d, pele, linha, extra='id="rosto"')
        + f'<g clip-path="url(#clip-rosto)">'
        f'<ellipse cx="{200 + w + 8}" cy="236" rx="40" ry="130" fill="{esc(pele, 0.9)}"/>'
        f"{extra_rosto}</g>"
    )


def olhos(cilios=False, dy=0, afastamento=36):
    y = 222 + dy
    out = ['<g id="olhos">']
    for s in (-1, 1):
        x = 200 + s * afastamento
        out.append(f'<ellipse cx="{x}" cy="{y}" rx="10" ry="14" fill="{TINTA}"/>')
        out.append(f'<circle cx="{x + 3}" cy="{y - 5}" r="4" fill="#FFF"/>')
        out.append(f'<circle cx="{x - 3}" cy="{y + 6}" r="1.8" fill="#FFF"/>')
        if cilios:
            out.append(
                f'<path d="M{x + s * 8} {y - 10} l{s * 9} -6 M{x + s * 10} {y - 4} l{s * 10} -2" '
                f'stroke="{TINTA}" stroke-width="3.5" stroke-linecap="round"/>'
            )
    out.append("</g>")
    return "\n".join(out)


def sobrancelhas(cor, esp=9, dy=0, forma_="normal", afastamento=36):
    y = 188 + dy
    if forma_ == "reta":
        d = (f"M{200 - afastamento - 18} {y + 2} L{200 - afastamento + 16} {y - 2} "
             f"M{200 + afastamento - 16} {y - 2} L{200 + afastamento + 18} {y + 2}")
    else:
        d = (f"M{200 - afastamento - 18} {y + 4} Q{200 - afastamento} {y - 8} {200 - afastamento + 16} {y + 1} "
             f"M{200 + afastamento - 16} {y + 1} Q{200 + afastamento} {y - 8} {200 + afastamento + 18} {y + 4}")
    return f'<path id="sobrancelhas" d="{d}" fill="none" stroke="{cor}" stroke-width="{esp}" stroke-linecap="round"/>'


def nariz(pele):
    return f'<path id="nariz" d="M191 250 Q200 260 209 250" fill="none" stroke="{esc(pele, 0.68)}" stroke-width="4.5" stroke-linecap="round"/>'


def boca(tipo="aberta", labio=None, dy=0):
    y = 270 + dy
    if tipo == "fechada":
        return (f'<g id="boca"><path d="M180 {y + 2} Q200 {y + 18} 220 {y + 2}" fill="none" stroke="{labio or "#7A2E34"}" '
                f'stroke-width="5" stroke-linecap="round"/></g>')
    linha = labio or "#5A1A22"
    return (
        '<g id="boca">'
        f'<clipPath id="clip-boca"><path d="M176 {y} Q200 {y + 32} 224 {y} Q200 {y + 6} 176 {y} Z"/></clipPath>'
        f'<path d="M176 {y} Q200 {y + 32} 224 {y} Q200 {y + 6} 176 {y} Z" fill="#6E2630"/>'
        f'<g clip-path="url(#clip-boca)"><rect x="170" y="{y - 2}" width="60" height="9" fill="#FFF"/>'
        f'<ellipse cx="200" cy="{y + 20}" rx="13" ry="7" fill="#E0707A"/></g>'
        f'<path d="M176 {y} Q200 {y + 32} 224 {y} Q200 {y + 6} 176 {y} Z" fill="none" stroke="{linha}" stroke-width="3.5" stroke-linejoin="round"/>'
        "</g>"
    )


# ------------------------------------------------------------------ documento
def svg(slug, titulo, camadas, defs_extra=""):
    corpo = "\n".join(camadas)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 900" width="400" height="900">
<title>{titulo}</title>
<defs>
<symbol id="icone" viewBox="0 0 244 225"><path fill-rule="evenodd" clip-rule="evenodd" d="{ICONE_D}"/></symbol>
<symbol id="logotipo" viewBox="0 0 591 150"><path fill-rule="evenodd" clip-rule="evenodd" d="{LOGO_D}"/></symbol>
{defs_extra}
</defs>
<g id="{slug}" stroke-linejoin="round">
{corpo}
</g>
</svg>
"""


# ------------------------------------------------------------------ personagens
def vinicius():
    """Apresentador geral: baseado no próprio Vinícius."""
    pele, cabelo, camiseta = "#EEC5A4", "#1C1512", "#1A1C20"
    c = [sombra_chao(), calca("#2A2E35"), sapatos("#F1EEE8", sola="#D3CEC4", detalhe="#C9C3B8")]
    kw = dict(w0=52, w1=38)
    be = ((100, 376), (72, 488), (66, 592))
    bd = ((300, 376), (328, 488), (334, 592))
    c.append(pescoco(pele, 58))
    c.append(tronco("clip-tronco", camiseta, ombro=120, cintura=100, barriga=10))
    c.append(f'<path d="M168 346 Q200 378 232 346" fill="none" stroke="#33373D" stroke-width="9" stroke-linecap="round"/>')
    c.append('<rect x="212" y="396" width="54" height="54" rx="4" fill="none" stroke="#FFF" stroke-width="3"/>')
    c.append(logo(220, 405, 38))
    c.append('<path d="M132 520 Q156 530 178 522 M226 540 Q250 548 272 538" fill="none" stroke="#2C3036" stroke-width="4" stroke-linecap="round"/>')
    barba = (
        f'<path d="M96 214 C98 290 150 330 200 330 C250 330 302 290 304 214 C300 262 280 290 252 298 '
        f'C236 302 224 292 200 290 C176 292 164 302 148 298 C120 290 100 262 96 214 Z" fill="{cabelo}" opacity="0.2"/>'
        f'<path d="M178 300 Q200 292 222 300 Q218 324 200 326 Q182 324 178 300 Z" fill="{cabelo}" opacity="0.18"/>'
    )
    c.append(braco("braco-esq", pele, be, "e", camiseta, 0.4, **kw))
    c.append(braco("braco-dir", pele, bd, "d", camiseta, 0.4, contas="#4A4A4A", **kw))
    c.append('<path d="M54 618 q12 6 24 2" fill="none" stroke="#D4A537" stroke-width="5" stroke-linecap="round"/>')
    c.append('<g id="cabeca">' + cabeca(pele, w=100, queixo=326, mand=0.72, extra_rosto=barba))
    c.append(nariz(pele))
    c.append(olhos())
    c.append(sobrancelhas(cabelo, esp=11, forma_="reta"))
    c.append(boca())
    c.append(f'<path d="M180 266 Q200 258 220 266" fill="none" stroke="{cabelo}" stroke-width="6" stroke-linecap="round" opacity="0.45"/>')
    # cabelo liso penteado para trás, com volume em cima
    cab = ("M98 214 C88 150 110 96 160 76 C200 60 256 64 286 92 C308 114 312 166 302 214 "
           "C296 186 288 168 272 156 C250 140 226 136 200 138 C172 140 148 146 128 160 C112 172 102 192 98 214 Z")
    c.append('<g id="cabelo">' + forma(cab, cabelo, "#0C0908"))
    c.append('<path d="M140 150 C150 112 186 88 236 84 M172 142 C188 112 220 100 266 108 M220 138 C240 124 262 124 284 136 '
             'M120 172 C122 136 140 108 170 94" fill="none" stroke="#3A2E28" stroke-width="4" stroke-linecap="round"/>')
    c.append('<path d="M168 92 C196 78 230 76 256 84" fill="none" stroke="#5C4A40" stroke-width="7" stroke-linecap="round" opacity="0.7"/>')
    c.append("</g></g>")
    return svg("vinicius-apresentador", "Vinícius — Apresentador", c)


def marcao():
    pele, uniforme, colete, refl, luva = "#B97A45", MARINHO, "#FF7A1A", "#E3E9EF", "#F0B93A"
    c = [sombra_chao(), calca("#1C2B3A"), sapatos("#5A3B26", sola="#2E2018", bico="#AEB6BF")]
    c.append(pescoco(pele))
    c.append(tronco("clip-tronco", uniforme, ombro=116, barriga=6))
    vest = ("M124 352 Q150 344 172 344 L186 420 L200 446 L214 420 L228 344 Q250 344 276 352 "
            "Q306 360 308 396 L300 600 Q200 616 100 600 L92 396 Q94 360 124 352 Z")
    c.append('<clipPath id="clip-colete"><path d="' + vest + '"/></clipPath>')
    c.append(forma(vest, colete, extra='id="colete"'))
    c.append(f'<g clip-path="url(#clip-colete)"><rect x="80" y="494" width="240" height="18" fill="{refl}"/>'
             f'<rect x="80" y="540" width="240" height="18" fill="{refl}"/>'
             f'<path d="M262 330 Q300 470 268 640 L340 640 L340 330 Z" fill="#000" opacity="0.1"/></g>')
    c.append(f'<path d="M200 446 V606" stroke="{esc(colete, 0.6)}" stroke-width="3"/>')
    c.append(logo(226, 384, 46))
    # cinto de ferramentas
    c.append(f'<rect x="98" y="578" width="204" height="24" rx="6" fill="#6B4423" stroke="#3E2614" stroke-width="3"/>')
    c.append(f'<rect x="186" y="578" width="28" height="24" rx="4" fill="#C9CED4" stroke="#7A828A" stroke-width="3"/>')
    for x in (110, 246):
        c.append(f'<rect x="{x}" y="596" width="44" height="50" rx="9" fill="#80542F" stroke="#3E2614" stroke-width="3"/>')
    c.append('<rect x="120" y="568" width="9" height="30" rx="3" fill="#E63946"/><rect x="134" y="574" width="9" height="24" rx="3" fill="#2B7BB9"/>')
    c.append('<path d="M258 588 l10 -30 l8 4 l-8 28 Z" fill="#9AA5B1" stroke="#5A646E" stroke-width="2"/>')
    barba = f'<path d="M96 230 C100 300 150 330 200 330 C250 330 300 300 304 230 C296 280 260 304 200 304 C140 304 104 280 96 230 Z" fill="#2B1B12" opacity="0.2"/>'
    c.append(braco("braco-esq", pele, BRACO_E, "e", uniforme, 0.9, cor_mao=luva, punho=esc(uniforme, 0.75)))
    c.append(braco("braco-dir", pele, BRACO_D, "d", uniforme, 0.9, cor_mao=luva, punho=esc(uniforme, 0.75)))
    c.append('<g id="cabeca">' + cabeca(pele, w=98, queixo=324, mand=0.68, extra_rosto=barba))
    c.append(nariz(pele))
    c.append(olhos())
    c.append(sobrancelhas("#1B120C", esp=10, dy=-4))
    c.append(boca())
    c.append('<path d="M168 266 Q184 250 200 260 Q216 250 232 266 Q216 262 200 268 Q184 262 168 266 Z" fill="#1B120C"/>')
    # óculos de proteção
    c.append(f'<path id="oculos-protecao" d="M144 204 Q200 192 256 204 Q260 240 234 244 Q214 246 206 232 Q200 226 194 232 '
             f'Q186 246 166 244 Q140 240 144 204 Z" fill="#B4E0FA" fill-opacity="0.4" stroke="{AZUL}" stroke-width="5"/>')
    c.append('<path d="M144 214 L102 222 M256 214 L298 222" stroke="#3A4650" stroke-width="8" stroke-linecap="round"/>')
    c.append('<path d="M156 210 Q166 205 178 207" stroke="#FFF" stroke-width="4" stroke-linecap="round" opacity="0.8"/>')
    # capacete
    c.append('<g id="capacete">' + forma("M94 172 C94 64 306 64 306 172 Z", "#F7F9FB", "#9AA6B2"))
    c.append('<path d="M200 98 V168" stroke="#DCE3EA" stroke-width="14"/>')
    c.append('<rect x="78" y="160" width="244" height="24" rx="12" fill="#E7ECF1" stroke="#9AA6B2" stroke-width="3.5"/>')
    c.append(logo(170, 104, 60, AZUL) + "</g>")
    c.append("</g>")
    return svg("marcao-instalador", "Marcão — Instalador", c)


def rodrigo():
    pele, camisa, cabelo = "#F3C9A5", "#DCEBFA", "#6B4128"
    c = [sombra_chao(), calca("#2E3A48"), sapatos("#1F1F1F", sola="#0E0E0E")]
    c.append(pescoco(pele))
    c.append(tronco("clip-tronco", camisa, linha="#7F9AB5"))
    c.append(f'<path d="M226 404 H274 V450 Q250 460 226 450 Z" fill="{esc(camisa, 0.94)}" stroke="#7F9AB5" stroke-width="3"/>')
    c.append(logo(234, 412, 32, AZUL))
    gravata = "M190 352 H210 L206 372 L216 520 L200 544 L184 520 L194 372 Z"
    c.append('<clipPath id="clip-gravata"><path d="' + gravata + '"/></clipPath>')
    c.append(forma(gravata, MARINHO, "#0F1C28", 3))
    c.append(f'<g clip-path="url(#clip-gravata)"><path d="M178 410 L222 380 M178 452 L222 422 M178 494 L222 464" stroke="{AZUL}" stroke-width="6"/></g>')
    c.append(forma("M190 352 H210 L206 372 H194 Z", "#16283A", "#0F1C28", 3))
    c.append(forma("M174 340 L192 356 L170 384 L156 350 Z", "#FFFFFF", "#7F9AB5", 3))
    c.append(forma(espelho("M174 340 L192 356 L170 384 L156 350 Z"), "#FFFFFF", "#7F9AB5", 3))
    c.append('<rect x="104" y="584" width="192" height="18" rx="5" fill="#1B1B1B"/><rect x="188" y="582" width="24" height="22" rx="4" fill="#C8A24A" stroke="#8A6A22" stroke-width="2.5"/>')
    c.append(braco("braco-esq", pele, BRACO_E, "e", camisa, 0.9, punho="#FFFFFF"))
    c.append(braco("braco-dir", pele, BRACO_D, "d", camisa, 0.8, punho="#FFFFFF", relogio=("#C8A24A", "#F7F3E6")))
    c.append('<g id="cabeca">' + cabeca(pele))
    c.append(nariz(pele))
    c.append(olhos())
    c.append(sobrancelhas(cabelo, esp=8))
    c.append(boca())
    cab = ("M100 212 C88 130 140 82 206 82 C268 84 310 126 300 208 C292 176 278 158 258 150 "
           "C228 140 200 158 162 148 C136 150 112 172 100 212 Z")
    c.append('<g id="cabelo">' + forma(cab, cabelo) +
             f'<path d="M150 104 Q186 90 230 98" fill="none" stroke="{esc(cabelo, 1.4)}" stroke-width="6" stroke-linecap="round" opacity="0.6"/></g>')
    c.append('<g id="oculos" fill="#FFF" fill-opacity="0.15" stroke="#2A2A2A" stroke-width="4.5">'
             '<rect x="138" y="200" width="54" height="42" rx="11"/><rect x="208" y="200" width="54" height="42" rx="11"/>'
             '<path d="M192 216 Q200 210 208 216 M138 214 L106 208 M262 214 L294 208" fill="none" stroke-linecap="round"/></g>')
    c.append("</g>")
    return svg("rodrigo-vendedor", "Rodrigo — Vendedor", c)


def luana():
    pele, polo, cabelo = "#A86A4A", VERDE, "#1E1512"
    c = [sombra_chao()]
    c.append('<g id="rabo-de-cavalo">' + forma("M262 150 C350 150 362 262 332 334 C322 356 300 354 306 330 C318 272 312 214 258 184 Z", cabelo) + "</g>")
    c.append(calca("#8C7B5E"))
    c.append('<rect x="114" y="690" width="40" height="52" rx="7" fill="#7C6C50" stroke="#4E4332" stroke-width="3"/>'
             '<rect x="246" y="690" width="40" height="52" rx="7" fill="#7C6C50" stroke="#4E4332" stroke-width="3"/>')
    c.append(sapatos("#2F2F2F", sola="#1A1A1A", bico="#E9B43A"))
    # leitor de código de barras (fica atrás da mão)
    c.append('<g id="leitor"><path d="M14 560 L90 552 Q102 552 102 564 L100 578 Q98 588 88 588 L80 588 L84 628 Q84 636 76 636 L66 636 Q60 636 60 628 L58 592 L20 594 Q10 592 10 582 Z" fill="#F2C230" stroke="#8A6A10" stroke-width="3.5"/>'
             '<path d="M14 562 L36 560 L38 592 L20 594 Q10 592 10 582 Z" fill="#33393F"/>'
             '<path d="M8 572 L-30 562 M8 582 L-28 594" stroke="#FF3B3B" stroke-width="3" opacity="0.85"/></g>')
    c.append(pescoco(pele))
    c.append(tronco("clip-tronco", polo, ombro=106, cintura=92))
    c.append(forma("M176 340 L200 374 L224 340 L242 348 L224 380 L200 366 L176 380 L158 348 Z", esc(polo, 0.85)))
    c.append(f'<path d="M200 370 V424" stroke="{esc(polo, 0.6)}" stroke-width="3"/><circle cx="200" cy="390" r="3.5" fill="#FFF"/><circle cx="200" cy="410" r="3.5" fill="#FFF"/>')
    c.append(logo(230, 396, 40))
    c.append('<rect x="106" y="584" width="188" height="16" rx="5" fill="#3B2F22"/>')
    c.append(braco("braco-esq", pele, BRACO_E, "e", polo, 0.4))
    c.append(braco("braco-dir", pele, BRACO_D, "d", polo, 0.4, relogio=("#2B2B2B", "#9AD7B4")))
    c.append('<g id="cabeca">' + cabeca(pele, w=94, queixo=318, mand=0.5))
    c.append(forma("M106 170 Q98 240 116 280 L130 180 Z", cabelo) + forma(espelho("M106 170 Q98 240 116 280 L130 180 Z"), cabelo))
    c.append(nariz(pele))
    c.append(olhos(cilios=True))
    c.append(sobrancelhas(cabelo, esp=7))
    c.append(boca(labio="#7A2E34"))
    c.append('<g id="bone">' + forma("M96 176 C96 74 304 74 304 176 Z", polo))
    c.append(f'<path d="M200 106 V170" stroke="{esc(polo, 0.85)}" stroke-width="4"/>')
    c.append(f'<ellipse cx="200" cy="178" rx="116" ry="18" fill="{esc(polo, 0.78)}" stroke="{esc(polo, 0.5)}" stroke-width="3.5"/>')
    c.append(logo(174, 106, 52) + "</g>")
    c.append("</g>")
    return svg("luana-estoquista", "Luana — Estoquista", c)


def caio():
    pele, camiseta, cabelo = "#F7D5BB", "#16181B", "#3D2A1E"
    c = [sombra_chao(), calca("#3D5A80"), sapatos("#F7F8FA", sola="#D3D9DF", detalhe=VERDE)]
    c.append(pescoco(pele))
    c.append(tronco("clip-tronco", camiseta, ombro=106, cintura=92))
    c.append('<path d="M170 346 Q200 378 230 346" fill="none" stroke="#2E3237" stroke-width="9" stroke-linecap="round"/>')
    c.append(logo(132, 416, 136, "#FFFFFF", "logotipo"))
    sardas = "".join(f'<circle cx="{x}" cy="{y}" r="2.6" fill="#D49A74"/>' for x, y in
                     ((146, 252), (156, 258), (150, 244), (254, 252), (244, 258), (250, 244)))
    c.append(braco("braco-esq", pele, BRACO_E, "e", camiseta, 0.42))
    c.append(braco("braco-dir", pele, BRACO_D, "d", camiseta, 0.42, relogio=("#111111", AZUL)))
    c.append('<g id="cabeca">' + cabeca(pele, w=94, extra_rosto=sardas))
    c.append(nariz(pele))
    c.append(olhos())
    c.append(sobrancelhas(cabelo, esp=7, dy=-8))
    c.append(boca())
    cab = ("M100 214 C88 160 100 120 128 110 C126 82 158 66 182 82 C196 56 240 60 246 88 C272 76 304 102 292 136 "
           "C306 150 304 190 298 214 C288 180 270 160 248 162 C240 146 222 142 210 156 C192 142 166 148 160 164 "
           "C140 156 112 172 100 214 Z")
    c.append('<g id="cabelo">' + forma(cab, cabelo) + "</g>")
    c.append('<g id="oculos" fill="#FFF" fill-opacity="0.15" stroke="#151515" stroke-width="7">'
             '<circle cx="164" cy="222" r="29"/><circle cx="236" cy="222" r="29"/>'
             '<path d="M193 218 Q200 212 207 218 M135 216 L108 210 M265 216 L292 210" fill="none" stroke-linecap="round"/></g>')
    c.append('<g id="headset"><path d="M98 236 C86 56 314 56 302 236" fill="none" stroke="#242424" stroke-width="14" stroke-linecap="round"/>'
             '<rect x="82" y="206" width="30" height="56" rx="13" fill="#2C2C2C" stroke="#111" stroke-width="3"/>'
             '<rect x="288" y="206" width="30" height="56" rx="13" fill="#2C2C2C" stroke="#111" stroke-width="3"/>'
             '<path d="M98 258 Q108 296 168 292" fill="none" stroke="#242424" stroke-width="6" stroke-linecap="round"/>'
             f'<rect x="164" y="284" width="20" height="14" rx="7" fill="{VERDE}" stroke="#137A3E" stroke-width="2"/></g>')
    c.append("</g>")
    return svg("caio-suporte", "Caio — Suporte técnico", c)


def antonio():
    pele, branco = "#F1C3A4", "#EEEFF1"
    defs = ('<pattern id="xadrez" width="36" height="36" patternUnits="userSpaceOnUse">'
            '<rect width="36" height="36" fill="#B5413A"/>'
            '<rect x="0" y="12" width="36" height="12" fill="#F3E3C3" opacity="0.5"/>'
            '<rect x="12" y="0" width="12" height="36" fill="#F3E3C3" opacity="0.5"/>'
            '<path d="M0 18 H36 M18 0 V36" stroke="#6E1E1B" stroke-width="2"/></pattern>')
    c = [sombra_chao(), calca("#A89272"), sapatos("#5B3A22", sola="#3A2416")]
    c.append(pescoco(pele))
    c.append(tronco("clip-tronco", "url(#xadrez)", barriga=22))
    c.append(forma("M174 340 L190 358 L170 384 L158 350 Z", "#B5413A", "#5A1E1A", 3) + forma(espelho("M174 340 L190 358 L170 384 L158 350 Z"), "#B5413A", "#5A1E1A", 3))
    c.append('<path d="M200 360 V606" stroke="#6E1E1B" stroke-width="3"/>' + "".join(
        f'<circle cx="208" cy="{y}" r="4" fill="#F3E3C3" stroke="#6E1E1B" stroke-width="2"/>' for y in (390, 440, 490, 540)))
    c.append('<path d="M84 594 Q200 618 316 594 L314 612 Q200 636 86 612 Z" fill="#4A2E1A"/><rect x="188" y="602" width="24" height="20" rx="4" fill="#C8A24A" stroke="#8A6A22" stroke-width="2.5"/>')
    rugas = (f'<path d="M160 150 Q200 140 240 150 M170 164 Q200 156 230 164" fill="none" stroke="{esc(pele, 0.78)}" stroke-width="3.5" stroke-linecap="round"/>'
             '<ellipse cx="170" cy="130" rx="30" ry="12" fill="#FFF" opacity="0.4" transform="rotate(-18 170 130)"/>')
    c.append(braco("braco-esq", pele, BRACO_E, "e", "url(#xadrez)", 0.42))
    c.append(braco("braco-dir", pele, BRACO_D, "d", "url(#xadrez)", 0.42))
    c.append('<g id="cabeca">' + cabeca(pele, extra_rosto=rugas))
    tufo = "M102 236 C88 196 100 158 126 146 C124 176 124 200 130 230 Z"
    c.append('<g id="cabelo">' + forma(tufo, branco, "#B9BEC4") + forma(espelho(tufo), branco, "#B9BEC4") + "</g>")
    c.append(nariz(pele))
    c.append(olhos())
    c.append(sobrancelhas(branco, esp=12, dy=-2))
    c.append(boca("fechada", dy=8))
    c.append('<path id="bigode" d="M158 270 Q166 238 200 250 Q234 238 242 270 Q222 258 200 266 Q178 258 158 270 Z" fill="#EEEFF1" stroke="#B9BEC4" stroke-width="3"/>')
    c.append("</g>")
    return svg("seu-antonio-cliente", "Seu Antônio — Cliente", c, defs)


def fernanda():
    pele, blusa, saia, cabelo = "#6E4428", "#F4B942", "#2A9D8F", "#1E1410"
    c = [sombra_chao()]
    cachos = []
    for i in range(24):
        a = 2 * math.pi * i / 24
        x, y = 200 + 128 * math.cos(a), 190 + 118 * math.sin(a)
        if y < 300:
            cachos.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="36"/>')
    c.append(f'<g id="cabelo-volume" fill="{cabelo}" stroke="#0A0605" stroke-width="3.5">{"".join(cachos)}</g>'
             f'<ellipse cx="200" cy="190" rx="130" ry="118" fill="{cabelo}"/>')
    for x in (148, 210):
        c.append(f'<rect x="{x}" y="720" width="42" height="124" rx="18" fill="{pele}" stroke="{esc(pele, 0.62)}" stroke-width="3.5"/>')
    c.append(sapatos("#FFFFFF", sola="#E2E6EA", detalhe="#E76F51"))
    c.append(pescoco(pele))
    c.append(tronco("clip-tronco", blusa, ombro=104, cintura=88))
    c.append('<clipPath id="clip-saia"><path d="M108 578 H292 L320 770 Q200 788 80 770 Z"/></clipPath>')
    c.append(forma("M108 578 H292 L320 770 Q200 788 80 770 Z", saia, extra='id="saia"'))
    c.append(f'<g clip-path="url(#clip-saia)"><path d="M150 600 L134 780 M200 600 V790 M250 600 L266 780" stroke="{esc(saia, 0.8)}" stroke-width="3"/>'
             f'<path d="M262 560 L340 800 L340 560 Z" fill="#000" opacity="0.1"/></g>')
    c.append(f'<path d="M172 346 Q200 382 228 346" fill="{esc(blusa, 0.9)}" stroke="{esc(blusa, 0.55)}" stroke-width="3"/>')
    c.append('<path d="M180 350 Q200 378 220 350" fill="none" stroke="#D4A537" stroke-width="3"/>')
    # braço direito dobrado segurando o celular na frente do corpo
    pts = ((298, 388), (338, 520), (266, 506))
    c.append(braco("braco-dir", pele, pts, "d", blusa, 0.34, relogio=("#D4A537", "#FFF6E0"), frente=True))
    c.append('<g id="celular"><rect x="232" y="440" width="44" height="76" rx="9" fill="#20252B" stroke="#0E1114" stroke-width="3"/>'
             f'<rect x="237" y="448" width="34" height="58" rx="4" fill="{AZUL}"/>'
             '<rect x="241" y="453" width="26" height="18" rx="2" fill="#9FD3F5"/><rect x="241" y="475" width="12" height="11" rx="2" fill="#9FD3F5"/>'
             '<rect x="255" y="475" width="12" height="11" rx="2" fill="#9FD3F5"/></g>')
    c.append(mao(266, 500, pele, "d"))
    c.append(braco("braco-esq", pele, BRACO_E, "e", blusa, 0.4))
    c.append('<g id="cabeca">' + cabeca(pele, w=94, queixo=318, mand=0.5))
    franja = "".join(f'<circle cx="{x}" cy="{y}" r="{r}"/>' for x, y, r in
                     ((128, 132, 30), (160, 108, 32), (200, 98, 34), (240, 108, 32), (272, 132, 30)))
    c.append(f'<g id="franja" fill="{cabelo}" stroke="#0A0605" stroke-width="3.5">{franja}</g><ellipse cx="200" cy="132" rx="90" ry="26" fill="{cabelo}"/>')
    c.append(nariz(pele))
    c.append(olhos(cilios=True))
    c.append(sobrancelhas(cabelo, esp=7))
    c.append(boca(labio="#4A1820"))
    c.append('<circle cx="104" cy="266" r="14" fill="none" stroke="#D4A537" stroke-width="5"/><circle cx="296" cy="266" r="14" fill="none" stroke="#D4A537" stroke-width="5"/>')
    c.append("</g>")
    return svg("fernanda-cliente", "Fernanda — Cliente", c)


PERSONAGENS = {
    "vinicius-apresentador": vinicius,
    "marcao-instalador": marcao,
    "rodrigo-vendedor": rodrigo,
    "luana-estoquista": luana,
    "caio-suporte": caio,
    "seu-antonio-cliente": antonio,
    "fernanda-cliente": fernanda,
}


# ------------------------------------------------------------------ folha de revisão
def folha():
    dados = json.loads((RAIZ / "personagens" / "personagens.json").read_text(encoding="utf-8"))
    cartoes = []
    for p in dados["personagens"]:
        v = p["voz"]
        cartoes.append(
            f'<article><img src="{p["arquivo"]}" alt="{html.escape(p["nome"])}">'
            f'<h2>{html.escape(p["nome"])}</h2><p class="papel">{html.escape(p["papel"])}</p>'
            f'<p>{html.escape(p["visual"])}</p>'
            f'<p class="voz"><b>Voz:</b> {v["genero"]}, {v["idade"]} anos. {html.escape(p["personalidade"])}</p>'
            f'<p class="frase">“{html.escape(v["frase_teste"])}”</p></article>'
        )
    pagina = f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Personagens Protemaxxi</title>
<style>
body{{margin:0;font-family:system-ui,sans-serif;background:#EEF3F8;color:#11202F}}
header{{background:#11202F;color:#fff;padding:20px 24px}} h1{{margin:0;font-size:22px}}
main{{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:18px;padding:20px}}
article{{background:#fff;border-radius:14px;padding:14px;box-shadow:0 2px 8px #0001}}
img{{width:100%;height:340px;object-fit:contain;background:linear-gradient(#E1EEF8,#fff)}}
h2{{margin:8px 0 0}} .papel{{color:#2B7BB9;font-weight:600;margin:2px 0 8px}}
p{{font-size:14px;line-height:1.4}} .frase{{font-style:italic;color:#5F7488}}
</style></head><body><header><h1>Video Factory Protemaxxi · Personagens</h1></header>
<main>{"".join(cartoes)}</main></body></html>
"""
    (RAIZ / "personagens" / "folha.html").write_text(pagina, encoding="utf-8")


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    for slug, fn in PERSONAGENS.items():
        (SAIDA / f"{slug}.svg").write_text(fn(), encoding="utf-8")
        print("ok", slug)
    folha()
    print("ok folha.html")


if __name__ == "__main__":
    main()
