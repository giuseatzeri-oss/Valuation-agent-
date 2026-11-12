# Rassegna economico-finanziaria del mattino — istruzioni per l'agente

Ogni mattina produci **un post di blog** (da leggere) e **un podcast** (da ascoltare) in italiano.
Il lettore è un professionista della valutazione d'azienda (corporate finance, private equity, real estate, hospitality) basato in Italia.

## Passi

1. Prepara l'ambiente (se serve): `pip install -q piper-tts feedparser markdown`
2. Data e cartella di lavoro:
   `D=$(TZ=Europe/Rome date +%F); OUT=/tmp/rassegna/$D; mkdir -p $OUT`
3. Raccogli le notizie: `python3 rassegna/fetch_news.py $OUT/news.json`
4. Leggi `$OUT/news.json` e scegli le notizie (vedi "Linea editoriale").
   Se una notizia importante ha solo il titolo e i dettagli sono necessari, puoi approfondire con uno strumento di ricerca web disponibile (Perplexity, Firecrawl o WebSearch). Se nessuno è disponibile, resta sui titoli.
5. Scrivi `$OUT/rassegna.md` (il blog) e `$OUT/podcast.txt` (il testo per la voce) seguendo i formati qui sotto.
6. Genera l'audio: `python3 rassegna/tts.py $OUT/podcast.txt $OUT/podcast-$D.mp3`
7. Impagina il blog: `python3 rassegna/build_html.py $OUT/rassegna.md $OUT/podcast-$D.mp3 $OUT/rassegna-$D.html`
8. Consegna con **SendUserFile** (`status: "proactive"`): prima `rassegna-$D.html` (`display: "render"`), poi `podcast-$D.mp3` (`display: "attach"`). Caption: una riga con le 3 notizie di apertura.
9. Non fare commit, non aprire PR, non modificare il repository.

## Linea editoriale

- **Priorità delle fonti** (dal catalogo MLOL FEEM, `research/mlol-feem/README.md`): Milano Finanza/MF, Il Sole 24 Ore, ItaliaOggi, L'Economia/Corriere, WSJ, Barron's, The Economist; per i settori: BeBeez, Requadro, TTG Italia, Italia a Tavola, Hospitality Net e testate specializzate equivalenti.
- **Priorità dei temi**: (1) operazioni di PE/M&A con un nesso con l'Italia; (2) real estate istituzionale (fondi, SGR, transazioni, yield, logistica, uffici, living); (3) hospitality (compravendite di hotel, aperture, gestori, RevPAR, turismo); (4) mercati e macro che spostano tassi, multipli e costo del capitale (BCE, Fed, BTP/spread, Ftse Mib); (5) grandi notizie societarie.
- Scarta: gossip, sport, lifestyle, comunicati minori, duplicati della stessa notizia da fonti diverse (tieni la fonte più autorevole).
- **Mai inventare** cifre, nomi o valori delle operazioni. Riporta solo quello che è nel titolo o in una fonte che hai effettivamente letto. Se un dato è incerto, scrivi "secondo [fonte]".
- Se in una sezione non ci sono notizie rilevanti nelle ultime 24 ore, scrivilo in una riga invece di riempire.
- Per ogni notizia aggiungi "Perché conta" in ottica di valutazione (multipli, tassi, comparabili, settore), in una frase, senza speculare oltre i fatti.

## Formato del blog (`rassegna.md`)

```
# [Giorno della settimana] [giorno] [mese] [anno]

> **In tre righe:** [le 3 notizie di apertura, una riga ciascuna]

## Mercati e macro
### [Titolo notizia riscritto, chiaro]
[2–3 frasi.] **Perché conta:** [1 frase.]
Fonte: [Testata](link)

## Private equity e M&A
...
## Real estate
...
## Hospitality e turismo
...
## Da tenere d'occhio oggi
- [eventi/dati in agenda se emergono dalle notizie: riunioni banche centrali, trimestrali, aste]

## Da leggere su MLOL
- [2–4 testate del catalogo FEEM in cui approfondire le notizie del giorno, con link alle schede in research/mlol-feem/catalogo_rilevante.csv]
```
Lunghezza: 12–18 notizie in totale, 700–1.100 parole.

## Formato del podcast (`podcast.txt`)

- Testo parlato, in prosa, **senza** markdown, elenchi, link o simboli. Paragrafi separati da una riga vuota (la voce fa una pausa).
- Apertura: "Buongiorno, è [giorno] [data]. Questa è la tua rassegna economico-finanziaria." Poi un sommario di 3 notizie.
- Poi le sezioni nello stesso ordine del blog, con brevi transizioni ("Passiamo al private equity.").
- Chiusura: "È tutto per oggi. Buona giornata e buon lavoro."
- **Numeri scritti per esteso** quando sono decimali o percentuali ("meno zero virgola trentadue per cento", "diciotto virgola otto milioni di euro"); sigle pronunciabili ("Ftse Mib", "B C E" se serve). Niente URL.
- Lunghezza: 1.100–1.400 parole (circa 8–10 minuti).
