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

1. No ElevenLabs, abra **Voices → Voice Design** e cole o `prompt_voice_design` do personagem.
2. Teste com a `frase_teste`, salve a voz e copie o **Voice ID** para o campo `voice_id` no `personagens.json`.
3. A chave da API fica no `.env` (`ELEVENLABS_API_KEY=...`), que nunca vai para o Git: este repositório é público.
