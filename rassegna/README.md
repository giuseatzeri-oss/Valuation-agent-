# Rassegna economico-finanziaria del mattino

Blog + podcast in italiano generati ogni mattina da un'attività pianificata di Claude Code.

| File | Ruolo |
|---|---|
| `ISTRUZIONI.md` | Linea editoriale e passi che l'agente segue ogni mattina |
| `fonti.json` | Query Google News RSS per sezione (testate prioritarie dal catalogo MLOL FEEM) |
| `fetch_news.py` | Raccoglie le notizie delle ultime ~36 ore → `news.json` |
| `tts.py` | Voce italiana Piper (offline, open-source) → MP3; scarica la voce in `.voices/` al primo uso |
| `build_html.py` | Impagina il blog in HTML autonomo con il podcast incorporato |

Rete necessaria: `news.google.com` (notizie), `huggingface.co` + CDN `*.hf.co` (download della voce, una volta per container).
Dipendenze: `pip install piper-tts feedparser markdown`, `ffmpeg`.

Per cambiare voce: variabile `RASSEGNA_VOICE` (es. `it_IT-riccardo-x_low`).
