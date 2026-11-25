"""Vídeo 05 — Erro de instalador #3: infravermelho estourado. Ver ferramentas/fabrica.py para o uso."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ferramentas"))
from fabrica import CORES, base_cartao, produzir, titulo_painel  # noqa: E402
from video import fonte, suave  # noqa: E402

TW, TH = 900, 560   # tela de câmera


def _quintal(boa: bool) -> Image.Image:
    """Imagem noturna em preto e branco de um quintal: portão, muro, árvore e um gato."""
    im = Image.new("RGB", (TW, TH), (52, 56, 58))
    d = ImageDraw.Draw(im)
    d.rectangle((0, TH * 0.62, TW, TH), fill=(86, 90, 92))                    # chão
    d.rectangle((0, TH * 0.28, TW, TH * 0.62), fill=(70, 74, 76))             # muro
    for x in range(40, TW, 120):
        d.line((x, TH * 0.28, x, TH * 0.62), fill=(60, 63, 65), width=4)
    d.rectangle((560, 120, 760, TH * 0.62), fill=(40, 42, 44))                # portão
    for x in range(575, 760, 28):
        d.line((x, 130, x, TH * 0.62 - 6), fill=(120, 124, 126), width=6)
    d.rectangle((150, 150, 175, TH * 0.66), fill=(76, 70, 64))                 # árvore
    d.ellipse((70, 40, 260, 200), fill=(96, 104, 98))
    d.ellipse((380, 380, 470, 440), fill=(150, 152, 150))                      # gato
    d.ellipse((440, 352, 492, 400), fill=(150, 152, 150))
    d.polygon([(446, 360), (452, 336), (462, 356)], fill=(150, 152, 150))
    d.polygon([(472, 356), (484, 334), (488, 360)], fill=(150, 152, 150))
    d.ellipse((456, 368, 466, 378), fill=(240, 240, 200))
    d.ellipse((474, 368, 484, 378), fill=(240, 240, 200))
    if not boa:
        brilho = Image.new("L", (TW, TH), 0)
        ImageDraw.Draw(brilho).ellipse((60, -240, TW - 60, TH * 0.75), fill=235)
        brilho = brilho.filter(ImageFilter.GaussianBlur(90))
        im = Image.composite(Image.new("RGB", (TW, TH), (246, 246, 246)), im, brilho)
    return im


_CACHE = {}


def _tela(titulo, boa, t):
    if boa not in _CACHE:
        _CACHE[boa] = _quintal(boa)
    w, h = TW + 40, TH + 130
    im, d = base_cartao(w, h, (24, 26, 30), 34)
    im.paste(_CACHE[boa], (40, 110))
    cor = CORES["verde"] if boa else CORES["vermelho"]
    d.ellipse((50, 40, 86, 76), fill=CORES["vermelho"] if int(t * 2) % 2 else (120, 30, 30))
    d.text((100, 58), "CAM 1 • IR LIGADO", font=fonte(34), fill="white", anchor="lm")
    d.rounded_rectangle((w - 300, 30, w - 10, 86), 28, fill=cor)
    d.text((w - 155, 58), titulo, font=fonte(32), fill="white", anchor="mm")
    return im


def tela_ruim(v, t, prog):
    return _tela("ESTOURADA", False, t)


def tela_boa(v, t, prog):
    return _tela("IMAGEM OK", True, t)


def reflexo(v, t, prog):
    """Parede e beiral perto da câmera: parte do infravermelho volta direto na lente."""
    w, h = 1000, 620
    im, d = base_cartao(w, h, (255, 255, 255), 40)
    titulo_painel(d, w, "POR QUE ESTOURA", CORES["azul_escuro"])
    ox, oy = 20, 20
    d.rectangle((ox + 40, oy + 120, ox + 110, oy + h - 20), fill=(190, 180, 168))     # parede
    d.rectangle((ox + 40, oy + 120, ox + 560, oy + 175), fill=(160, 120, 90))         # beiral
    cx, cy = ox + 200, oy + 240
    d.rectangle((ox + 110, cy - 10, cx - 30, cy + 10), fill=(120, 124, 128))           # suporte
    d.rounded_rectangle((cx - 40, cy - 34, cx + 70, cy + 34), 14, fill=(244, 246, 248), outline=(150, 156, 164), width=4)
    d.ellipse((cx + 50, cy - 22, cx + 94, cy + 22), fill=(30, 32, 36))
    lente = (cx + 92, cy)
    k = suave(prog / 0.5)
    vermelho = (226, 59, 48)
    for ang in (-8, 4, 16):   # raios que saem para a cena
        a = np.radians(ang)
        comp = 640 * k
        d.line((*lente, lente[0] + comp * np.cos(a), lente[1] + comp * np.sin(a)), fill=(240, 150, 140), width=8)
    if prog > 0.3:            # raio que bate no beiral e volta
        k2 = suave((prog - 0.3) / 0.4)
        bate = (lente[0] + 170, oy + 175)
        u1 = min(1.0, k2 * 2)
        d.line((*lente, lente[0] + (bate[0] - lente[0]) * u1, lente[1] + (bate[1] - lente[1]) * u1), fill=vermelho, width=12)
        if k2 > 0.5:
            u = (k2 - 0.5) * 2
            d.line((*bate, bate[0] + (lente[0] + 6 - bate[0]) * u, bate[1] + (lente[1] - 12 - bate[1]) * u),
                   fill=vermelho, width=12)
    if prog > 0.75:
        d.ellipse((lente[0] - 40, lente[1] - 40, lente[0] + 40, lente[1] + 40), outline=(255, 210, 60), width=10)
        d.text((ox + 600, oy + 300), "Luz volta", font=fonte(54), fill=vermelho, anchor="lm")
        d.text((ox + 600, oy + 370), "direto na lente", font=fonte(54), fill=vermelho, anchor="lm")
        d.text((ox + 600, oy + 450), "= imagem branca", font=fonte(46, "bold"), fill=(60, 66, 74), anchor="lm")
    return im


produzir(__file__, {"tela_ruim": tela_ruim, "tela_boa": tela_boa, "reflexo": reflexo})
