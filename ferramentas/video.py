"""Motor de vídeo 2D da Protemaxxi.

Monta vídeos verticais (Reels, 1080x1920) com os cenários e personagens do repositório:
- rasteriza os SVGs com o Google Chrome (headless), em camadas transparentes;
- anima a boca pela intensidade do áudio de cada fala e faz os personagens piscarem;
- move uma câmera virtual (posição e zoom) por cima do cenário;
- desenha legendas e cartões por cima do vídeo e codifica com o ffmpeg.

Precisa de: Google Chrome, Pillow, numpy e imageio-ffmpeg (pip install imageio-ffmpeg).
Cada vídeo tem uma pasta em videos/<slug>/ com roteiro.json e montagem.py.
"""
from __future__ import annotations

import hashlib
import math
import re
import subprocess
import sys
import wave
from dataclasses import dataclass, field
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "ferramentas"))
import gerar_cenarios as gc  # noqa: E402

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
LARG, ALT, FPS = 1080, 1920, 30
SR = 44100
F = 2.5  # pixels do "mundo" por unidade do cenário (cenário 1920x1080 -> 4800x2700)
TINTA = "#2A1E1A"

_CHROMES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
]
CHROME = next((p for p in _CHROMES if Path(p).exists()), None)

_FONTES = {
    "black": ["C:/Windows/Fonts/seguibl.ttf", "C:/Windows/Fonts/arialbd.ttf"],
    "bold": ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf"],
}


def fonte(tam: int, peso: str = "black") -> ImageFont.FreeTypeFont:
    for p in _FONTES[peso]:
        if Path(p).exists():
            return ImageFont.truetype(p, tam)
    return ImageFont.load_default(tam)


# ------------------------------------------------------------------ rasterização
def rasterizar(svg: str, w: int, h: int, cache: Path) -> Image.Image:
    """SVG -> PNG transparente de w x h, com cache por conteúdo."""
    cache.mkdir(parents=True, exist_ok=True)
    chave = hashlib.sha1(f"{w}x{h}|".encode() + svg.encode()).hexdigest()[:20]
    png = cache / f"{chave}.png"
    if not png.exists():
        if CHROME is None:
            raise SystemExit("Google Chrome não encontrado: ele é usado para rasterizar os SVGs.")
        svg2 = re.sub(r'(<svg\b[^>]*?)\swidth="[\d.]+"\s+height="[\d.]+"', rf'\1 width="{w}" height="{h}"', svg, count=1)
        html = cache / f"{chave}.html"
        html.write_text(
            '<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;background:transparent;'
            f'overflow:hidden}}svg{{display:block}}</style></head><body>{svg2}</body></html>',
            encoding="utf-8",
        )
        subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={cache / 'chrome'}",
             "--default-background-color=00000000", f"--window-size={w},{h}", f"--screenshot={png}", html.as_uri()],
            check=True, capture_output=True,
        )
        html.unlink()
    return Image.open(png).convert("RGBA")


def esconder(svg: str, *grupos: str) -> str:
    for g in grupos:
        svg = svg.replace(f'<g id="{g}">', f'<g id="{g}" style="display:none">')
    return svg


def _grupo(svg: str, gid: str) -> tuple[int, int]:
    i = svg.index(f'<g id="{gid}"')
    nivel = 0
    for m in re.finditer(r"<g\b|</g>", svg[i:]):
        nivel += -1 if m.group() == "</g>" else 1
        if nivel == 0:
            return i, i + m.end()
    raise ValueError(gid)


# ------------------------------------------------------------------ personagens
BOCAS = ("fechada", "media", "aberta", "bem")


def trocar_boca(svg: str, tipo: str) -> str:
    a, b = _grupo(svg, "boca")
    g = svg[a:b]
    m = re.search(r"M176 ([\d.]+)", g)
    y = float(m.group(1)) if m else float(re.search(r"M180 ([\d.]+)", g).group(1)) - 2
    if tipo == "fechada":
        novo = (f'<g id="boca"><path d="M180 {y + 2} Q200 {y + 18} 220 {y + 2}" fill="none" stroke="#7A2E34" '
                'stroke-width="5" stroke-linecap="round"/></g>')
    else:
        abre, larg = {"media": (22, 22), "aberta": (32, 24), "bem": (46, 26)}[tipo]
        d = f"M{200 - larg} {y} Q200 {y + abre} {200 + larg} {y} Q200 {y + 5} {200 - larg} {y} Z"
        cid = f"clip-boca-{tipo}"
        novo = (f'<g id="boca"><clipPath id="{cid}"><path d="{d}"/></clipPath><path d="{d}" fill="#6E2630"/>'
                f'<g clip-path="url(#{cid})"><rect x="170" y="{y - 2}" width="60" height="9" fill="#FFF"/>'
                f'<ellipse cx="200" cy="{y + abre * 0.62}" rx="{larg * 0.55}" ry="{abre * 0.22}" fill="#E0707A"/></g>'
                f'<path d="{d}" fill="none" stroke="#5A1A22" stroke-width="3.5" stroke-linejoin="round"/></g>')
    return svg[:a] + novo + svg[b:]


def fechar_olhos(svg: str) -> str:
    a, b = _grupo(svg, "olhos")
    olhos = re.findall(r'<ellipse cx="([\d.]+)" cy="([\d.]+)" rx="10" ry="14"', svg[a:b])
    arcos = "".join(f'<path d="M{float(x) - 12} {float(y) + 2} Q{x} {float(y) + 10} {float(x) + 12} {float(y) + 2}" '
                    f'fill="none" stroke="{TINTA}" stroke-width="5" stroke-linecap="round"/>' for x, y in olhos)
    return svg[:a] + f'<g id="olhos">{arcos}</g>' + svg[b:]


class Ator:
    """Personagem pronto para animar, numa altura (em unidades do cenário) fixa."""

    def __init__(self, slug: str, altura: float, cache: Path, boca_parada: str = "aberta", flip: bool = False):
        self.slug, self.altura, self.boca_parada = slug, altura, boca_parada
        base = (RAIZ / "personagens" / "svg" / f"{slug}.svg").read_text(encoding="utf-8")
        h = round(altura * F)
        w = round(h * 400 / 900)
        self.imgs: dict[tuple[str, bool], Image.Image] = {}
        for boca in BOCAS:
            for piscando in (False, True):
                s = trocar_boca(base, boca)
                if piscando:
                    s = fechar_olhos(s)
                img = rasterizar(s, w, h, cache)
                self.imgs[(boca, piscando)] = img.transpose(Image.FLIP_LEFT_RIGHT) if flip else img
        self.w, self.h = w, h
        # piscadas em momentos pseudoaleatórios, fixos por personagem
        rng = np.random.default_rng(int(hashlib.md5(slug.encode()).hexdigest()[:6], 16))
        self.piscadas = np.cumsum(rng.uniform(2.2, 4.5, 60))

    def piscando(self, t: float) -> bool:
        return bool(np.any((t >= self.piscadas) & (t < self.piscadas + 0.12)))

    def imagem(self, t: float, nivel: float | None) -> Image.Image:
        if nivel is None:
            boca = self.boca_parada
        else:
            boca = "fechada" if nivel < 0.12 else "media" if nivel < 0.35 else "aberta" if nivel < 0.7 else "bem"
        return self.imgs[(boca, self.piscando(t))]


# ------------------------------------------------------------------ cenários
@dataclass
class Cenario:
    fundo: Image.Image                 # camada de trás (atrás dos personagens)
    frente: Image.Image | None = None  # camada da frente (bancada, balcão...)
    extras: dict[str, Image.Image] = field(default_factory=dict)  # variações do fundo


def carregar_cenario(svg: str, cache: Path, frente_grupos: tuple[str, ...] = ()) -> Cenario:
    """Rasteriza um cenário. Os grupos em frente_grupos ficam na frente dos personagens."""
    w, h = round(1920 * F), round(1080 * F)
    if not frente_grupos:
        return Cenario(rasterizar(svg, w, h, cache))
    fundo = rasterizar(esconder(svg, *frente_grupos), w, h, cache)
    tras = [g for g in ("fundo", "chao", "moveis") if g not in frente_grupos]
    frente = rasterizar(esconder(svg, *tras), w, h, cache)
    return Cenario(fundo, frente)


# ------------------------------------------------------------------ áudio
def ler_audio(caminho: Path) -> np.ndarray:
    bruto = subprocess.run([FFMPEG, "-v", "error", "-i", str(caminho), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                           check=True, capture_output=True).stdout
    a = np.frombuffer(bruto, dtype=np.float32).copy()
    voz = np.flatnonzero(np.abs(a) > 0.02)
    if len(voz):
        a = a[max(0, voz[0] - int(0.04 * SR)): voz[-1] + int(0.12 * SR)]
    return a


def envelope(a: np.ndarray) -> np.ndarray:
    """Intensidade 0..1 por quadro do vídeo, para animar a boca."""
    n = int(math.ceil(len(a) / SR * FPS))
    passo = SR / FPS
    rms = np.array([np.sqrt(np.mean(a[int(i * passo): int((i + 1) * passo)] ** 2) + 1e-12) for i in range(n)])
    ref = np.percentile(rms, 90) or 1
    v = np.clip(rms / ref, 0, 1.2)
    return np.convolve(v, [0.25, 0.5, 0.25], mode="same")


def blip(freq=880, dur=0.09, vol=0.12) -> np.ndarray:
    t = np.arange(int(dur * SR)) / SR
    f = freq * (1 + 0.6 * t / dur)
    return (vol * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 30)).astype(np.float32)


def whoosh(dur=0.4, vol=0.10) -> np.ndarray:
    n = int(dur * SR)
    ruido = np.random.default_rng(7).standard_normal(n).astype(np.float32)
    ruido = np.convolve(ruido, np.ones(12) / 12, mode="same")
    env = np.sin(np.linspace(0, np.pi, n)) ** 2
    return (vol * ruido * env / (np.abs(ruido).max() or 1) * 3).astype(np.float32)


def salvar_wav(a: np.ndarray, caminho: Path):
    a = np.clip(a, -1, 1)
    with wave.open(str(caminho), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((a * 32767).astype("<i2").tobytes())


# ------------------------------------------------------------------ desenho 2D (tela)
def suave(x: float) -> float:
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def pop(x: float) -> float:
    """Escala de entrada com leve 'quique' (0 -> 1)."""
    x = min(max(x, 0.0), 1.0)
    c = 1.70158
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def texto_quebrado(txt: str, fnt, larg_max: int) -> list[str]:
    linhas, atual = [], ""
    for p in txt.split():
        teste = f"{atual} {p}".strip()
        if fnt.getlength(teste) <= larg_max or not atual:
            atual = teste
        else:
            linhas.append(atual)
            atual = p
    return linhas + ([atual] if atual else [])


def colar(base: Image.Image, img: Image.Image, cx: float, cy: float, escala: float = 1.0, alfa: float = 1.0):
    if escala <= 0.01 or alfa <= 0.01:
        return
    if abs(escala - 1) > 0.01:
        img = img.resize((max(1, round(img.width * escala)), max(1, round(img.height * escala))), Image.BILINEAR)
    if alfa < 0.99:
        img = img.copy()
        img.putalpha(img.getchannel("A").point(lambda v: int(v * alfa)))
    base.alpha_composite(img, (round(cx - img.width / 2), round(cy - img.height / 2)))


# ------------------------------------------------------------------ câmera e quadro
@dataclass
class Camera:
    cx: float
    cy: float
    zoom: float = 1.0


def interpolar_camera(chaves: list[tuple[float, Camera]], t: float, transicao: float = 0.7) -> Camera:
    atual = chaves[0]
    anterior = None
    for i, (tc, cam) in enumerate(chaves):
        if tc <= t:
            atual = (tc, cam)
            anterior = chaves[i - 1] if i else None
    tc, cam = atual
    if anterior is None:
        return cam
    k = suave((t - tc) / transicao)
    a = anterior[1]
    return Camera(a.cx + (cam.cx - a.cx) * k, a.cy + (cam.cy - a.cy) * k, a.zoom + (cam.zoom - a.zoom) * k)


@dataclass
class AtorNaCena:
    ator: Ator
    x: float            # centro, em unidades do cenário
    pe: float           # linha do chão (pés), em unidades do cenário
    nivel: float | None = None  # intensidade da fala neste quadro (None = calado)
    dx: float = 0.0
    dy: float = 0.0


def quadro(cen: Cenario, cam: Camera, atores: list[AtorNaCena], t: float, fundo_extra: str | None = None) -> Image.Image:
    vis_h = 1080 / cam.zoom
    vis_w = vis_h * LARG / ALT
    x0 = min(max(cam.cx - vis_w / 2, 0), 1920 - vis_w)
    y0 = min(max(cam.cy - vis_h / 2, 0), 1080 - vis_h)
    caixa = (round(x0 * F), round(y0 * F), round((x0 + vis_w) * F), round((y0 + vis_h) * F))
    fundo = cen.extras.get(fundo_extra, cen.fundo) if fundo_extra else cen.fundo
    img = fundo.crop(caixa)
    for a in atores:
        im = a.ator.imagem(t, a.nivel)
        topo = (a.pe + a.dy) - a.ator.altura * 870 / 900
        px = round((a.x + a.dx) * F - im.width / 2) - caixa[0]
        py = round(topo * F) - caixa[1]
        _colar_parcial(img, im, px, py)
    if cen.frente is not None:
        img.alpha_composite(cen.frente.crop(caixa))
    return img.resize((LARG, ALT), Image.BILINEAR)


def _colar_parcial(base: Image.Image, im: Image.Image, px: int, py: int):
    sx, sy = max(0, -px), max(0, -py)
    dx, dy = max(0, px), max(0, py)
    w = min(im.width - sx, base.width - dx)
    h = min(im.height - sy, base.height - dy)
    if w > 0 and h > 0:
        base.alpha_composite(im, (dx, dy), (sx, sy, sx + w, sy + h))


# ------------------------------------------------------------------ codificação
class Codificador:
    def __init__(self, saida: Path, audio: Path):
        self.proc = subprocess.Popen(
            [FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{LARG}x{ALT}", "-r", str(FPS),
             "-i", "-", "-i", str(audio), "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(saida)],
            stdin=subprocess.PIPE,
        )

    def escrever(self, img: Image.Image):
        self.proc.stdin.write(img.convert("RGB").tobytes())

    def fechar(self):
        self.proc.stdin.close()
        if self.proc.wait() != 0:
            raise SystemExit("ffmpeg falhou ao codificar o vídeo")
