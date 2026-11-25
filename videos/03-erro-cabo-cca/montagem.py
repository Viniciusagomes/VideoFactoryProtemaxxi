"""Vídeo 03 — Erro de instalador #2: cabo CCA. Ver ferramentas/fabrica.py para o uso."""
import sys
from pathlib import Path

from PIL import ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ferramentas"))
from fabrica import CORES, ajustar, base_cartao, produzir, titulo_painel  # noqa: E402
from video import fonte, pop, suave  # noqa: E402

COBRE, ALUMINIO = (204, 120, 60), (196, 202, 210)


def corte_cabos(v, t, prog):
    """Corte dos dois fios (CCA x 100% cobre) e a energia que chega na câmera."""
    w, h = 1000, 640
    im, d = base_cartao(w, h, (255, 255, 255), 40)
    titulo_painel(d, w, "POR DENTRO DO FIO", CORES["azul_escuro"])
    for j, (nome, cor_txt, nucleo, energia) in enumerate((("CCA", CORES["vermelho"], ALUMINIO, 0.55),
                                                           ("100% COBRE", CORES["verde"], COBRE, 1.0))):
        cx = 20 + w * (0.27 + 0.46 * j)
        ent = 0.0 if j == 0 else 0.35
        if prog < ent:
            continue
        s = pop((prog - ent) / 0.25)
        r = 110 * s
        cy = 20 + 270
        d.ellipse((cx - r - 18, cy - r - 18, cx + r + 18, cy + r + 18), fill=(60, 120, 200))   # capa
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=COBRE)
        rn = r * (0.82 if j == 0 else 0.0)
        if rn > 1:
            d.ellipse((cx - rn, cy - rn, cx + rn, cy + rn), fill=nucleo)
        d.text((cx, cy + 165), nome, font=ajustar(nome, 52, 400), fill=cor_txt, anchor="mm")
        sub = "alumínio + capa de cobre" if j == 0 else "cobre até o centro"
        d.text((cx, cy + 220), sub, font=ajustar(sub, 34, 420, "bold"), fill=CORES["cinza"], anchor="mm")
        # energia que chega na câmera
        k = suave((prog - ent - 0.2) / 0.4)
        bx0, by = cx - 180, cy + 285
        d.rounded_rectangle((bx0, by - 20, bx0 + 360, by + 20), 20, fill=(225, 229, 234))
        if k > 0:
            d.rounded_rectangle((bx0, by - 20, bx0 + 360 * energia * k, by + 20), 20,
                                fill=CORES["amarelo"] if j == 0 else CORES["verde"])
    if prog > 0.6:
        d.text((20 + w / 2, 20 + h - 18), "energia que chega na câmera", font=fonte(30, "bold"), fill=CORES["cinza"],
               anchor="mm")
    return im


produzir(__file__, {"corte_cabos": corte_cabos})
