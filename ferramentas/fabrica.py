"""Fábrica de vídeos por roteiro declarativo.

Um vídeo novo é só um `roteiro.json` (cenas, falas, câmera e cartões) e um `montagem.py` de 3 linhas:

    from fabrica import produzir
    produzir(__file__)

Uso:
    python videos/<slug>/montagem.py                 # gera saida/<slug>/video.mp4
    python videos/<slug>/montagem.py --quadros 2,15  # só salva esses quadros em PNG (revisão)
    python ferramentas/fabrica.py falas <slug>       # lista as falas com o voice_id de cada personagem

Formato do roteiro (resumo; ver videos/03-* para um exemplo completo):
    "cenas": {"<nome>": {"cenario": "estoque-expedicao", "frente": ["moveis"], "filtro": "noite",
                         "camera": [cx, cy, zoom], "atores": {"<slug>": {"x": 800, "pe": 990, "altura": 640}}}}
    "falas": [{"id": "f01", "cena": "<nome>", "personagem": "<slug>", "texto": "[tom] fala",
               "legenda": "texto na tela (opcional)", "camera": [cx, cy, zoom], "acao": "pulo|tremor",
               "cartoes": [{"tipo": "banner", "linhas": ["..."], "cor": "amarelo", "ate": "f03"}]}]
    "serie": "ERRO DE INSTALADOR #2"      (opcional: selo no topo durante a primeira cena)
    "final": {"linhas": ["...", "..."], "sub": "...", "cta": "..."}

Tipos de cartão: banner, notificacao, lista, comparativo, numero, selo, celular, custom (função passada em extras).
Tempo de um cartão: entra em INI(fala) + "de" (s) e fica até o início de "ate" (id de fala), ou "dur" segundos,
ou o fim da fala (padrão).
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gerar_cenarios as gc  # noqa: E402
import video as V  # noqa: E402
from video import FPS, LARG, ALT, SR, Camera, AtorNaCena, fonte, colar, pop  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]

CORES = {
    "verde": (31, 174, 90), "azul_escuro": (34, 55, 75), "amarelo": (242, 194, 48), "vermelho": (226, 59, 48),
    "laranja": (242, 140, 40), "azul": (43, 123, 185), "cinza": (90, 96, 104), "roxo": (124, 77, 190),
    "branco": (255, 255, 255), "preto": (24, 26, 30),
}
COR_NOME = {
    "vinicius-apresentador": "verde", "marcao-instalador": "laranja", "rodrigo-vendedor": "verde",
    "luana-estoquista": "roxo", "caio-suporte": "azul", "seu-antonio-cliente": (142, 100, 64),
    "fernanda-cliente": (214, 72, 120),
}
PAPEL = {"caio-suporte": "SUPORTE", "luana-estoquista": "ESTOQUE", "rodrigo-vendedor": "VENDAS",
         "marcao-instalador": "INSTALADOR"}


def cor(c):
    if isinstance(c, (list, tuple)):
        return tuple(c)
    return CORES[c]


def sem_tags(t: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"\[[^\]]*\]", "", t)).strip()


def personagens() -> dict:
    d = json.loads((RAIZ / "personagens" / "personagens.json").read_text(encoding="utf-8"))
    return {p["slug"]: p for p in d["personagens"]}


# ------------------------------------------------------------------ desenho de cartões
def base_cartao(w: int, h: int, fundo, raio=38, borda=None, larg_borda=8):
    im = Image.new("RGBA", (w + 40, h + 46), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((24, 32, w + 24, h + 32), raio, fill=(0, 0, 0, 70))
    d.rounded_rectangle((20, 20, w + 20, h + 20), raio, fill=fundo, outline=borda, width=larg_borda if borda else 0)
    return im, d


def icone(d, tipo: str, cx, cy, r=46):
    if r < 2:
        return
    if tipo == "ok":
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=CORES["verde"])
        d.line((cx - r * 0.45, cy + 2, cx - r * 0.1, cy + r * 0.35, cx + r * 0.5, cy - r * 0.35), fill="white",
               width=max(4, int(r / 4)), joint="curve")
    elif tipo == "x":
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=CORES["vermelho"])
        k = r * 0.42
        d.line((cx - k, cy - k, cx + k, cy + k), fill="white", width=max(4, int(r / 4)))
        d.line((cx - k, cy + k, cx + k, cy - k), fill="white", width=max(4, int(r / 4)))
    elif tipo == "!":
        d.polygon([(cx, cy - r), (cx + r * 1.1, cy + r * 0.85), (cx - r * 1.1, cy + r * 0.85)], fill=CORES["amarelo"])
        d.text((cx, cy + r * 0.2), "!", font=fonte(max(8, int(r * 1.2))), fill=(20, 20, 20), anchor="mm")
    elif tipo == "sino":
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=CORES["laranja"])
        d.pieslice((cx - r * 0.5, cy - r * 0.6, cx + r * 0.5, cy + r * 0.5), 180, 360, fill="white")
        d.rectangle((cx - r * 0.5, cy - r * 0.05, cx + r * 0.5, cy + r * 0.3), fill="white")
        d.ellipse((cx - r * 0.14, cy + r * 0.3, cx + r * 0.14, cy + r * 0.58), fill="white")
    elif tipo == "ao_vivo":
        d.ellipse((cx - r * 0.8, cy - r * 0.8, cx + r * 0.8, cy + r * 0.8), fill=CORES["vermelho"])
    elif tipo == "fone":
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=CORES["verde"])
        d.arc((cx - r * 0.55, cy - r * 0.55, cx + r * 0.55, cy + r * 0.6), 120, 330, fill="white", width=max(4, int(r / 3.5)))
    else:  # número dentro de um círculo
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=CORES["amarelo"])
        d.text((cx, cy + 2), str(tipo), font=fonte(max(8, int(r * 1.2))), fill=(20, 20, 20), anchor="mm")


def ajustar(txt, tam, larg, peso="black"):
    while tam > 10 and fonte(tam, peso).getlength(txt) > larg:
        tam -= 2
    return fonte(tam, peso)


def banner(linhas, fundo, cor_txt=(20, 20, 20), tam=86, larg=920, giro=-2.5):
    while max(fonte(tam).getlength(l) for l in linhas) > larg - 90:
        tam -= 2
    fnt = fonte(tam)
    h = 60 + len(linhas) * (tam + 16)
    im, d = base_cartao(larg, h, fundo, 34)
    for k, l in enumerate(linhas):
        d.text((20 + larg / 2, 20 + 36 + k * (tam + 16) + tam / 2), l, font=fnt, fill=cor_txt, anchor="mm")
    return im.rotate(giro, resample=Image.BICUBIC, expand=True)


def notificacao(titulo, sub, tipo_icone, escuro=False):
    w, h = 900, 210
    im, d = base_cartao(w, h, (24, 26, 30) if escuro else (255, 255, 255), 40)
    icone(d, tipo_icone, 20 + 100, 20 + h / 2, 54)
    d.text((20 + 190, 20 + 78), titulo, font=ajustar(titulo, 62, w - 220), fill="white" if escuro else (25, 25, 25),
           anchor="lm")
    d.text((20 + 190, 20 + 150), sub, font=ajustar(sub, 40, w - 220, "bold"),
           fill=(190, 196, 204) if escuro else (90, 96, 104), anchor="lm")
    return im


def selo(txt, c=CORES["vermelho"], giro=-7):
    fnt = fonte(104)
    w = int(fnt.getlength(txt)) + 120
    im = Image.new("RGBA", (w + 40, 220), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, w + 20, 200), 30, fill=(255, 255, 255, 235), outline=c, width=14)
    d.text((20 + w / 2, 110), txt, font=fnt, fill=c, anchor="mm")
    im = im.rotate(giro, resample=Image.BICUBIC, expand=True)
    if im.width > 1000:
        im = im.resize((1000, round(im.height * 1000 / im.width)), Image.LANCZOS)
    return im


def titulo_painel(d, w, titulo, c):
    d.rounded_rectangle((20, 20, 20 + w, 20 + 96), 40, fill=c)
    d.rectangle((20, 76, 20 + w, 20 + 96), fill=c)
    d.text((20 + w / 2, 20 + 50), titulo, font=ajustar(titulo, 52, w - 60), fill="white", anchor="mm")


def lista(titulo, itens, c, progresso: float, w=960, escalas=None):
    """Painel com título e itens [tipo, texto] que aparecem conforme o progresso (0..1),
    ou conforme 'escalas' (uma por item: 0 = escondido, 1 = inteiro)."""
    lin = 104
    h = 110 + lin * len(itens)
    im, d = base_cartao(w, h, (255, 255, 255), 40)
    titulo_painel(d, w, titulo, c)
    n = len(itens)
    for k, (tipo, txt, *_r) in enumerate(itens):
        if escalas is not None:
            s = escalas[k]
            if s <= 0:
                continue
        else:
            ent = k / n
            if progresso < ent:
                continue
            s = pop((progresso - ent) * n / 0.6) if n else 1
        y = 20 + 110 + k * lin + lin / 2 - 6
        icone(d, tipo, 20 + 70, y, 34 * s)
        d.text((20 + 128, y), txt, font=ajustar(txt, 48, w - 150, "bold"), fill=(25, 25, 25), anchor="lm")
    return im


def comparativo(esq, dir_, progresso: float, w=1000):
    """Duas colunas lado a lado: {"titulo", "cor", "itens": [[tipo, texto]]}."""
    n = max(len(esq["itens"]), len(dir_["itens"]))
    lin = 92
    h = 130 + lin * n
    im, d = base_cartao(w, h, (255, 255, 255), 40)
    col = w / 2
    for j, lado in enumerate((esq, dir_)):
        x0 = 20 + j * col
        c = cor(lado.get("cor", "cinza"))
        d.rounded_rectangle((x0 + 14, 34, x0 + col - 14, 124), 30, fill=c)
        d.text((x0 + col / 2, 79), lado["titulo"], font=ajustar(lado["titulo"], 46, col - 60), fill="white", anchor="mm")
        for k, (tipo, txt) in enumerate(lado["itens"]):
            ent = (k + j * 0.5) / (n + 0.5)
            if progresso < ent:
                continue
            s = pop((progresso - ent) * (n + 0.5) / 0.6)
            y = 20 + 130 + k * lin + lin / 2 - 4
            icone(d, tipo, x0 + 52, y, 26 * s)
            d.text((x0 + 90, y), txt, font=ajustar(txt, 38, col - 110, "bold"), fill=(25, 25, 25), anchor="lm")
    d.line((20 + col, 140, 20 + col, 20 + h - 20), fill=(220, 224, 230), width=4)
    return im


def numero(valor, sub, c, w=760):
    h = 330
    im, d = base_cartao(w, h, (255, 255, 255), 44, c, 10)
    d.text((20 + w / 2, 20 + 140), valor, font=ajustar(valor, 170, w - 80), fill=c, anchor="mm")
    d.text((20 + w / 2, 20 + 270), sub, font=ajustar(sub, 46, w - 80, "bold"), fill=(60, 66, 74), anchor="mm")
    return im


def celular(titulo, telas: int, alerta: str | None, t: float):
    """Celular com o app de câmeras: mosaico de 'telas' câmeras e, opcionalmente, um alerta no topo."""
    w, h = 520, 900
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((24, 30, w + 24, h + 30), 70, fill=(0, 0, 0, 80))
    d.rounded_rectangle((20, 20, w + 20, h + 20), 70, fill=(24, 26, 30))
    x0, y0, x1, y1 = 48, 60, w - 8, h - 20
    d.rounded_rectangle((x0, y0, x1, y1), 46, fill=(244, 247, 250))
    d.rounded_rectangle((x0, y0, x1, y0 + 120), 46, fill=CORES["verde"])
    d.rectangle((x0, y0 + 80, x1, y0 + 120), fill=CORES["verde"])
    d.text(((x0 + x1) / 2, y0 + 70), titulo, font=ajustar(titulo, 40, x1 - x0 - 40), fill="white", anchor="mm")
    cols = 1 if telas == 1 else 2
    rows = (telas + cols - 1) // cols
    gw = (x1 - x0 - 36) / cols
    gh = min(260.0, (y1 - y0 - 200) / max(rows, 1))
    paleta = [((126, 173, 214), (150, 128, 100)), ((190, 210, 190), (90, 110, 90)), ((214, 196, 170), (120, 96, 70)),
              ((170, 190, 214), (80, 90, 110))]
    for k in range(telas):
        cx0 = x0 + 12 + (k % cols) * (gw + 12)
        cy0 = y0 + 140 + (k // cols) * (gh + 12)
        ceu, chao = paleta[k % 4]
        d.rectangle((cx0, cy0, cx0 + gw, cy0 + gh), fill=ceu)
        d.rectangle((cx0, cy0 + gh * 0.6, cx0 + gw, cy0 + gh), fill=chao)
        d.rectangle((cx0 + gw * 0.15, cy0 + gh * 0.3, cx0 + gw * 0.4, cy0 + gh * 0.75), fill=(240, 236, 228))
        d.ellipse((cx0 + 10, cy0 + 10, cx0 + 26, cy0 + 26), fill=CORES["vermelho"] if int(t * 2) % 2 else (150, 40, 40))
        d.text((cx0 + gw - 10, cy0 + 18), f"CAM {k + 1}", font=fonte(22), fill="white", anchor="rm",
               stroke_width=3, stroke_fill=(20, 20, 20))
    if alerta:
        d.rounded_rectangle((x0 + 14, y1 - 170, x1 - 14, y1 - 30), 30, fill="white", outline=(210, 214, 220), width=3)
        icone(d, "sino", x0 + 70, y1 - 100, 36)
        d.text((x0 + 120, y1 - 100), alerta, font=ajustar(alerta, 34, x1 - x0 - 140, "bold"), fill=(25, 25, 25), anchor="lm")
    return im


def cartao_final(logo: Image.Image, fin: dict):
    im = Image.new("RGBA", (LARG, ALT), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, LARG, ALT), fill=(16, 26, 36, 228))
    colar(im, logo, LARG / 2, 500)
    d.rounded_rectangle((90, 740, LARG - 90, 1200), 44, fill=(255, 255, 255))
    l1, l2 = (fin["linhas"] + [""])[:2]
    d.text((LARG / 2, 850), l1, font=ajustar(l1, 64, LARG - 260), fill=CORES["azul_escuro"], anchor="mm")
    d.text((LARG / 2, 950), l2, font=ajustar(l2, 64, LARG - 260), fill=CORES["verde"], anchor="mm")
    sub = fin.get("sub", "")
    for k, linha in enumerate(V.texto_quebrado(sub, fonte(40, "bold"), LARG - 300)[:2]):
        d.text((LARG / 2, 1070 + k * 54), linha, font=fonte(40, "bold"), fill=CORES["cinza"], anchor="mm")
    cta = fin.get("cta", "Salva e manda pro seu instalador")
    d.rounded_rectangle((110, 1280, LARG - 110, 1400), 60, fill=CORES["amarelo"])
    d.text((LARG / 2, 1340), cta, font=ajustar(cta, 44, LARG - 300), fill=(20, 20, 20), anchor="mm")
    return im


def pilula_serie(txt):
    fnt = fonte(40)
    w = int(fnt.getlength(txt)) + 60
    im = Image.new("RGBA", (w + 20, 90), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 10, w + 10, 80), 35, fill=CORES["vermelho"], outline="white", width=5)
    d.text((10 + w / 2, 45), txt, font=fnt, fill="white", anchor="mm")
    return im


# ------------------------------------------------------------------ o vídeo
class Video:
    def __init__(self, pasta: Path, extras: dict | None = None):
        self.pasta = pasta
        self.slug = pasta.name
        self.saida = RAIZ / "saida" / self.slug
        self.cache = self.saida / "cache"
        self.r = json.loads((pasta / "roteiro.json").read_text(encoding="utf-8"))
        self.falas = self.r["falas"]
        self.extras = extras or {}
        self.pers = personagens()
        self._tempos()

    # --- tempos
    def _tempos(self):
        self.audios = [V.ler_audio(self.saida / "audio" / f"{f['id']}.mp3") for f in self.falas]
        self.envs = [V.envelope(a) for a in self.audios]
        self.durs = [len(a) / SR for a in self.audios]
        self.ini, self.cortes = [], []
        t = 0.45
        for i, f in enumerate(self.falas):
            if i and f["cena"] != self.falas[i - 1]["cena"]:
                t += 0.55 + f.get("pausa", 0)
                self.cortes.append(t - 0.3)
            elif i:
                t += f.get("pausa", 0)
            self.ini.append(t)
            t += self.durs[i] + 0.12
        self.fim_falas = t
        self.dur = t + 3.2
        self.idx = {f["id"]: i for i, f in enumerate(self.falas)}

    def nivel(self, i: int, t: float):
        if self.ini[i] <= t < self.ini[i] + self.durs[i]:
            e = self.envs[i]
            return float(e[min(len(e) - 1, int((t - self.ini[i]) * FPS))])
        return None

    def fim_fala(self, i):
        return self.ini[i + 1] - 0.05 if i + 1 < len(self.falas) else self.fim_falas

    # --- preparação
    def preparar(self):
        print("Rasterizando cenários e personagens (com cache)...")
        self.cenas = {}
        self.atores = {}
        for nome, c in self.r["cenas"].items():
            svg = gc.CENARIOS[c["cenario"]]()
            if "svg_extra" in self.extras and nome in self.extras["svg_extra"]:
                svg = self.extras["svg_extra"][nome](svg)
            self.cenas[nome] = V.carregar_cenario(svg, self.cache, tuple(c.get("frente", ())))
            for slug, a in c["atores"].items():
                chave = (slug, a["altura"], a.get("flip", False))
                if chave not in self.atores:
                    self.atores[chave] = V.Ator(slug, a["altura"], self.cache, boca_parada=a.get("boca", "fechada"),
                                                flip=a.get("flip", False))
        logo_svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 591 150" width="591" height="150">'
                    f'<path fill="#FFFFFF" fill-rule="evenodd" d="{gc.LOGO_D}"/></svg>')
        self.logo = V.rasterizar(logo_svg, 820, 208, self.cache)
        self.final = cartao_final(self.logo, self.r["final"])
        self.serie = pilula_serie(self.r["serie"]) if self.r.get("serie") else None
        self._cameras()
        self._cartoes()

    def _cameras(self):
        """Lista de segmentos (início, fim, cena, chaves de câmera)."""
        self.segmentos = []
        for i, f in enumerate(self.falas):
            c = self.r["cenas"][f["cena"]]
            if not self.segmentos or self.segmentos[-1]["cena"] != f["cena"]:
                ini = 0.0 if i == 0 else self.ini[i] - 0.3
                if self.segmentos:
                    self.segmentos[-1]["fim"] = ini
                self.segmentos.append({"ini": ini, "fim": 1e9, "cena": f["cena"], "falas": [],
                                       "chaves": [(ini, Camera(*c["camera"]))]})
            seg = self.segmentos[-1]
            seg["falas"].append(i)
            if "camera" in f:
                seg["chaves"].append((max(seg["ini"], self.ini[i] - 0.15), Camera(*f["camera"])))

    def _cartoes(self):
        self.cartoes = []   # (ini, fim, spec, imagem estática ou None, y)
        for i, f in enumerate(self.falas):
            for c in f.get("cartoes", []):
                a = self.ini[i] + c.get("de", 0.0)
                if "ate" in c:
                    b = self.ini[self.idx[c["ate"]]] - 0.05
                elif "dur" in c:
                    b = a + c["dur"]
                else:
                    b = self.fim_fala(i)
                if "ate" not in c:   # sem "ate", o cartão não atravessa um corte de cena
                    b = min(b, next(s for s in self.segmentos if i in s["falas"])["fim"])
                tipo = c["tipo"]
                y = c.get("y", {"banner": 300, "notificacao": 300, "selo": 330, "numero": 420}.get(tipo, 470))
                im = None
                if tipo == "banner":
                    corf = cor(c.get("cor", "amarelo"))
                    txt = (20, 20, 20) if c.get("cor", "amarelo") in ("amarelo", "branco") else (255, 255, 255)
                    im = banner(c["linhas"], corf, txt, c.get("tam", 86))
                elif tipo == "notificacao":
                    im = notificacao(c["titulo"], c.get("sub", ""), c.get("icone", "ok"), c.get("escuro", False))
                elif tipo == "selo":
                    im = selo(c["texto"], cor(c.get("cor", "vermelho")))
                elif tipo == "numero":
                    im = numero(c["valor"], c.get("sub", ""), cor(c.get("cor", "verde")))
                self.cartoes.append((a, b, c, im, y))

    def _desenhar_cartao(self, spec, a, b, t):
        tipo = spec["tipo"]
        prog = min(1.0, max(0.0, (t - a) / max(0.3, (b - a) * spec.get("ritmo", 0.8))))
        if tipo == "lista":
            escalas = None
            if any(len(it) > 2 for it in spec["itens"]):   # item com id de fala: aparece no início dela
                escalas = [pop((t - (self.ini[self.idx[it[2]]] if len(it) > 2 else a)) / 0.3) if
                           t >= (self.ini[self.idx[it[2]]] if len(it) > 2 else a) else 0.0 for it in spec["itens"]]
            return lista(spec["titulo"], spec["itens"], cor(spec.get("cor", "azul_escuro")), prog, escalas=escalas)
        if tipo == "comparativo":
            return comparativo(spec["esq"], spec["dir"], prog)
        if tipo == "celular":
            alerta_t = self.ini[self.idx[spec["alerta_fala"]]] if "alerta_fala" in spec else a + spec.get("alerta_em", 0.0)
            return celular(spec.get("titulo", "Câmeras"), spec.get("telas", 4),
                           spec.get("alerta") if t >= alerta_t else None, t)
        if tipo == "custom":
            return self.extras[spec["nome"]](self, t, prog)
        raise ValueError(f"tipo de cartão desconhecido: {tipo}")

    # --- quadro
    def estado(self, t):
        seg = next((s for s in self.segmentos if s["ini"] <= t < s["fim"]), self.segmentos[-1])
        c = self.r["cenas"][seg["cena"]]
        cam = V.interpolar_camera(seg["chaves"], t)
        atores = []
        for slug, a in c["atores"].items():
            ator = self.atores[(slug, a["altura"], a.get("flip", False))]
            lv, dx, dy = None, 0.0, 0.0
            for i in seg["falas"]:
                if self.falas[i]["personagem"] == slug:
                    v = self.nivel(i, t)
                    if v is not None:
                        lv = v
                        acao = self.falas[i].get("acao")
                        if acao == "tremor":
                            dx = 4 * np.sin(t * 30)
                        elif acao == "pulo":
                            dy = -16 * abs(np.sin((t - self.ini[i]) * 8))
            atores.append(AtorNaCena(ator, a["x"], a["pe"], lv, dx, dy))
        return seg, c, cam, atores

    def legenda(self, img, t):
        for i, f in enumerate(self.falas):
            if self.ini[i] - 0.05 <= t < self.ini[i] + self.durs[i] + 0.1:
                p = self.pers[f["personagem"]]
                nome = p["nome"].upper() + (f" • {PAPEL[f['personagem']]}" if f["personagem"] in PAPEL else "")
                corn = cor(COR_NOME.get(f["personagem"], "verde"))
                d = ImageDraw.Draw(img)
                fn = fonte(38)
                wn = fn.getlength(nome) + 50
                d.rounded_rectangle((LARG / 2 - wn / 2, 1318, LARG / 2 + wn / 2, 1376), 29, fill=corn)
                d.text((LARG / 2, 1347), nome, font=fn, fill="white", anchor="mm")
                palavras = (f.get("legenda") or sem_tags(f["texto"])).split()
                pedacos = [" ".join(palavras[k:k + 4]) for k in range(0, len(palavras), 4)]
                total = sum(len(x) for x in pedacos)
                ta = self.ini[i]
                for k, txt in enumerate(pedacos):
                    tb = ta + self.durs[i] * len(txt) / total
                    if ta <= t < tb or (k == len(pedacos) - 1 and t >= ta):
                        fnt = fonte(74)
                        for j, l in enumerate(V.texto_quebrado(txt.upper(), fnt, 960)):
                            d.text((LARG / 2, 1450 + j * 88), l, font=fnt, fill="white", anchor="mm",
                                   stroke_width=10, stroke_fill=(15, 15, 15))
                        break
                    ta = tb
                return

    def montar(self, t: float) -> Image.Image:
        seg, c, cam, atores = self.estado(t)
        img = V.quadro(self.cenas[seg["cena"]], cam, atores, t)
        if c.get("filtro") == "noite":
            img.alpha_composite(Image.new("RGBA", img.size, (8, 16, 48, 115)))
        if self.serie is not None and t < self.segmentos[0]["fim"]:
            colar(img, self.serie, LARG / 2, 110, pop(t / 0.3))
        for a, b, spec, im, y in self.cartoes:
            if a <= t < b:
                if im is None:
                    im = self._desenhar_cartao(spec, a, b, t)
                colar(img, im, spec.get("x", LARG / 2), y, pop((t - a) / 0.28), min(1.0, (b - t) / 0.18))
        self.legenda(img, t)
        fin = self.fim_falas - 0.1
        if t >= fin:
            colar(img, self.final, LARG / 2, ALT / 2, 1.0, min(1.0, (t - fin) / 0.4))
        for corte in self.cortes:
            if corte <= t < corte + 0.15:
                img.alpha_composite(Image.new("RGBA", img.size, (255, 255, 255, int(255 * (1 - (t - corte) / 0.15)))))
        return img

    # --- saída
    def renderizar(self, previa: list[float] | None = None):
        self.saida.mkdir(parents=True, exist_ok=True)
        self.preparar()
        if previa:
            for t in previa:
                p = self.saida / f"quadro_{t:05.1f}s.png"
                self.montar(t).convert("RGB").save(p)
                print(p)
            return
        total = np.zeros(int((self.dur + 0.5) * SR), dtype=np.float32)

        def por(sinal, t):
            i = int(t * SR)
            total[i:i + len(sinal)] += sinal[: max(0, len(total) - i)]

        for i, a in enumerate(self.audios):
            por(a, self.ini[i])
        for t in self.cortes:
            por(V.whoosh(), t - 0.15)
        for a, *_ in self.cartoes:
            por(V.blip(), a)
        wav = self.saida / "audio_mix.wav"
        V.salvar_wav(total, wav)
        saida = self.saida / "video.mp4"
        enc = V.Codificador(saida, wav)
        n = int(self.dur * FPS)
        t0 = time.time()
        for i in range(n):
            enc.escrever(self.montar(i / FPS))
            if i % 300 == 0:
                print(f"  quadro {i}/{n}  ({time.time() - t0:.0f}s)", flush=True)
        enc.fechar()
        print(f"Pronto: {saida}  ({self.dur:.1f}s)")


def produzir(arquivo_montagem: str, extras: dict | None = None):
    v = Video(Path(arquivo_montagem).resolve().parent, extras)
    if "--quadros" in sys.argv:
        v.renderizar([float(x) for x in sys.argv[sys.argv.index("--quadros") + 1].split(",")])
    else:
        v.renderizar()
    return v


def listar_falas(slug: str):
    r = json.loads((RAIZ / "videos" / slug / "roteiro.json").read_text(encoding="utf-8"))
    p = personagens()
    for f in r["falas"]:
        print(f["id"], p[f["personagem"]]["voz"]["voice_id"], f["texto"])


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "falas":
        listar_falas(sys.argv[2])
