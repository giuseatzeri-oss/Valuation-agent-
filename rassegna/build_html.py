"""Impagina la rassegna (markdown) come post di blog HTML autonomo, con il podcast incorporato.
Uso: python3 rassegna/build_html.py RASSEGNA.md PODCAST.mp3 OUT.html"""
import sys, base64, markdown, re

CSS = """
:root{--bg:#faf8f4;--fg:#1d1d1f;--muted:#6b6b70;--accent:#0b5d4b;--rule:#e4e0d8;--card:#fff}
@media (prefers-color-scheme:dark){:root{--bg:#141517;--fg:#ececec;--muted:#9a9aa0;--accent:#5cc8a8;--rule:#2b2d31;--card:#1c1d20}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:17px/1.65 Georgia,'Iowan Old Style',serif}
main{max-width:720px;margin:0 auto;padding:28px 16px 64px}
.kicker{font:600 12px/1 system-ui,sans-serif;letter-spacing:.12em;text-transform:uppercase;color:var(--accent)}
h1{font-size:30px;line-height:1.2;margin:.4em 0 .2em}h2{font:700 13px/1.3 system-ui,sans-serif;letter-spacing:.1em;text-transform:uppercase;color:var(--accent);border-top:1px solid var(--rule);padding-top:22px;margin-top:34px}
h3{font-size:19px;margin:1.2em 0 .2em}a{color:var(--accent)}
.player{position:sticky;top:0;background:var(--card);border:1px solid var(--rule);border-radius:12px;padding:12px 14px;margin:18px 0 8px;z-index:2}
.player p{margin:0 0 6px;font:600 13px system-ui,sans-serif;color:var(--muted)}audio{width:100%}
blockquote{margin:1em 0;padding:.2em 1em;border-left:3px solid var(--accent);color:var(--muted)}
.src{font:13px system-ui,sans-serif;color:var(--muted)}li{margin:.35em 0}
footer{margin-top:40px;font:12px/1.5 system-ui,sans-serif;color:var(--muted);border-top:1px solid var(--rule);padding-top:14px}
"""

def main(md_path, mp3_path, out):
    md = open(md_path, encoding="utf-8").read()
    md = re.sub(r"\n(Fonti?:)", r"\n\n\1", md)  # fonti in un paragrafo a sé
    title = (re.search(r"^# (.+)$", md, re.M) or [None, "Rassegna del mattino"])[1]
    body = markdown.markdown(re.sub(r"^# .+$", "", md, count=1, flags=re.M), extensions=["extra", "sane_lists"])
    body = re.sub(r"<p>(Fonte|Fonti):", r'<p class="src">\1:', body)
    audio = ""
    if mp3_path and mp3_path != "-":
        b64 = base64.b64encode(open(mp3_path, "rb").read()).decode()
        audio = f'<div class="player"><p>🎧 Ascolta la rassegna</p><audio controls preload="none" src="data:audio/mpeg;base64,{b64}"></audio></div>'
    html = f"""<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>{CSS}</style></head><body><main>
<div class="kicker">Rassegna economico-finanziaria del mattino</div><h1>{title}</h1>{audio}{body}
<footer>Rassegna generata automaticamente da titoli e abstract pubblici (Google News) delle testate prioritarie del catalogo MLOL FEEM. Per gli articoli integrali, apri le testate su feem.medialibrary.it. Verifica sempre i dati prima di usarli in un lavoro di valutazione.</footer>
</main></body></html>"""
    open(out, "w", encoding="utf-8").write(html)
    print(out)

if __name__ == "__main__":
    main(*sys.argv[1:4])
