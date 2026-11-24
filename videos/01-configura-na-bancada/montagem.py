"""Vídeo 01 — "Configura na bancada, instala na altura" (Reels, ~1 min).

Uso:
    python videos/01-configura-na-bancada/montagem.py            # gera saida/01-configura-na-bancada/video.mp4
    python videos/01-configura-na-bancada/montagem.py --quadros 2,15,40   # só salva esses quadros em PNG (revisão)

As falas ficam em saida/01-configura-na-bancada/audio/fNN.mp3 (geradas no ElevenLabs com o texto do roteiro.json).
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
NOMES = {
    "marcao-instalador": ("MARCÃO", (242, 140, 40)),
    "seu-antonio-cliente": ("SEU ANTÔNIO", (142, 100, 64)),
    "vinicius-apresentador": ("VINÍCIUS", VERDE),
}

# ------------------------------------------------------------------ cenários
# Campo: a câmera da parede fica ao lado do rosto do Marcão na escada (no cenário original ela ficaria atrás dele).
CAM_ORIG, CABO_ORIG = gc.camera_bullet(1290, 300, 0.9, led=True), gc.P("M1290 330 Q1310 420 1296 600", "none", "#1E1F22", 4)
svg_campo = gc.campo_instalador()
assert CAM_ORIG in svg_campo and CABO_ORIG in svg_campo, "o cenário campo-instalador mudou: ajuste a montagem"
svg_campo = svg_campo.replace(CAM_ORIG, gc.camera_bullet(1160, 300, 0.9, led=True)).replace(
    CABO_ORIG, gc.P("M1160 330 Q1180 420 1166 600", "none", "#1E1F22", 4))

# Bancada: roteador, câmera e cabo em cima da bancada do estoque.
PROPS_BANCADA = (
    gc.P("M712 652 L696 586 M808 652 L824 586", "none", "#9AA5B1", 8)
    + gc.R(690, 648, 140, 46, "#F4F6F8", 14, "#9AA5B1", 3)
    + "".join(f'<circle cx="{720 + k * 24}" cy="672" r="6" fill="#1FAE5A"/>' for k in range(4))
    + gc.P("M922 690 Q870 730 828 684", "none", "#1E1F22", 5)
    + gc.camera_bullet(1040, 668, 1.2, led=True)
)
svg_bancada = gc.estoque_expedicao().replace('<g id="chao">', PROPS_BANCADA + '<g id="chao">', 1)


def seta_6m(img: Image.Image) -> Image.Image:
    """Cota de 6 metros desenhada no cenário do campo."""
    img = img.copy()
    d = ImageDraw.Draw(img)
    f = V.F
    x, y0, y1 = 1100 * f, 1000 * f, 318 * f
    for cor, larg in (((20, 20, 20), 26), ((255, 255, 255), 12)):
        y = y1 + 40 * f
        while y < y0 - 40 * f:
            d.line((x, y, x, min(y + 40 * f, y0 - 40 * f)), fill=cor, width=larg)
            y += 70 * f
        for ya, s in ((y1, 1), (y0, -1)):
            d.polygon([(x, ya), (x - 26 * f, ya + s * 46 * f), (x + 26 * f, ya + s * 46 * f)], fill=cor,
                      outline=(20, 20, 20), width=6)
    ym = (y0 + y1) / 2
    d.rounded_rectangle((x - 100 * f, ym - 52 * f, x + 100 * f, ym + 52 * f), 26 * f, fill=AMARELO, outline=(20, 20, 20), width=14)
    d.text((x, ym), "6 m", font=fonte(round(70 * f)), fill=(20, 20, 20), anchor="mm")
    return img


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
CORTE_BANCADA = INI[4] - 0.3
CORTE_CAMPO2 = INI[10] - 0.3


def nivel(i: int, t: float):
    if INI[i] <= t < INI[i] + DURS[i]:
        e = ENVS[i]
        return float(e[min(len(e) - 1, int((t - INI[i]) * FPS))])
    return None


# ------------------------------------------------------------------ cartões (tela)
def base_cartao(w: int, h: int, cor, raio=38, borda=None, larg_borda=8):
    im = Image.new("RGBA", (w + 40, h + 46), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((24, 32, w + 24, h + 32), raio, fill=(0, 0, 0, 70))
    d.rounded_rectangle((20, 20, w + 20, h + 20), raio, fill=cor, outline=borda, width=larg_borda if borda else 0)
    return im, d


def icone_x(d, cx, cy, r=46):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=VERMELHO)
    k = r * 0.42
    d.line((cx - k, cy - k, cx + k, cy + k), fill="white", width=12)
    d.line((cx - k, cy + k, cx + k, cy - k), fill="white", width=12)


def icone_ok(d, cx, cy, r=46, cor=VERDE):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=cor)
    d.line((cx - r * 0.45, cy + 2, cx - r * 0.1, cy + r * 0.35, cx + r * 0.5, cy - r * 0.35), fill="white", width=12,
           joint="curve")


def banner(linhas, fundo, cor_txt=(20, 20, 20), tam=86, larg=920, giro=-2.5):
    while max(fonte(tam).getlength(l) for l in linhas) > larg - 90:
        tam -= 2
    fnt = fonte(tam)
    h = 60 + len(linhas) * (tam + 16)
    im, d = base_cartao(larg, h, fundo, 34)
    for k, l in enumerate(linhas):
        d.text((20 + larg / 2, 20 + 36 + k * (tam + 16) + tam / 2), l, font=fnt, fill=cor_txt, anchor="mm")
    return im.rotate(giro, resample=Image.BICUBIC, expand=True)


def notificacao(titulo, sub, icone):
    w, h = 900, 210
    im, d = base_cartao(w, h, (255, 255, 255), 40)
    (icone_x if icone == "x" else icone_ok)(d, 20 + 100, 20 + h / 2, 54)
    d.text((20 + 190, 20 + 78), titulo, font=fonte(62), fill=(25, 25, 25), anchor="lm")
    d.text((20 + 190, 20 + 150), sub, font=fonte(40, "bold"), fill=(90, 96, 104), anchor="lm")
    return im


def ao_vivo():
    w, h = 900, 210
    im, d = base_cartao(w, h, (24, 26, 30), 40)
    d.ellipse((20 + 60, 20 + 65, 20 + 140, 20 + 145), fill=VERMELHO)
    d.text((20 + 190, 20 + 78), "AO VIVO", font=fonte(66), fill="white", anchor="lm")
    d.text((20 + 190, 20 + 150), "Câmera fixada e gravando", font=fonte(40, "bold"), fill=(190, 196, 204), anchor="lm")
    return im


def selo_erro():
    fnt = fonte(104)
    w = int(fnt.getlength("ERRO COMUM")) + 120
    im = Image.new("RGBA", (w + 40, 220), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, w + 20, 200), 30, fill=(255, 255, 255, 235), outline=VERMELHO, width=14)
    d.text((20 + w / 2, 110), "ERRO COMUM", font=fnt, fill=VERMELHO, anchor="mm")
    return im.rotate(-7, resample=Image.BICUBIC, expand=True)


def chip(txt):
    fnt = fonte(56)
    w = int(fnt.getlength(txt)) + 150
    im, d = base_cartao(w, 112, VERMELHO, 56)
    icone_x(d, 20 + 62, 20 + 56, 32)
    d.text((20 + 112, 20 + 56), txt, font=fnt, fill="white", anchor="lm")
    return im


PASSOS = ["Liga na fonte, perto do roteador", "Adiciona no app pelo QR Code",
          "Conecta no Wi-Fi 2,4 GHz do cliente", "Testa imagem, nome e gravação"]


def checklist(atual: int):
    w, lin = 960, 104
    h = 110 + lin * len(PASSOS)
    im, d = base_cartao(w, h, (255, 255, 255), 40)
    d.rounded_rectangle((20, 20, 20 + w, 20 + 96), 40, fill=VERDE)
    d.rectangle((20, 76, 20 + w, 20 + 96), fill=VERDE)
    d.text((20 + w / 2, 20 + 50), "NA BANCADA, ANTES DE SUBIR", font=fonte(52), fill="white", anchor="mm")
    for k, txt in enumerate(PASSOS):
        y = 20 + 110 + k * lin + lin / 2 - 6
        if k == atual:
            d.rounded_rectangle((34, y - lin / 2 + 8, 6 + w, y + lin / 2 - 8), 24, fill=(255, 241, 196))
        if k < atual:
            icone_ok(d, 20 + 70, y, 34)
        else:
            cor = AMARELO if k == atual else (205, 210, 216)
            d.ellipse((20 + 36, y - 34, 20 + 104, y + 34), fill=cor)
            d.text((20 + 70, y + 2), str(k + 1), font=fonte(46), fill=(20, 20, 20), anchor="mm")
        cor_txt = (25, 25, 25) if k <= atual else (150, 156, 164)
        d.text((20 + 130, y), txt, font=fonte(48, "bold"), fill=cor_txt, anchor="lm")
    return im


def cartao_final(logo: Image.Image):
    im = Image.new("RGBA", (LARG, ALT), (16, 24, 32, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, LARG, ALT), fill=(16, 26, 36, 228))
    colar(im, logo, LARG / 2, 520)
    d.rounded_rectangle((90, 760, LARG - 90, 1180), 44, fill=(255, 255, 255))
    d.text((LARG / 2, 860), "CONFIGURA NA BANCADA.", font=fonte(58), fill=AZUL_ESCURO, anchor="mm")
    d.text((LARG / 2, 960), "INSTALA NA ALTURA.", font=fonte(58), fill=VERDE, anchor="mm")
    d.text((LARG / 2, 1080), "Menos tempo na escada, zero retrabalho.", font=fonte(40, "bold"), fill=(90, 96, 104),
           anchor="mm")
    d.rounded_rectangle((110, 1260, LARG - 110, 1380), 60, fill=AMARELO)
    d.text((LARG / 2, 1320), "Salva e manda pro seu instalador", font=fonte(44), fill=(20, 20, 20), anchor="mm")
    return im


def legenda_chunks(i: int):
    """Divide a fala em pedaços de até 4 palavras, distribuídos pelo tempo da fala."""
    palavras = sem_tags(FALAS[i]["texto"]).split()
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
            for a, b, txt in legenda_chunks(i):
                if a <= t < b or (txt == legenda_chunks(i)[-1][2] and t >= a):
                    fnt = fonte(74)
                    linhas = V.texto_quebrado(txt.upper(), fnt, 960)
                    for k, l in enumerate(linhas):
                        d.text((LARG / 2, 1450 + k * 88), l, font=fnt, fill="white", anchor="mm",
                               stroke_width=10, stroke_fill=(15, 15, 15))
                    break
            return


# ------------------------------------------------------------------ montagem
def preparar():
    print("Rasterizando cenários e personagens (com cache)...")
    campo = V.carregar_cenario(svg_campo, CACHE)
    campo.extras["6m"] = seta_6m(campo.fundo)
    bancada = V.carregar_cenario(svg_bancada, CACHE, frente_grupos=("moveis",))
    atores = {
        "marcao": V.Ator("marcao-instalador", 500, CACHE, boca_parada="fechada"),
        "antonio": V.Ator("seu-antonio-cliente", 500, CACHE, boca_parada="fechada"),
        "vini": V.Ator("vinicius-apresentador", 500, CACHE),
        "marcao_b": V.Ator("marcao-instalador", 640, CACHE),
        "vini_b": V.Ator("vinicius-apresentador", 640, CACHE),
    }
    logo_svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 591 150" width="591" height="150">'
                f'<path fill="#FFFFFF" fill-rule="evenodd" d="{gc.LOGO_D}"/></svg>')
    logo = V.rasterizar(logo_svg, 820, 208, CACHE)
    return campo, bancada, atores, logo


def roteiro_cenas(campo, bancada, A):
    cam_campo1 = [(0.0, Camera(1244, 380, 1.45)), (INI[1] - 0.15, Camera(960, 640, 1.25)),
                  (INI[2] - 0.2, Camera(880, 540, 1.0)), (INI[3] - 0.1, Camera(730, 620, 1.3))]
    cam_banc = [(CORTE_BANCADA, Camera(970, 540, 1.0)), (INI[5] - 0.1, Camera(930, 600, 1.08)),
                (INI[9] - 0.1, Camera(1110, 560, 1.32))]
    cam_campo2 = [(CORTE_CAMPO2, Camera(1244, 380, 1.45)), (INI[11] - 0.1, Camera(960, 640, 1.25)),
                  (INI[12] - 0.1, Camera(880, 540, 1.0))]

    def estado(t: float):
        def lv(*idx):
            vals = [nivel(i, t) for i in idx]
            vals = [v for v in vals if v is not None]
            return vals[0] if vals else None

        if t < CORTE_BANCADA:
            cam = V.interpolar_camera(cam_campo1, t)
            tremor = 5 * np.sin(t * 38) if nivel(0, t) is not None else 0.0
            atores = [AtorNaCena(A["antonio"], 900, 1010, lv(1)),
                      AtorNaCena(A["marcao"], 1244, 696, lv(0), dx=tremor)]
            entra = INI[2] - 0.25
            if t >= entra:
                k = suave((t - entra) / 0.45)
                atores.insert(0, AtorNaCena(A["vini"], 700 - 330 * (1 - k), 1010, lv(2, 3),
                                            dy=-40 * np.sin(np.pi * k) if k < 1 else 0.0))
            return campo, cam, atores, ("6m" if INI[1] - 0.3 <= t < INI[2] else None)
        if t < CORTE_CAMPO2:
            cam = V.interpolar_camera(cam_banc, t)
            pulo = -18 * abs(np.sin((t - INI[9]) * 9)) if nivel(9, t) is not None else 0.0
            # pés escondidos atrás da bancada, rosto acima dos objetos
            atores = [AtorNaCena(A["vini_b"], 800, 990, lv(4, 5, 6, 7, 8)),
                      AtorNaCena(A["marcao_b"], 1130, 990, lv(9), dy=pulo)]
            return bancada, cam, atores, None
        A["marcao"].boca_parada = "aberta"
        A["antonio"].boca_parada = "aberta" if t > INI[11] else "fechada"
        cam = V.interpolar_camera(cam_campo2, t)
        atores = [AtorNaCena(A["vini"], 700, 1010, lv(12)), AtorNaCena(A["antonio"], 900, 1010, lv(11)),
                  AtorNaCena(A["marcao"], 1244, 696, lv(10))]
        return campo, cam, atores, None

    return estado


def lista_cartoes(logo):
    """(entra, sai, imagem, cx, cy). As imagens entram com 'pop' e saem com fade."""
    c = [
        (0.15, INI[1] - 0.1, banner(["CÂMERA A 6 METROS", "E NÃO CONECTA?"], AMARELO), LARG / 2, 300),
        (INI[0] + 1.0, INI[1] + 0.2, notificacao("Falha ao conectar", "Sinal Wi-Fi fraco ou instável", "x"), LARG / 2, 1100),
        (INI[2] + 1.1, INI[3] - 0.05, selo_erro(), LARG / 2, 330),
        (INI[3] + 0.2, CORTE_BANCADA, chip("Sinal oscilando"), 420, 290),
        (INI[3] + 1.5, CORTE_BANCADA, chip("Uma mão na escada"), 610, 430),
        (INI[3] + 3.0, CORTE_BANCADA, chip("Reset vira novela"), 450, 570),
        (CORTE_BANCADA + 0.25, INI[5] - 0.05, banner(["O JEITO CERTO:", "CONFIGURA NA BANCADA"], VERDE, (255, 255, 255), 80),
         LARG / 2, 330),
        (INI[9] + 0.3, CORTE_CAMPO2, notificacao("Câmera conectada", "Wi-Fi do cliente (2,4 GHz) • imagem OK", "ok"),
         LARG / 2, 330),
        (CORTE_CAMPO2 + 0.2, INI[10] + 2.2, banner(["AGORA É SÓ", "SUBIR E FIXAR"], VERDE, (255, 255, 255), 80), LARG / 2, 300),
        (INI[10] + 2.4, INI[11] + 0.3, ao_vivo(), LARG / 2, 1100),
        (INI[12] - 0.05, FIM_FALAS, banner(["CONFIGURA NA BANCADA,", "INSTALA NA ALTURA"], AMARELO, tam=74), LARG / 2, 300),
    ]
    for k in range(4):
        fim = INI[6 + k] - 0.05 if k < 3 else INI[9] - 0.05
        c.append((INI[5 + k] - 0.05, fim, checklist(k), LARG / 2, 400))
    return c, (FIM_FALAS - 0.1, DUR + 1, cartao_final(logo))


def mixar_audio() -> Path:
    total = np.zeros(int((DUR + 0.5) * SR), dtype=np.float32)

    def por(sinal, t):
        i = int(t * SR)
        total[i:i + len(sinal)] += sinal[: max(0, len(total) - i)]

    for i, a in enumerate(AUDIOS):
        por(a, INI[i])
    for t in (CORTE_BANCADA - 0.15, CORTE_CAMPO2 - 0.15):
        por(V.whoosh(), t)
    return total


def renderizar(quadros_previa: list[float] | None = None):
    SAIDA.mkdir(parents=True, exist_ok=True)
    campo, bancada, A, logo = preparar()
    estado = roteiro_cenas(campo, bancada, A)
    cartoes, (fin_ini, _, fin_img) = lista_cartoes(logo)

    def montar(t: float) -> Image.Image:
        cen, cam, atores, extra = estado(t)
        img = V.quadro(cen, cam, atores, t, extra)
        for a, b, im, cx, cy in cartoes:
            if a <= t < b:
                colar(img, im, cx, cy, pop((t - a) / 0.28), min(1.0, (b - t) / 0.18))
        desenhar_legenda(img, t)
        if t >= fin_ini:
            colar(img, fin_img, LARG / 2, ALT / 2, 1.0, min(1.0, (t - fin_ini) / 0.4))
        for corte in (CORTE_BANCADA, CORTE_CAMPO2):
            if corte <= t < corte + 0.15:
                flash = Image.new("RGBA", img.size, (255, 255, 255, int(255 * (1 - (t - corte) / 0.15))))
                img.alpha_composite(flash)
        return img

    if quadros_previa:
        for t in quadros_previa:
            p = SAIDA / f"quadro_{t:05.1f}s.png"
            montar(t).convert("RGB").save(p)
            print(p)
        return

    audio = mixar_audio()
    for a, _b, *_r in cartoes:
        i = int(a * SR)
        bl = V.blip()
        audio[i:i + len(bl)] += bl[: max(0, len(audio) - i)]
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
