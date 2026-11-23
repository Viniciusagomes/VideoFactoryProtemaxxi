"""Gera os SVGs 2D dos personagens da Video Factory Protemaxxi.

Uso:  python ferramentas/gerar_personagens.py

Cada personagem sai em personagens/svg/<slug>.svg, com grupos nomeados
(bracos, tronco, cabeca, olhos, boca...) para facilitar animação depois
(piscar, sincronia labial, gestos).
"""
from __future__ import annotations

import pathlib
import re

RAIZ = pathlib.Path(__file__).resolve().parents[1]
SAIDA = RAIZ / "personagens" / "svg"

CONTORNO = "#1E2A38"
AZUL = "#2B7BB9"
VERDE = "#1FAE5A"
MARINHO = "#22374B"


def _d_do_svg(nome: str) -> str:
    texto = (RAIZ / "assets" / "marca" / nome).read_text(encoding="utf-8")
    return re.search(r'\sd="([^"]+)"', texto).group(1)


ICONE_D = _d_do_svg("icone.svg")
LOGO_D = _d_do_svg("logotipo.svg")


# ---------------------------------------------------------------- utilidades
def escurecer(cor: str, f: float = 0.8) -> str:
    cor = cor.lstrip("#")
    r, g, b = (int(cor[i : i + 2], 16) for i in (0, 2, 4))
    return "#{:02X}{:02X}{:02X}".format(int(r * f), int(g * f), int(b * f))


def O(w: float = 4) -> str:
    return f'stroke="{CONTORNO}" stroke-width="{w}"'


def _bez(p0, p1, p2, t):
    return tuple((1 - t) ** 2 * a + 2 * (1 - t) * t * b + t**2 * c for a, b, c in zip(p0, p1, p2))


def _sub(p0, p1, p2, a, b):
    """Trecho [a, b] de uma curva quadrática (via blossom)."""
    q0 = _bez(p0, p1, p2, a)
    q2 = _bez(p0, p1, p2, b)
    q1 = tuple(
        (1 - a) * (1 - b) * x0 + ((1 - a) * b + a * (1 - b)) * x1 + a * b * x2
        for x0, x1, x2 in zip(p0, p1, p2)
    )
    return q0, q1, q2


def _d(q0, q1, q2) -> str:
    f = lambda p: f"{p[0]:.1f} {p[1]:.1f}"
    return f"M{f(q0)} Q{f(q1)} {f(q2)}"


def logo(x, y, w, cor="#FFFFFF", tipo="icone") -> str:
    vb_w, vb_h = (244, 225) if tipo == "icone" else (591, 150)
    h = w * vb_h / vb_w
    return f'<use href="#{tipo}" x="{x}" y="{y}" width="{w}" height="{h:.1f}" fill="{cor}"/>'


# ---------------------------------------------------------------- partes
BRACO_ESQ = ((110, 338), (86, 452), (84, 560))
BRACO_DIR = ((290, 338), (314, 452), (316, 560))


def braco(id_, pele, pontos, manga=None, comprimento=0.9, mao=None, relogio=None, punho=None):
    """Braço em traço grosso. comprimento = fração do braço coberta pela manga."""
    s, e, w = pontos
    cheio = _d(s, e, w)
    out = [f'<g id="{id_}">']
    out.append(f'<path d="{cheio}" fill="none" stroke="{CONTORNO}" stroke-width="50"/>')
    out.append(f'<path d="{cheio}" fill="none" stroke="{pele}" stroke-width="42"/>')
    if manga and comprimento > 0:
        trecho = _d(*_sub(s, e, w, 0, comprimento))
        out.append(f'<path d="{trecho}" fill="none" stroke="{CONTORNO}" stroke-width="56"/>')
        out.append(f'<path d="{trecho}" fill="none" stroke="{manga}" stroke-width="48"/>')
        if punho:
            faixa = _d(*_sub(s, e, w, comprimento - 0.07, comprimento))
            out.append(f'<path d="{faixa}" fill="none" stroke="{punho}" stroke-width="48" stroke-linecap="butt"/>')
    if relogio:
        pulseira, mostrador = relogio
        faixa = _d(*_sub(s, e, w, 0.84, 0.9))
        out.append(f'<path d="{faixa}" fill="none" stroke="{CONTORNO}" stroke-width="46" stroke-linecap="butt"/>')
        out.append(f'<path d="{faixa}" fill="none" stroke="{pulseira}" stroke-width="44" stroke-linecap="butt"/>')
        cx, cy = _bez(s, e, w, 0.87)
        out.append(f'<rect x="{cx-11:.1f}" y="{cy-12:.1f}" width="22" height="24" rx="6" fill="{mostrador}" {O(3)}/>')
        out.append(f'<path d="M{cx:.1f} {cy-6:.1f} V{cy:.1f} H{cx+5:.1f}" fill="none" stroke="{CONTORNO}" stroke-width="2"/>')
    cx, cy = w
    cor_mao = mao or pele
    out.append(f'<circle cx="{cx}" cy="{cy+6}" r="23" fill="{cor_mao}" {O()}/>')
    out.append(f'<path d="M{cx-14} {cy+12} q4 8 12 9" fill="none" stroke="{escurecer(cor_mao, 0.7)}" stroke-width="3"/>')
    out.append("</g>")
    return "\n".join(out)


def tronco(cor, barriga=0, ombro=0):
    """Camisa/corpo. barriga > 0 deixa a parte de baixo mais larga."""
    l, r = 92 - ombro, 308 + ombro
    b = barriga
    return (
        f'<path id="tronco-base" d="M{l+28} 306 C160 294 240 294 {r-28} 306 '
        f'C{r} 314 {r+8} 338 {r+6} 368 L{r+b} 470 C{r+b+6} 520 {r-4} 552 296 558 '
        f'C240 566 160 566 104 558 C{l+4} 552 {l-b-6} 520 {l-b} 470 L{l-6} 368 '
        f'C{l-8} 338 {l} 314 {l+28} 306 Z" fill="{cor}" {O()}/>'
    )


def pescoco(pele):
    return (
        f'<rect x="176" y="250" width="48" height="70" rx="14" fill="{pele}" {O()}/>'
        f'<path d="M178 290 Q200 304 222 290" fill="none" stroke="{escurecer(pele, 0.82)}" stroke-width="7"/>'
    )


def calca(cor, cos=540):
    escuro = escurecer(cor, 0.8)
    return (
        f'<path id="calca" d="M104 {cos} H296 L290 832 H208 L200 640 L192 832 H110 Z" fill="{cor}" {O()}/>'
        f'<path d="M200 600 V640" stroke="{escuro}" stroke-width="4"/>'
    )


def sapatos(cor, sola="#2A2A2A", bico=None):
    out = ['<g id="sapatos">']
    for x in (100, 202):
        out.append(f'<path d="M{x+6} 826 H{x+92} Q{x+100} 826 {x+100} 846 V856 H{x} V846 Q{x} 826 {x+6} 826 Z" fill="{cor}" {O()}/>')
        out.append(f'<rect x="{x-2}" y="852" width="104" height="12" rx="6" fill="{sola}" {O()}/>')
        if bico:
            out.append(f'<path d="M{x+60} 830 H{x+92} Q{x+98} 830 {x+98} 846 V852 H{x+60} Z" fill="{bico}" {O(3)}/>')
    out.append("</g>")
    return "\n".join(out)


def sombra():
    return '<ellipse cx="200" cy="876" rx="130" ry="14" fill="#000" opacity="0.13"/>'


def cabeca(pele, rosto_extra=""):
    esc = escurecer(pele, 0.85)
    return (
        f'<g id="orelhas">'
        f'<ellipse cx="114" cy="192" rx="15" ry="21" fill="{pele}" {O()}/>'
        f'<ellipse cx="286" cy="192" rx="15" ry="21" fill="{pele}" {O()}/>'
        f'<path d="M110 184 q8 6 2 16 M290 184 q-8 6 -2 16" fill="none" stroke="{esc}" stroke-width="4"/>'
        f"</g>"
        f'<ellipse id="rosto" cx="200" cy="180" rx="86" ry="94" fill="{pele}" {O()}/>'
        f"{rosto_extra}"
        f'<ellipse cx="150" cy="222" rx="13" ry="8" fill="#FF6B6B" opacity="0.22"/>'
        f'<ellipse cx="250" cy="222" rx="13" ry="8" fill="#FF6B6B" opacity="0.22"/>'
        f'<path id="nariz" d="M201 196 Q190 214 203 216" fill="none" stroke="{escurecer(pele, 0.7)}" stroke-width="4"/>'
    )


def olhos(iris="#4A3020", sobrancelha="#2C1E14", cilios=False, esp_sob=7, sob_y=0):
    out = ['<g id="olhos">']
    for x in (168, 232):
        out.append(f'<ellipse cx="{x}" cy="186" rx="13" ry="15" fill="#FFF" {O(3)}/>')
        out.append(f'<circle cx="{x+1}" cy="188" r="8.5" fill="{iris}"/>')
        out.append(f'<circle cx="{x+1}" cy="188" r="4.5" fill="#111"/>')
        out.append(f'<circle cx="{x+4}" cy="184" r="2.6" fill="#FFF"/>')
    if cilios:
        out.append(f'<path d="M156 178 l-7 -5 M158 174 l-4 -7 M244 178 l7 -5 M242 174 l4 -7" stroke="{CONTORNO}" stroke-width="3"/>')
    out.append("</g>")
    y = 158 + sob_y
    out.append(
        f'<path id="sobrancelhas" d="M152 {y+4} Q166 {y-6} 182 {y+2} M218 {y+2} Q234 {y-6} 248 {y+4}" '
        f'fill="none" stroke="{sobrancelha}" stroke-width="{esp_sob}"/>'
    )
    return "\n".join(out)


def boca(labio=None):
    contorno_labio = f'stroke="{labio}" stroke-width="5"' if labio else O(3)
    return (
        '<g id="boca">'
        f'<path d="M174 228 Q200 256 226 228 Q200 236 174 228 Z" fill="#7A2430" {contorno_labio}/>'
        '<path d="M182 231 Q200 236 218 231 L216 236 Q200 240 184 236 Z" fill="#FFF"/>'
        '<path d="M190 244 Q200 248 210 244" fill="none" stroke="#E0707A" stroke-width="4"/>'
        "</g>"
    )


def svg(slug, titulo, camadas, defs_extra=""):
    corpo = "\n".join(camadas)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 900" width="400" height="900">
<title>{titulo}</title>
<defs>
<symbol id="icone" viewBox="0 0 244 225"><path fill-rule="evenodd" clip-rule="evenodd" d="{ICONE_D}"/></symbol>
<symbol id="logotipo" viewBox="0 0 591 150"><path fill-rule="evenodd" clip-rule="evenodd" d="{LOGO_D}"/></symbol>
<clipPath id="clip-rosto"><ellipse cx="200" cy="180" rx="84" ry="92"/></clipPath>
{defs_extra}
</defs>
<g id="{slug}" stroke-linejoin="round" stroke-linecap="round">
{corpo}
</g>
</svg>
"""


# ---------------------------------------------------------------- personagens
def marcao():
    pele = "#B9783F"
    uniforme = MARINHO
    colete = "#FF7A1A"
    refletivo = "#DCE4EC"
    luva = "#E9B43A"
    c = [sombra(), calca("#1C2B3A"), sapatos("#4A3424", bico="#9AA5B1"), pescoco(pele), tronco(uniforme)]
    # colete refletivo
    c.append(
        f'<path id="colete" d="M118 312 C140 304 160 302 172 302 L186 372 L200 396 L214 372 L228 302 '
        f'C240 302 260 304 282 312 C300 320 308 340 306 370 L300 552 C240 560 160 560 100 552 L94 370 '
        f'C92 340 100 320 118 312 Z" fill="{colete}" {O()}/>'
    )
    c.append(f'<path d="M98 440 H302 M98 488 H302" stroke="{refletivo}" stroke-width="16" stroke-linecap="butt"/>')
    c.append(f'<path d="M98 440 H302 M98 488 H302" stroke="{CONTORNO}" stroke-width="2" stroke-dasharray="0" opacity="0.25"/>')
    c.append(f'<path d="M200 396 V552" stroke="{escurecer(colete, 0.75)}" stroke-width="4"/>')
    c.append(logo(224, 330, 50, "#FFFFFF"))
    # cinto de ferramentas
    c.append(f'<rect x="96" y="528" width="208" height="26" rx="6" fill="#6B4423" {O()}/>')
    c.append(f'<rect x="186" y="530" width="28" height="22" rx="4" fill="#C9CED4" {O(3)}/>')
    c.append(f'<rect x="112" y="548" width="44" height="52" rx="8" fill="#7E5230" {O()}/>')
    c.append(f'<rect x="244" y="548" width="44" height="52" rx="8" fill="#7E5230" {O()}/>')
    c.append(f'<rect x="122" y="520" width="9" height="30" rx="3" fill="#E63946" {O(2)}/>')
    c.append(f'<rect x="136" y="526" width="9" height="24" rx="3" fill="{AZUL}" {O(2)}/>')
    c.append(f'<path d="M258 540 l10 -30 l8 4 l-8 28 Z" fill="#9AA5B1" {O(2)}/>')
    c.append(braco("braco-esq", pele, BRACO_ESQ, uniforme, 0.86, mao=luva, punho=escurecer(uniforme, 0.8)))
    c.append(braco("braco-dir", pele, BRACO_DIR, uniforme, 0.86, mao=luva, punho=escurecer(uniforme, 0.8)))
    barba = f'<path d="M124 214 Q130 276 200 278 Q270 276 276 214 Q262 262 200 262 Q138 262 124 214 Z" fill="#2B1B12" opacity="0.22" clip-path="url(#clip-rosto)"/>'
    c.append('<g id="cabeca">' + cabeca(pele, barba))
    # cabelo (costeletas) e bigode
    c.append(f'<path d="M116 170 Q114 196 122 206 L128 170 Z M284 170 Q286 196 278 206 L272 170 Z" fill="#1B120C" {O(2)}/>')
    c.append(olhos(iris="#3B2414", sobrancelha="#1B120C", esp_sob=8))
    c.append(boca())
    c.append(f'<path d="M172 226 Q186 214 200 222 Q214 214 228 226 Q214 224 200 230 Q186 224 172 226 Z" fill="#1B120C"/>')
    # óculos de proteção
    c.append(
        f'<path id="oculos-protecao" d="M140 172 Q200 160 260 172 Q262 200 238 206 Q218 208 206 196 Q200 192 194 196 '
        f'Q182 208 162 206 Q138 200 140 172 Z" fill="#A8DCFA" fill-opacity="0.45" stroke="{AZUL}" stroke-width="5"/>'
    )
    c.append(f'<path d="M150 176 Q160 172 170 174" stroke="#FFF" stroke-width="4" opacity="0.8"/>')
    c.append(f'<path d="M140 180 L116 186 M260 180 L284 186" stroke="#3A4650" stroke-width="7"/>')
    # capacete
    c.append(
        f'<g id="capacete"><path d="M106 150 C106 60 294 60 294 150 Z" fill="#F7F9FB" {O()}/>'
        f'<path d="M200 90 V140" stroke="#D5DCE3" stroke-width="12" stroke-linecap="butt"/>'
        f'<path d="M106 150 C106 60 294 60 294 150 Z" fill="none" {O()}/>'
        f'<rect x="90" y="140" width="220" height="22" rx="11" fill="#E9EEF3" {O()}/>'
        f"{logo(174, 98, 52, AZUL)}</g>"
    )
    c.append("</g>")
    return svg("marcao-instalador", "Marcão — Instalador", c)


def rodrigo():
    pele = "#F2C6A0"
    camisa = "#DCEBFA"
    cabelo = "#5A3825"
    c = [sombra(), calca("#2E3A48"), sapatos("#1B1B1B", sola="#0E0E0E"), pescoco(pele), tronco(camisa)]
    c.append(f'<path d="M200 330 V548" stroke="{escurecer(camisa, 0.85)}" stroke-width="3"/>')
    for y in (512,):
        c.append(f'<circle cx="208" cy="{y}" r="3.5" fill="#FFF" {O(2)}/>')
    # bolso com logo
    c.append(f'<path d="M226 372 H272 V420 Q249 430 226 420 Z" fill="{escurecer(camisa, 0.93)}" {O(3)}/>')
    c.append(logo(232, 380, 34, AZUL))
    # gravata
    c.append(f'<path id="gravata" d="M190 312 H210 L206 330 L216 470 L200 492 L184 470 L194 330 Z" fill="{MARINHO}" {O(3)}/>')
    c.append(f'<path d="M190 312 H210 L206 330 H194 Z" fill="{escurecer(MARINHO, 0.8)}" {O(3)}/>')
    c.append(f'<clipPath id="clip-gravata"><path d="M194 330 L206 330 L216 470 L200 492 L184 470 Z"/></clipPath>'
             f'<path d="M180 370 L220 340 M180 410 L222 378 M180 450 L222 418" stroke="{AZUL}" stroke-width="5" clip-path="url(#clip-gravata)"/>')
    # colarinho
    c.append(f'<path d="M176 298 L190 312 L170 336 L158 304 Z M224 298 L210 312 L230 336 L242 304 Z" fill="#FFFFFF" {O(3)}/>')
    # cinto
    c.append(f'<rect x="102" y="534" width="196" height="18" rx="5" fill="#1B1B1B" {O(3)}/>')
    c.append(f'<rect x="188" y="532" width="24" height="22" rx="4" fill="#C8A24A" {O(3)}/>')
    c.append(braco("braco-esq", pele, BRACO_ESQ, camisa, 0.9, punho="#FFFFFF"))
    c.append(braco("braco-dir", pele, BRACO_DIR, camisa, 0.78, punho="#FFFFFF", relogio=("#C8A24A", "#F4F1E8")))
    c.append('<g id="cabeca">' + cabeca(pele))
    c.append(
        f'<path id="cabelo" d="M112 176 C96 92 156 62 214 70 C268 76 304 112 288 176 '
        f'C280 140 262 122 236 116 C204 110 176 132 146 126 C128 134 118 150 112 176 Z" fill="{cabelo}" {O()}/>'
    )
    c.append(f'<path d="M150 98 Q186 84 226 92" fill="none" stroke="{escurecer(cabelo, 1.35)}" stroke-width="5" opacity="0.6"/>')
    c.append(olhos(iris="#4F7A3A", sobrancelha=cabelo))
    c.append(boca())
    # óculos de armação fina
    c.append(
        f'<g id="oculos" fill="#FFFFFF" fill-opacity="0.12" stroke="{CONTORNO}" stroke-width="4">'
        f'<rect x="146" y="170" width="44" height="32" rx="9"/><rect x="210" y="170" width="44" height="32" rx="9"/>'
        f'<path d="M190 182 Q200 176 210 182 M146 180 L118 176 M254 180 L282 176" fill="none"/></g>'
    )
    c.append("</g>")
    return svg("rodrigo-vendedor", "Rodrigo — Vendedor", c)


def luana():
    pele = "#A8694A"
    polo = VERDE
    cabelo = "#1A1210"
    c = [sombra()]
    # rabo de cavalo (atrás da cabeça)
    c.append(
        f'<path id="rabo-de-cavalo" d="M262 120 C330 120 338 210 314 270 C306 292 286 296 290 270 '
        f'C300 220 296 170 252 150 Z" fill="{cabelo}" {O()}/>'
    )
    c += [calca("#8C7B5E"), sapatos("#2B2B2B", bico="#E9B43A"), pescoco(pele), tronco(polo, ombro=-4)]
    # bolsos laterais da calça cargo
    c.append(f'<rect x="112" y="640" width="40" height="50" rx="6" fill="#7C6C50" {O(3)}/>')
    c.append(f'<rect x="248" y="640" width="40" height="50" rx="6" fill="#7C6C50" {O(3)}/>')
    # gola polo e botões
    c.append(f'<path d="M176 298 L200 330 L224 298 L240 306 L224 336 L200 324 L176 336 L160 306 Z" fill="{escurecer(polo, 0.85)}" {O(3)}/>')
    c.append(f'<path d="M200 326 V380" stroke="{escurecer(polo, 0.7)}" stroke-width="3"/>')
    c.append(f'<circle cx="200" cy="346" r="3" fill="#FFF"/><circle cx="200" cy="366" r="3" fill="#FFF"/>')
    c.append(logo(226, 352, 42, "#FFFFFF"))
    c.append(f'<rect x="104" y="534" width="192" height="16" rx="5" fill="#3B2F22" {O(3)}/>')
    # braço esquerdo segura o leitor de código de barras
    c.append(
        f'<g id="leitor"><path d="M40 520 L104 506 Q118 504 118 518 L116 534 Q114 544 102 544 L86 546 L80 586 '
        f'Q78 594 70 592 L62 590 Q56 588 58 580 L64 548 L46 550 Q36 548 36 538 Z" fill="#F2C230" {O()}/>'
        f'<path d="M40 520 L58 516 L60 548 L46 550 Q36 548 36 538 Z" fill="#33393F"/><rect x="74" y="516" width="26" height="14" rx="3" fill="#33393F"/>'
        f'<path d="M38 528 L4 520 M38 534 L6 540" stroke="#FF3B3B" stroke-width="3" opacity="0.8"/></g>'
    )
    c.append(braco("braco-esq", pele, BRACO_ESQ, polo, 0.42))
    c.append(braco("braco-dir", pele, BRACO_DIR, polo, 0.42, relogio=("#2B2B2B", "#9AD7B4")))
    c.append('<g id="cabeca">' + cabeca(pele))
    # cabelo nas laterais por baixo do boné
    c.append(
        f'<path d="M110 150 Q104 210 120 236 L128 160 Z M290 150 Q298 200 284 226 L274 158 Z" fill="{cabelo}" {O(3)}/>'
    )
    c.append(olhos(iris="#3A2416", sobrancelha=cabelo, cilios=True, esp_sob=6))
    c.append(boca(labio="#8E3B3B"))
    # boné
    c.append(
        f'<g id="bone"><path d="M108 148 C108 64 292 64 292 148 Z" fill="{polo}" {O()}/>'
        f'<path d="M200 90 V138" stroke="{escurecer(polo, 0.85)}" stroke-width="4"/>'
        f'<ellipse cx="200" cy="150" rx="104" ry="16" fill="{escurecer(polo, 0.8)}" {O()}/>'
        f"{logo(178, 96, 44, '#FFFFFF')}</g>"
    )
    c.append("</g>")
    return svg("luana-estoquista", "Luana — Estoquista", c)


def caio():
    pele = "#F6D3B8"
    camiseta = "#141619"
    cabelo = "#3A281C"
    c = [sombra(), calca("#3D5A80"), sapatos("#F4F6F8", sola="#D0D6DC"), pescoco(pele), tronco(camiseta, ombro=-6)]
    c.append('<path d="M112 618 L124 604 M276 700 L288 690" stroke="#2C4462" stroke-width="4"/>')
    # listras verdes no tênis
    c.append(f'<path d="M126 840 L150 832 M228 840 L252 832" stroke="{VERDE}" stroke-width="6"/>')
    # gola
    c.append(f'<path d="M172 300 Q200 330 228 300" fill="none" stroke="#2A2E33" stroke-width="10"/>')
    c.append(logo(134, 376, 132, "#FFFFFF", "logotipo"))
    c.append(braco("braco-esq", pele, BRACO_ESQ, camiseta, 0.44))
    c.append(braco("braco-dir", pele, BRACO_DIR, camiseta, 0.44, relogio=("#111111", "#2B7BB9")))
    sardas = "".join(
        f'<circle cx="{x}" cy="{y}" r="2.2" fill="#C98A64" opacity="0.7"/>'
        for x, y in ((140, 210), (150, 216), (146, 204), (254, 210), (260, 202), (250, 216))
    )
    c.append('<g id="cabeca">' + cabeca(pele, sardas))
    # cabelo bagunçado
    c.append(
        f'<path id="cabelo" d="M114 168 C96 130 112 96 140 94 C138 70 170 58 190 74 C204 50 240 56 246 80 '
        f'C272 72 300 98 286 126 C300 140 292 162 286 170 C274 140 250 128 232 132 C226 118 212 116 204 128 '
        f'C188 116 168 122 162 136 C146 128 122 140 114 168 Z" fill="{cabelo}" {O()}/>'
    )
    c.append(f'<path d="M196 76 Q212 52 232 62" fill="none" stroke="{cabelo}" stroke-width="8"/>')
    c.append(olhos(iris="#5A7FA8", sobrancelha=cabelo, sob_y=-4))
    c.append(boca())
    # óculos redondos grandes
    c.append(
        f'<g id="oculos" fill="#FFFFFF" fill-opacity="0.15" stroke="#111" stroke-width="7">'
        f'<circle cx="166" cy="188" r="25"/><circle cx="234" cy="188" r="25"/>'
        f'<path d="M191 186 Q200 178 209 186 M141 184 L118 178 M259 184 L282 178" fill="none"/></g>'
    )
    # headset
    c.append(
        f'<g id="headset"><path d="M110 186 C100 50 300 50 290 186" fill="none" stroke="#222" stroke-width="12"/>'
        f'<rect x="96" y="166" width="26" height="50" rx="12" fill="#2A2A2A" {O(3)}/>'
        f'<rect x="278" y="166" width="26" height="50" rx="12" fill="#2A2A2A" {O(3)}/>'
        f'<path d="M110 212 Q118 250 166 246" fill="none" stroke="#222" stroke-width="6"/>'
        f'<rect x="162" y="239" width="18" height="12" rx="6" fill="{VERDE}" {O(2)}/></g>'
    )
    c.append("</g>")
    return svg("caio-suporte", "Caio — Suporte técnico", c)


def antonio():
    pele = "#F0BFA0"
    branco = "#ECEDEF"
    defs = (
        '<pattern id="xadrez" width="36" height="36" patternUnits="userSpaceOnUse">'
        '<rect width="36" height="36" fill="#B23A35"/>'
        '<rect x="0" y="12" width="36" height="12" fill="#F3E3C3" opacity="0.55"/>'
        '<rect x="12" y="0" width="12" height="36" fill="#F3E3C3" opacity="0.55"/>'
        '<path d="M0 18 H36 M18 0 V36" stroke="#6E1E1B" stroke-width="2"/></pattern>'
    )
    c = [sombra(), calca("#A89272"), sapatos("#5B3A22", sola="#3A2416"), pescoco(pele), tronco("url(#xadrez)", barriga=22)]
    c.append(f'<path d="M176 298 L190 316 L172 336 L160 306 Z M224 298 L210 316 L228 336 L240 306 Z" fill="#B23A35" {O(3)}/>')
    c.append(f'<path d="M200 318 V560" stroke="#6E1E1B" stroke-width="3"/>')
    for y in (350, 400, 450, 500):
        c.append(f'<circle cx="207" cy="{y}" r="3.5" fill="#F3E3C3" {O(2)}/>')
    c.append(f'<path d="M90 548 Q200 572 310 548 L308 566 Q200 588 92 566 Z" fill="#4A2E1A" {O(3)}/>')
    c.append(f'<rect x="188" y="556" width="24" height="20" rx="4" fill="#C8A24A" {O(3)}/>')
    c.append(braco("braco-esq", pele, BRACO_ESQ, "url(#xadrez)", 0.44))
    c.append(braco("braco-dir", pele, BRACO_DIR, "url(#xadrez)", 0.44))
    rugas = (
        f'<path d="M160 128 Q200 120 240 128 M168 140 Q200 134 232 140" fill="none" stroke="{escurecer(pele, 0.78)}" stroke-width="3"/>'
        f'<path d="M144 194 l-8 4 M256 194 l8 4" stroke="{escurecer(pele, 0.75)}" stroke-width="3"/>'
        '<ellipse cx="176" cy="112" rx="26" ry="10" fill="#FFF" opacity="0.35" transform="rotate(-15 176 112)"/>'
    )
    c.append('<g id="cabeca">' + cabeca(pele, rugas))
    # cabelo branco nas laterais
    c.append(
        f'<path d="M114 196 C100 160 112 128 132 118 C130 142 128 160 130 190 Z '
        f'M286 196 C300 160 288 128 268 118 C270 142 272 160 270 190 Z" fill="{branco}" {O(3)}/>'
    )
    c.append(olhos(iris="#5C7F9C", sobrancelha=branco, esp_sob=10))
    c.append(boca())
    # bigodão branco
    c.append(
        f'<path id="bigode" d="M160 232 Q170 204 200 214 Q230 204 240 232 Q222 222 200 228 Q178 222 160 232 Z" '
        f'fill="{branco}" {O(3)}/>'
    )
    c.append("</g>")
    return svg("seu-antonio-cliente", "Seu Antônio — Cliente", c, defs)


def fernanda():
    pele = "#6B4226"
    blusa = "#F4B942"
    saia = "#2A9D8F"
    cabelo = "#1E1410"
    import math

    cachos = []
    for i in range(22):
        a = 2 * math.pi * i / 22
        x = 200 + 122 * math.cos(a)
        y = 168 + 112 * math.sin(a)
        if y > 250:
            continue
        cachos.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="34"/>')
    c = [sombra()]
    c.append(
        f'<g id="cabelo-volume" fill="{cabelo}" {O()}>{"".join(cachos)}</g>'
        f'<ellipse cx="200" cy="168" rx="124" ry="110" fill="{cabelo}"/>'
    )
    # pernas, tênis e saia
    c.append(f'<rect x="146" y="680" width="44" height="160" rx="18" fill="{pele}" {O()}/>')
    c.append(f'<rect x="210" y="680" width="44" height="160" rx="18" fill="{pele}" {O()}/>')
    c.append(sapatos("#FFFFFF", sola="#E2E6EA", bico=None))
    c.append(f'<path d="M126 836 L150 830 M228 836 L252 830" stroke="#E76F51" stroke-width="6"/>')
    c.append(pescoco(pele))
    c.append(tronco(blusa, ombro=-8))
    c.append(f'<path id="saia" d="M106 536 H294 L320 740 Q200 758 80 740 Z" fill="{saia}" {O()}/>')
    c.append(f'<path d="M150 560 L136 740 M200 560 V748 M250 560 L264 740" stroke="{escurecer(saia, 0.8)}" stroke-width="3"/>')
    c.append(f'<path d="M168 300 Q200 340 232 300" fill="{escurecer(blusa, 0.9)}" {O(3)}/>')
    # colar
    c.append(f'<path d="M178 302 Q200 330 222 302" fill="none" stroke="#D4A537" stroke-width="3"/>')
    c.append(braco("braco-esq", pele, BRACO_ESQ, blusa, 0.4))
    # braço direito dobrado segurando o celular na frente do corpo
    pontos = ((290, 338), (330, 470), (262, 462))
    c.append(braco("braco-dir", pele, pontos, blusa, 0.36, relogio=("#D4A537", "#FFF6E0")))
    c.append(
        f'<g id="celular"><rect x="232" y="404" width="40" height="70" rx="8" fill="#20252B" {O(3)}/>'
        f'<rect x="237" y="412" width="30" height="52" rx="3" fill="{AZUL}"/>'
        f'<rect x="240" y="416" width="24" height="16" rx="2" fill="#9FD3F5"/>'
        f'<rect x="240" y="436" width="11" height="10" rx="2" fill="#9FD3F5"/>'
        f'<rect x="253" y="436" width="11" height="10" rx="2" fill="#9FD3F5"/></g>'
    )
    c.append(f'<circle cx="262" cy="474" r="23" fill="{pele}" {O()}/>')
    c.append(f'<ellipse cx="244" cy="452" rx="9" ry="13" fill="{pele}" {O(3)}/>')
    c.append('<g id="cabeca">' + cabeca(pele))
    # franja de cachos
    franja = "".join(
        f'<circle cx="{x}" cy="{y}" r="{r}"/>'
        for x, y, r in ((132, 112, 26), (162, 92, 28), (200, 84, 30), (238, 92, 28), (268, 112, 26))
    )
    c.append(f'<g id="franja" fill="{cabelo}" {O()}>{franja}</g>')
    c.append(f'<ellipse cx="200" cy="112" rx="84" ry="24" fill="{cabelo}"/>')
    c.append(olhos(iris="#2A1A10", sobrancelha=cabelo, cilios=True, esp_sob=6))
    c.append(boca(labio="#5A2228"))
    # brincos de argola
    c.append('<circle cx="112" cy="226" r="13" fill="none" stroke="#D4A537" stroke-width="5"/>')
    c.append('<circle cx="288" cy="226" r="13" fill="none" stroke="#D4A537" stroke-width="5"/>')
    c.append("</g>")
    return svg("fernanda-cliente", "Fernanda — Cliente", c)


PERSONAGENS = {
    "marcao-instalador": marcao,
    "rodrigo-vendedor": rodrigo,
    "luana-estoquista": luana,
    "caio-suporte": caio,
    "seu-antonio-cliente": antonio,
    "fernanda-cliente": fernanda,
}


def folha():
    """Página de revisão com todos os personagens lado a lado."""
    import html
    import json

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
