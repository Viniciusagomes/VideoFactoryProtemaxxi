# Video Factory Protemaxxi

Fábrica de vídeos 2D da Protemaxxi: personagens, roteiros e vozes (ElevenLabs).

## Estrutura

- `personagens/` — elenco fixo dos vídeos.
  - `personagens.json` — ficha de cada personagem: visual, personalidade e voz (prompt do Voice Design, configurações e `voice_id`).
  - `svg/` — desenho 2D de cada personagem, com grupos nomeados (`olhos`, `boca`, `braco-esq`, `braco-dir`, `cabeca`...) para animação.
  - `folha.html` — página de revisão com todos lado a lado (abrir no navegador).
- `ferramentas/gerar_personagens.py` — gera os SVGs e a folha. Para mudar um personagem, edite a função dele e rode:

  ```
  python ferramentas/gerar_personagens.py
  ```
- `cenarios/` — cenários 2D (1920x1080) no mesmo estilo dos personagens.
  - `cenarios.json` — nome, descrição, personagens sugeridos e `chao_y` (altura onde ficam os pés).
  - `svg/` — loja (interior e painel de demonstração), estoque/expedição, fachada, casa da Fernanda, casa do Seu Antônio, campo do instalador e central de suporte.
  - `folha.html` — revisão de todos os cenários.
- `ferramentas/gerar_cenarios.py` — gera os cenários e a folha.
- `assets/marca/` — ícone e logotipo da Protemaxxi usados nos uniformes.
- `ferramentas/video.py` — motor dos vídeos: rasteriza cenários e personagens no Chrome, anima boca (pelo áudio) e piscadas, move a câmera virtual, desenha legendas e cartões e codifica o MP4.
- `videos/<slug>/` — um vídeo por pasta:
  - `roteiro.json` — falas (personagem, cena e texto com a direção de tom para o `eleven_v4`).
  - `montagem.py` — coreografia: câmera, posição dos personagens, cartões e legendas.

## Vídeos

Precisa de Google Chrome, Python com `pillow`, `numpy` e `imageio-ffmpeg` (`pip install pillow numpy imageio-ffmpeg`).

1. Gere cada fala do `roteiro.json` no ElevenLabs com a voz do personagem e salve em `saida/<slug>/audio/f01.mp3`, `f02.mp3`...
2. Revise alguns quadros: `python videos/<slug>/montagem.py --quadros 3,20,45`
3. Gere o vídeo: `python videos/<slug>/montagem.py` → `saida/<slug>/video.mp4` (a pasta `saida/` não vai para o Git).

| Vídeo | Tema | Duração |
|---|---|---|
| `01-configura-na-bancada` | Instalador: configurar a câmera Wi-Fi na bancada antes de fixar no alto | ~1 min |
| `02-poe-um-cabo-so` | Caio (suporte) explica o PoE com o switch HAIZ HZ-1006P-EA2 | ~1 min |

## Elenco

| Personagem | Papel | Voz |
|---|---|---|
| Vinícius | Apresentador geral | voz clonada do próprio Vinícius |
| Marcão | Instalador | masculina, 40-45, grave e calma |
| Rodrigo | Vendedor | masculina, 30-35, carismática |
| Luana | Estoquista | feminina, 24-28, enérgica |
| Caio | Suporte técnico | masculina, 25-28, nerd e didática |
| Seu Antônio | Cliente (comerciante) | masculina, 60-68, rouca e desconfiada |
| Fernanda | Cliente (moradora e empreendedora) | feminina, 32-38, clara e decidida |

## Vozes (ElevenLabs)

Todos os personagens já têm `voice_id` no `personagens.json`: o Vinícius usa a voz clonada, e os outros usam vozes brasileiras da biblioteca do ElevenLabs. Gere as falas com o modelo `eleven_v4` e comece cada fala com uma direção de tom entre colchetes, ex.: `[calmo, conversando]`.

Para trocar uma voz, troque o `voice_id` na ficha do personagem. O `prompt_voice_design` descreve o perfil de voz buscado e serve para procurar outra na biblioteca ou criar uma no Voice Design.

A chave da API fica no `.env` (`ELEVENLABS_API_KEY=...`), que nunca vai para o Git: este repositório é público.
