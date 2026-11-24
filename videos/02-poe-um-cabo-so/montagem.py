"""Vídeo 02 — "PoE: um cabo só, imagem e energia" (Reels, ~1 min).

Caio, do suporte técnico, explica ao Marcão como funciona o PoE usando o switch HAIZ HZ-1006P-EA2.

Uso:
    python videos/02-poe-um-cabo-so/montagem.py                 # gera saida/02-poe-um-cabo-so/video.mp4
    python videos/02-poe-um-cabo-so/montagem.py --quadros 2,15,40   # só salva esses quadros em PNG (revisão)

As falas ficam em saida/02-poe-um-cabo-so/audio/fNN.mp3 (geradas no ElevenLabs com o 'texto' do roteiro.json).
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

PASTA = Path(__file__).resolve().parent
RAIZ = PASTA.parents[1]
sys.path.insert(0, str(RAIZ / "ferramentas"))
import gerar_cenarios as gc  # noqa: E402
import video as V  # noqa: E402
from video import FPS, LARG, ALT, SR, Camera, AtorNaCena, fonte, colar, pop, suave  # noqa: E402

SLUG = PASTA.name
SAIDA = RAIZ / "saida" / SLUG
CACHE = SAIDA / "cache"
ROTEIRO = json.loads((PASTA / "roteiro.json").read_text(encoding="utf-8"))
FALAS = ROTEIRO["falas"]

VERDE, AZUL_ESCURO, AMARELO, VERMELHO = (31, 174, 90), (34, 55, 75), (242, 194, 48), (226, 59, 48)
LARANJA, AZUL, CINZA = (242, 140, 40), (43, 123, 185), (90, 96, 104)
NOMES = {
    "marcao-instalador": ("MARCÃO", LARANJA),
    "caio-suporte": ("CAIO • SUPORTE", AZUL),
}

# ------------------------------------------------------------------ switch HAIZ HZ-1006P-EA2 (2D, a partir da ficha técnica)
SW_W, SW_H = 1060, 250
SW_POE = [400 + k * 88 for k in range(4)]       # x das 4 portas PoE (largura 76)
SW_UP = [846, 934]                               # x das 2 portas uplink
SW_EXT = 784                                     # centro da chave Extend
SW_PORTA_Y, SW_PORTA_H = 104, 64


def _porta(x, y):
    return (gc.R(x, y, 76, SW_PORTA_H, "#F4F6F8", 6, "#C9D3DD", 2)
            + gc.P(f"M{x + 12} {y + 14} H{x + 64} V{y + 44} H{x + 50} V{y + 54} H{x + 26} V{y + 44} H{x + 12} Z", "#1A1C1F"))


def switch_svg() -> str:
    c = [gc.R(0, 0, SW_W, SW_H, "#2B2F35", 16),
         gc.R(14, 14, SW_W - 28, SW_H - 28, "#F28C28", 8),
         gc.P(f"M470 14 H{SW_W - 14} V{SW_H - 14} H330 Z", "#141518"),
         gc.texto(48, 74, "HAIZ", 52, "#FFFFFF", 900, "start"),
         gc.texto(48, 116, "PoE Switch", 22, "#FFFFFF", 600, "start"),
         gc.texto(48, 144, "4POE 10/100Mbps", 20, "#FFFFFF", 600, "start"),
         gc.texto(48, 170, "2UPLINK 100Mbps", 20, "#FFFFFF", 600, "start"),
         gc.P(f"M{SW_POE[0]} 86 V78 H{SW_POE[3] + 76} V86", "none", "#F28C28", 3),
         gc.texto((SW_POE[0] + SW_POE[3] + 76) / 2, 72, "POE", 22, "#F28C28", 800),
         gc.P(f"M{SW_UP[0]} 86 V78 H{SW_UP[1] + 76} V86", "none", "#F28C28", 3),
         gc.texto((SW_UP[0] + SW_UP[1] + 76) / 2, 72, "UPLINK", 22, "#F28C28", 800),
         gc.texto(SW_EXT, 110, "OFF/ON", 16, "#FFFFFF", 700),
         gc.R(SW_EXT - 18, 120, 36, 46, "#3A3E44", 6, "#9AA5B1", 2),
         gc.texto(SW_EXT, 214, "Extend", 18, "#FFFFFF", 700),
         gc.texto(SW_W - 70, 214, "POWER", 16, "#FFFFFF", 700)]
    for k, x in enumerate(SW_POE + SW_UP):
        c.append(_porta(x, SW_PORTA_Y))
        c.append(f'<circle cx="{x + 14}" cy="196" r="6" fill="#5A5F66"/>')
        c.append(gc.texto(x + 50, 203, str(k + 1), 20, "#FFFFFF", 700))
    c.append(f'<circle cx="{SW_W - 70}" cy="190" r="7" fill="#1FAE5A"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SW_W} {SW_H}" width="{SW_W}" height="{SW_H}">'
            f'<g stroke-linejoin="round" stroke-linecap="round">{"".join(c)}</g></svg>')


def camera_svg() -> str:
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 140" width="200" height="140">'
            + gc.camera_bullet(100, 60, 1.6, led=True) + "</svg>")


# ------------------------------------------------------------------ áudio e tempos
def sem_tags(t: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"\[[^\]]*\]", "", t)).strip()


AUDIOS = [V.ler_audio(SAIDA / "audio" / f"{f['id']}.mp3") for f in FALAS]
ENVS = [V.envelope(a) for a in AUDIOS]
DURS = [len(a) / SR for a in AUDIOS]
INI = []
_t = 0.45
for i, f in enumerate(FALAS):
    if i and f["cena"] != FALAS[i - 1]["cena"]:
        _t += 0.55
    INI.append(_t)
    _t += DURS[i] + 0.12
FIM_FALAS = _t
DUR = FIM_FALAS + 3.2
CORTE_SUP = INI[1] - 0.3
CORTE_CAMPO2 = INI[9] - 0.3
CORTE_SUP2 = INI[10] - 0.3
CORTES = (CORTE_SUP, CORTE_CAMPO2, CORTE_SUP2)


def nivel(i: int, t: float):
    if INI[i] <= t < INI[i] + DURS[i]:
        e = ENVS[i]
        return float(e[min(len(e) - 1, int((t - INI[i]) * FPS))])
    return None


def falando(i: int, t: float) -> bool:
    return INI[i] - 0.05 <= t < (INI[i + 1] if i + 1 < len(INI) else FIM_FALAS)


# ------------------------------------------------------------------ cartões
def base_cartao(w: int, h: int, cor, raio=38, borda=None, larg_borda=8):
    im = Image.new("RGBA", (w + 40, h + 46), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((24, 32, w + 24, h + 32), raio, fill=(0, 0, 0, 70))
    d.rounded_rectangle((20, 20, w + 20, h + 20), raio, fill=cor, outline=borda, width=larg_borda if borda else 0)
    return im, d


def icone_ok(d, cx, cy, r=46, cor=VERDE):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=cor)
    d.line((cx - r * 0.45, cy + 2, cx - r * 0.1, cy + r * 0.35, cx + r * 0.5, cy - r * 0.35), fill="white",
           width=max(6, int(r / 4)), joint="curve")


def icone_alerta(d, cx, cy, r=46):
    d.polygon([(cx, cy - r), (cx + r * 1.1, cy + r * 0.85), (cx - r * 1.1, cy + r * 0.85)], fill=AMARELO)
    d.text((cx, cy + r * 0.2), "!", font=fonte(int(r * 1.2)), fill=(20, 20, 20), anchor="mm")


def raio_icone(d, cx, cy, s=1.0, cor=AMARELO):
    pts = [(4, -30), (-14, 4), (0, 4), (-6, 30), (14, -6), (0, -6), (6, -30)]
    d.polygon([(cx + x * s, cy + y * s) for x, y in pts], fill=cor, outline=(20, 20, 20), width=3)


def banner(linhas, fundo, cor_txt=(20, 20, 20), tam=86, larg=920, giro=-2.5):
    while max(fonte(tam).getlength(l) for l in linhas) > larg - 90:
        tam -= 2
    fnt = fonte(tam)
    h = 60 + len(linhas) * (tam + 16)
    im, d = base_cartao(larg, h, fundo, 34)
    for k, l in enumerate(linhas):
        d.text((20 + larg / 2, 20 + 36 + k * (tam + 16) + tam / 2), l, font=fnt, fill=cor_txt, anchor="mm")
    return im.rotate(giro, resample=Image.BICUBIC, expand=True)


def ligando():
    w, h = 900, 210
    im, d = base_cartao(w, h, (24, 26, 30), 40)
    d.ellipse((20 + 50, 20 + 55, 20 + 150, 20 + 155), fill=VERDE)
    # fone
    d.arc((20 + 72, 20 + 76, 20 + 128, 20 + 134), 120, 330, fill="white", width=14)
    d.text((20 + 190, 20 + 78), "Ligando...", font=fonte(64), fill="white", anchor="lm")
    d.text((20 + 190, 20 + 150), "Suporte técnico Protemaxxi", font=fonte(40, "bold"), fill=(190, 196, 204), anchor="lm")
    return im


def tudo_ligado():
    w, h = 900, 210
    im, d = base_cartao(w, h, (24, 26, 30), 40)
    d.ellipse((20 + 60, 20 + 65, 20 + 140, 20 + 145), fill=VERMELHO)
    d.text((20 + 190, 20 + 78), "4 CÂMERAS NO AR", font=fonte(60), fill="white", anchor="lm")
    d.text((20 + 190, 20 + 150), "Um cabo de rede em cada uma", font=fonte(40, "bold"), fill=(190, 196, 204), anchor="lm")
    return im


def cartao_final(logo: Image.Image):
    im = Image.new("RGBA", (LARG, ALT), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, LARG, ALT), fill=(16, 26, 36, 228))
    colar(im, logo, LARG / 2, 500)
    d.rounded_rectangle((90, 740, LARG - 90, 1200), 44, fill=(255, 255, 255))
    d.text((LARG / 2, 840), "PoE: UM CABO SÓ.", font=fonte(64), fill=AZUL_ESCURO, anchor="mm")
    d.text((LARG / 2, 940), "IMAGEM + ENERGIA.", font=fonte(64), fill=VERDE, anchor="mm")
    d.text((LARG / 2, 1060), "Exemplo: switch HAIZ HZ-1006P-EA2", font=fonte(40, "bold"), fill=CINZA, anchor="mm")
    d.text((LARG / 2, 1120), "4 portas PoE • 2 uplink • Extend 250 m", font=fonte(36, "bold"), fill=CINZA, anchor="mm")
    d.rounded_rectangle((110, 1280, LARG - 110, 1400), 60, fill=AMARELO)
    d.text((LARG / 2, 1340), "Salva e marca seu parceiro instalador", font=fonte(42), fill=(20, 20, 20), anchor="mm")
    return im


# ------------------------------------------------------------------ painéis animados (desenhados a cada quadro)
PW, PH = 1000, 700            # tamanho do painel (px de saída)
PAINEL_CY = 470               # centro vertical do painel na tela


def pontos_no_cabo(d, p0, p1, t, cor, sentido=1, passo=48, r=9, vel=160):
    """Bolinhas andando de p0 para p1 (sentido 1) ou de p1 para p0 (-1)."""
    (x0, y0), (x1, y1) = p0, p1
    comp = float(np.hypot(x1 - x0, y1 - y0))
    off = (t * vel) % passo
    s = off
    while s < comp:
        u = s / comp if sentido > 0 else 1 - s / comp
        x, y = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
        d.ellipse((x - r, y - r, x + r, y + r), fill=cor, outline=(20, 20, 20), width=2)
        s += passo


def cabo(d, p0, p1, larg=16, cor=(43, 123, 185)):
    d.line((*p0, *p1), fill=(20, 20, 20), width=larg + 6)
    d.line((*p0, *p1), fill=cor, width=larg)


def fundo_painel(titulo: str, cor=AZUL_ESCURO):
    im, d = base_cartao(PW, PH, (255, 255, 255), 40)
    d.rounded_rectangle((20, 20, 20 + PW, 20 + 96), 40, fill=cor)
    d.rectangle((20, 76, 20 + PW, 20 + 96), fill=cor)
    tam = 52
    while fonte(tam).getlength(titulo) > PW - 60:
        tam -= 2
    d.text((20 + PW / 2, 20 + 50), titulo, font=fonte(tam), fill="white", anchor="mm")
    return im, d


class Paineis:
    def __init__(self, sw: Image.Image, cam: Image.Image):
        self.sw = sw                       # switch rasterizado em largura 940
        self.esc = sw.width / SW_W
        self.cam = cam                     # câmera 200x140
        self.cam_peq = cam.resize((180, 126), Image.LANCZOS)

    # --- f03/f04: um cabo leva imagem e energia
    def um_cabo(self, t: float) -> Image.Image:
        im, d = fundo_painel("1 CABO DE REDE = IMAGEM + ENERGIA")
        sw_peq = self.sw.resize((360, round(360 * SW_H / SW_W)), Image.LANCZOS)
        im.alpha_composite(sw_peq, (20 + 40, 20 + 170))
        colar(im, self.cam, 20 + 830, 20 + 210, 1.0)
        a, b = (20 + 400, 20 + 214), (20 + 740, 20 + 214)
        cabo(d, a, b, 26)
        pontos_no_cabo(d, (a[0], a[1] - 6), (b[0], b[1] - 6), t, AMARELO, 1, r=8)
        pontos_no_cabo(d, (a[0] + 24, a[1] + 6), (b[0], b[1] + 6), t, VERDE, -1, r=8)
        raio_icone(d, 20 + 470, 20 + 300, 1.1)
        d.text((20 + 500, 20 + 300), "ENERGIA →", font=fonte(36), fill=(150, 110, 0), anchor="lm")
        d.ellipse((20 + 452, 20 + 352, 20 + 488, 20 + 388), fill=VERDE, outline=(20, 20, 20), width=2)
        d.text((20 + 500, 20 + 370), "← IMAGEM", font=fonte(36), fill=(20, 130, 65), anchor="lm")
        # vantagens aparecem durante a f04
        itens = ["Sem fonte em cada câmera", "Sem tomada lá no alto", "Um cabo só e pronto"]
        for k, txt in enumerate(itens):
            ent = INI[3] + k * DURS[3] / 3
            if t >= ent:
                s = pop((t - ent) / 0.25)
                y = 20 + 470 + k * 74
                icone_ok(d, 20 + 90, y, 26 * s)
                d.text((20 + 135, y), txt, font=fonte(44, "bold"), fill=(25, 25, 25), anchor="lm")
        if t < INI[3]:
            d.text((20 + PW / 2, 20 + 540), "Os dois vão juntos,", font=fonte(44, "bold"), fill=CINZA, anchor="mm")
            d.text((20 + PW / 2, 20 + 600), "no mesmo cabo.", font=fonte(44, "bold"), fill=CINZA, anchor="mm")
        return im

    # --- f05..f09: o switch e seus recursos
    def _sw_xy(self, x_sw, y_sw, ox, oy):
        return ox + x_sw * self.esc, oy + y_sw * self.esc

    def switch(self, t: float) -> Image.Image:
        im, d = fundo_painel("SWITCH HAIZ HZ-1006P-EA2", LARANJA)
        ox, oy = 20 + 30, 20 + 160
        d.text((20 + PW / 2, 20 + 130), "Fast Ethernet 10/100 • comutação 1,6 Gbps",
               font=fonte(34, "bold"), fill=CINZA, anchor="mm")
        im.alpha_composite(self.sw, (round(ox), round(oy)))
        passo = 0
        for k in range(4):
            if t >= INI[5 + k] - 0.05:
                passo = k + 1
        y_cabo = oy + (SW_PORTA_Y + SW_PORTA_H) * self.esc
        base_y = 20 + 450

        def destaque(x_sw, w_sw, cor=AMARELO, y_sw=SW_PORTA_Y - 8, h_sw=SW_PORTA_H + 16):
            x0, y0 = self._sw_xy(x_sw - 8, y_sw, ox, oy)
            x1, y1 = self._sw_xy(x_sw + w_sw + 8, y_sw + h_sw, ox, oy)
            pulso = 6 + 3 * np.sin(t * 8)
            d.rounded_rectangle((x0, y0, x1, y1), 12, outline=cor, width=int(pulso))

        if passo in (0, 1, 2):
            # 4 câmeras ligadas às portas PoE
            xs_cam = [20 + 100, 20 + 270, 20 + 440, 20 + 610] if passo == 2 else [20 + 140, 20 + 380, 20 + 620, 20 + 860]
            for k, xc in enumerate(xs_cam):
                ent = INI[5] + 0.6 + k * 0.7 if passo >= 1 else 1e9
                if t < ent:
                    continue
                xp, _ = self._sw_xy(SW_POE[k] + 38, 0, ox, oy)
                p0, p1 = (xp, y_cabo), (xc, base_y + 40)
                cabo(d, p0, p1, 12)
                pontos_no_cabo(d, p0, p1, t, AMARELO, 1, passo=60, r=7)
                pontos_no_cabo(d, (p0[0] + 4, p0[1] + 30), p1, t + 0.15, VERDE, -1, passo=60, r=7)
                colar(im, self.cam_peq, xc, base_y + 70, pop((t - ent) / 0.3))
                # LED da porta acende
                lx, ly = self._sw_xy(SW_POE[k] + 14, 196, ox, oy)
                d.ellipse((lx - 8, ly - 8, lx + 8, ly + 8), fill=(80, 255, 120))
                d.text((xc, base_y + 150), f"CÂM {k + 1}", font=fonte(30), fill=AZUL_ESCURO, anchor="mm")
            if passo == 1:
                destaque(SW_POE[0], SW_POE[3] + 76 - SW_POE[0])
                d.text((20 + PW / 2, 20 + 660), "Cada porta: energia + imagem", font=fonte(40), fill=(20, 20, 20), anchor="mm")
            if passo == 2:
                destaque(SW_UP[0], SW_UP[1] + 76 - SW_UP[0], VERDE)
                uplinks = [(j, nome, cor, INI[6] + 0.3 + j * 0.8, base_y + 30 + j * 110)
                           for j, (nome, cor) in enumerate((("GRAVADOR", AZUL_ESCURO), ("REDE", AZUL)))
                           if t >= INI[6] + 0.3 + j * 0.8]
                for j, *_r, yb in uplinks:   # cabos primeiro, etiquetas por cima
                    xp, _ = self._sw_xy(SW_UP[j] + 38, 0, ox, oy)
                    cabo(d, (xp, y_cabo), (xp, yb), 12, VERDE)
                for j, nome, cor, ent, yb in uplinks:
                    s = pop((t - ent) / 0.3)
                    fn = fonte(int(34 * s) or 1)
                    wl = fn.getlength(nome) + 36
                    d.rounded_rectangle((20 + 880 - wl / 2, yb - 30 * s, 20 + 880 + wl / 2, yb + 30 * s), 24, fill=cor)
                    d.text((20 + 880, yb), nome, font=fn, fill="white", anchor="mm")
                d.text((20 + PW / 2, 20 + 660), "Uplink: liga no gravador e na rede", font=fonte(40), fill=(20, 20, 20),
                       anchor="mm")
        elif passo == 3:
            # chave Extend liga e a distância cresce
            ligado = t >= INI[7] + 1.4
            x0, y0 = self._sw_xy(SW_EXT - 18, 120, ox, oy)
            x1, y1 = self._sw_xy(SW_EXT + 18, 166, ox, oy)
            ym = (y0 + y1) / 2
            d.rounded_rectangle((x0 + 3, (y0 if ligado else ym) + 3, x1 - 3, (ym if ligado else y1) - 3), 4,
                                fill=VERDE if ligado else (200, 200, 200))
            destaque(SW_EXT - 26, 52, AMARELO, 96, 130)
            yb = base_y + 30
            d.text((20 + 60, yb), "Padrão", font=fonte(38, "bold"), fill=CINZA, anchor="lm")
            larg_max = 470
            d.rounded_rectangle((20 + 300, yb - 26, 20 + 300 + larg_max * 100 / 250, yb + 26), 26, fill=(200, 205, 212))
            d.text((20 + 300 + larg_max * 100 / 250 + 20, yb), "100 m", font=fonte(44), fill=CINZA, anchor="lm")
            yb2 = yb + 120
            d.text((20 + 60, yb2), "Extend ON", font=fonte(38), fill=VERDE, anchor="lm")
            k = suave((t - (INI[7] + 1.4)) / 1.2) if ligado else 0.0
            wbar = larg_max * (100 + 150 * k) / 250
            d.rounded_rectangle((20 + 300, yb2 - 30, 20 + 300 + wbar, yb2 + 30), 30, fill=VERDE)
            metros = round(100 + 150 * k)
            d.text((20 + 300 + wbar + 20, yb2), f"{metros} m", font=fonte(54), fill=VERDE, anchor="lm")
            d.text((20 + PW / 2, 20 + 660), "Câmera longe do switch? Liga o Extend.", font=fonte(38), fill=(20, 20, 20),
                   anchor="mm")
        else:
            itens = [("ok", "Plug and play: sem configurar nada"), ("!", "Confira se a câmera é PoE")]
            for k, (tipo, txt) in enumerate(itens):
                ent = INI[8] + (0.2 if k == 0 else DURS[8] * 0.55)
                if t < ent:
                    continue
                s = pop((t - ent) / 0.28)
                y = base_y + 40 + k * 120
                (icone_ok if tipo == "ok" else icone_alerta)(d, 20 + 90, y, 36 * s)
                d.text((20 + 150, y), txt, font=fonte(46, "bold"), fill=(25, 25, 25), anchor="lm")
        return im


# ------------------------------------------------------------------ legendas
def legenda_chunks(i: int):
    """Divide a fala (texto de legenda) em pedaços de até 4 palavras, distribuídos pelo tempo da fala."""
    palavras = (FALAS[i].get("legenda") or sem_tags(FALAS[i]["texto"])).split()
    pedacos = [" ".join(palavras[k:k + 4]) for k in range(0, len(palavras), 4)]
    total = sum(len(p) for p in pedacos)
    t, out = INI[i], []
    for p in pedacos:
        d = DURS[i] * len(p) / total
        out.append((t, t + d, p))
        t += d
    return out


def desenhar_legenda(img: Image.Image, t: float):
    for i, f in enumerate(FALAS):
        if INI[i] - 0.05 <= t < INI[i] + DURS[i] + 0.1:
            nome, cor = NOMES[f["personagem"]]
            d = ImageDraw.Draw(img)
            fn = fonte(38)
            wn = fn.getlength(nome) + 50
            d.rounded_rectangle((LARG / 2 - wn / 2, 1318, LARG / 2 + wn / 2, 1376), 29, fill=cor)
            d.text((LARG / 2, 1347), nome, font=fn, fill="white", anchor="mm")
            pedacos = legenda_chunks(i)
            for a, b, txt in pedacos:
                if a <= t < b or (txt == pedacos[-1][2] and t >= a):
                    fnt = fonte(74)
                    linhas = V.texto_quebrado(txt.upper(), fnt, 960)
                    for k, l in enumerate(linhas):
                        d.text((LARG / 2, 1450 + k * 88), l, font=fnt, fill="white", anchor="mm",
                               stroke_width=10, stroke_fill=(15, 15, 15))
                    break
            return


# ------------------------------------------------------------------ montagem
def preparar():
    print("Rasterizando cenários, personagens e o switch (com cache)...")
    campo = V.carregar_cenario(gc.campo_instalador(), CACHE)
    suporte = V.carregar_cenario(gc.suporte_tecnico(), CACHE)
    atores = {
        "marcao": V.Ator("marcao-instalador", 540, CACHE, boca_parada="fechada"),
        "caio": V.Ator("caio-suporte", 600, CACHE),
    }
    logo_svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 591 150" width="591" height="150">'
                f'<path fill="#FFFFFF" fill-rule="evenodd" d="{gc.LOGO_D}"/></svg>')
    logo = V.rasterizar(logo_svg, 820, 208, CACHE)
    sw = V.rasterizar(switch_svg(), 940, round(940 * SW_H / SW_W), CACHE)
    cam = V.rasterizar(camera_svg(), 200, 140, CACHE)
    return campo, suporte, atores, logo, Paineis(sw, cam)


CAIO_X, CAIO_PE = 1180, 1060
MARCAO_X, MARCAO_PE = 1480, 1010


def roteiro_cenas(campo, suporte, A):
    cam_campo1 = [(0.0, Camera(MARCAO_X, 560, 1.5)), (INI[0] + 2.5, Camera(MARCAO_X - 40, 620, 1.3))]
    cam_sup = [(CORTE_SUP, Camera(CAIO_X, 560, 1.35)), (INI[2] - 0.2, Camera(CAIO_X, 540, 1.0))]
    cam_campo2 = [(CORTE_CAMPO2, Camera(MARCAO_X, 560, 1.4))]
    cam_sup2 = [(CORTE_SUP2, Camera(CAIO_X, 560, 1.35)), (INI[10] + 2.0, Camera(CAIO_X, 520, 1.15))]

    def estado(t: float):
        if t < CORTE_SUP:
            tremor = 4 * np.sin(t * 30) if nivel(0, t) is not None else 0.0
            return campo, V.interpolar_camera(cam_campo1, t), [AtorNaCena(A["marcao"], MARCAO_X, MARCAO_PE, nivel(0, t),
                                                                         dx=tremor)]
        if t < CORTE_CAMPO2:
            lv = next((v for v in (nivel(i, t) for i in range(1, 9)) if v is not None), None)
            return suporte, V.interpolar_camera(cam_sup, t), [AtorNaCena(A["caio"], CAIO_X, CAIO_PE, lv)]
        if t < CORTE_SUP2:
            A["marcao"].boca_parada = "aberta"
            pulo = -16 * abs(np.sin((t - INI[9]) * 8)) if nivel(9, t) is not None else 0.0
            return campo, V.interpolar_camera(cam_campo2, t), [AtorNaCena(A["marcao"], MARCAO_X, MARCAO_PE, nivel(9, t),
                                                                         dy=pulo)]
        return suporte, V.interpolar_camera(cam_sup2, t), [AtorNaCena(A["caio"], CAIO_X, CAIO_PE, nivel(10, t))]

    return estado


def lista_cartoes(logo):
    """(entra, sai, imagem, cx, cy). As imagens entram com 'pop' e saem com fade."""
    c = [
        (0.15, INI[0] + DURS[0] * 0.55, banner(["4 CÂMERAS IP", "E NENHUMA TOMADA?"], AMARELO), LARG / 2, 300),
        (INI[0] + DURS[0] * 0.55, CORTE_SUP, ligando(), LARG / 2, 300),
        (CORTE_SUP + 0.25, INI[2] - 0.2, banner(["PoE = POWER", "OVER ETHERNET"], AZUL, (255, 255, 255), 84), LARG / 2, 300),
        (INI[9] + 0.2, CORTE_SUP2, tudo_ligado(), LARG / 2, 300),
        (CORTE_SUP2 + 0.2, FIM_FALAS, banner(["UM CABO SÓ:", "IMAGEM + ENERGIA"], AMARELO, tam=80), LARG / 2, 300),
    ]
    return c, (FIM_FALAS - 0.1, DUR + 1, cartao_final(logo))


def mixar_audio():
    total = np.zeros(int((DUR + 0.5) * SR), dtype=np.float32)

    def por(sinal, t):
        i = int(t * SR)
        total[i:i + len(sinal)] += sinal[: max(0, len(total) - i)]

    for i, a in enumerate(AUDIOS):
        por(a, INI[i])
    for t in CORTES:
        por(V.whoosh(), t - 0.15)
    return total, por


def renderizar(quadros_previa: list[float] | None = None):
    SAIDA.mkdir(parents=True, exist_ok=True)
    campo, suporte, A, logo, P = preparar()
    estado = roteiro_cenas(campo, suporte, A)
    cartoes, (fin_ini, _, fin_img) = lista_cartoes(logo)
    ini_um_cabo, fim_um_cabo = INI[2] - 0.2, INI[4] - 0.05
    ini_switch, fim_switch = INI[4] - 0.05, CORTE_CAMPO2

    def montar(t: float) -> Image.Image:
        cen, cam, atores = estado(t)
        img = V.quadro(cen, cam, atores, t)
        for a, b, im, cx, cy in cartoes:
            if a <= t < b:
                colar(img, im, cx, cy, pop((t - a) / 0.28), min(1.0, (b - t) / 0.18))
        if ini_um_cabo <= t < fim_um_cabo:
            colar(img, P.um_cabo(t), LARG / 2, PAINEL_CY, pop((t - ini_um_cabo) / 0.3), min(1.0, (fim_um_cabo - t) / 0.15))
        if ini_switch <= t < fim_switch:
            colar(img, P.switch(t), LARG / 2, PAINEL_CY, pop((t - ini_switch) / 0.3), min(1.0, (fim_switch - t) / 0.15))
        desenhar_legenda(img, t)
        if t >= fin_ini:
            colar(img, fin_img, LARG / 2, ALT / 2, 1.0, min(1.0, (t - fin_ini) / 0.4))
        for corte in CORTES:
            if corte <= t < corte + 0.15:
                img.alpha_composite(Image.new("RGBA", img.size, (255, 255, 255, int(255 * (1 - (t - corte) / 0.15)))))
        return img

    if quadros_previa:
        for t in quadros_previa:
            p = SAIDA / f"quadro_{t:05.1f}s.png"
            montar(t).convert("RGB").save(p)
            print(p)
        return

    audio, por = mixar_audio()
    entradas = [a for a, *_ in cartoes] + [ini_um_cabo, ini_switch] + [INI[5 + k] + 0.6 + k * 0.7 for k in range(4)]
    for a in entradas:
        por(V.blip(), a)
    wav = SAIDA / "audio_mix.wav"
    V.salvar_wav(audio, wav)

    saida = SAIDA / "video.mp4"
    enc = V.Codificador(saida, wav)
    n = int(DUR * FPS)
    t0 = time.time()
    for i in range(n):
        enc.escrever(montar(i / FPS))
        if i % 150 == 0:
            print(f"  quadro {i}/{n}  ({time.time() - t0:.0f}s)", flush=True)
    enc.fechar()
    print(f"Pronto: {saida}  ({DUR:.1f}s)")


if __name__ == "__main__":
    if "--quadros" in sys.argv:
        ts = [float(x) for x in sys.argv[sys.argv.index("--quadros") + 1].split(",")]
        renderizar(ts)
    else:
        renderizar()
