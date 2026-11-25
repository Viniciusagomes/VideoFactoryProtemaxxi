"""Vídeo 09 — Erro de instalador #4: conector mal crimpado. Ver ferramentas/fabrica.py para o uso."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ferramentas"))
from fabrica import CORES, base_cartao, produzir, titulo_painel  # noqa: E402
from video import fonte, pop  # noqa: E402

BRANCO = (244, 244, 240)
LARANJA, VERDE, AZUL, MARROM = (240, 130, 40), (40, 160, 80), (40, 100, 200), (130, 80, 40)
# T568B: (cor, listrado com branco?, nome)
T568B = [(LARANJA, True, "Branco laranja"), (LARANJA, False, "Laranja"), (VERDE, True, "Branco verde"),
         (AZUL, False, "Azul"), (AZUL, True, "Branco azul"), (VERDE, False, "Verde"),
         (MARROM, True, "Branco marrom"), (MARROM, False, "Marrom")]


def cores(v, t, prog):
    """Os 8 fios do padrão T568B aparecendo um a um, com o nome de cada cor."""
    w, h = 1000, 660
    im, d = base_cartao(w, h, (255, 255, 255), 40)
    titulo_painel(d, w, "PADRÃO T568B (AS DUAS PONTAS)", CORES["azul_escuro"])
    x0, larg, y0, y1 = 20 + 70, 100, 20 + 130, 20 + 470
    for k, (cor, listra, nome) in enumerate(T568B):
        ent = 0.15 + k * 0.08
        if prog < ent:
            continue
        s = pop((prog - ent) / 0.08)
        x = x0 + k * (larg + 8)
        yb = y0 + (y1 - y0) * min(1.0, s)
        d.rounded_rectangle((x + 20, y0, x + larg - 20, yb), 18, fill=BRANCO if listra else cor, outline=(60, 60, 60), width=3)
        if listra:
            for yy in range(int(y0) + 12, int(yb) - 10, 46):
                d.polygon([(x + 22, yy), (x + larg - 22, yy - 18), (x + larg - 22, yy + 4), (x + 22, yy + 22)], fill=cor)
        d.ellipse((x + larg / 2 - 26, y1 + 18, x + larg / 2 + 26, y1 + 70), fill=CORES["amarelo"])
        d.text((x + larg / 2, y1 + 45), str(k + 1), font=fonte(34), fill=(20, 20, 20), anchor="mm")
    if prog > 0.85:
        d.text((20 + w / 2, 20 + h - 40), "Igual nas duas pontas do cabo!", font=fonte(44), fill=CORES["verde"], anchor="mm")
    return im


produzir(__file__, {"cores": cores})
