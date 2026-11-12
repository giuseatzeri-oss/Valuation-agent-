"""Converte lo script testuale della rassegna in MP3 con voce italiana Piper (offline, open-source).
Uso: python3 rassegna/tts.py SCRIPT.txt OUT.mp3"""
import sys, os, subprocess, urllib.request, wave, re
HERE = os.path.dirname(os.path.abspath(__file__))
VOICE = os.environ.get("RASSEGNA_VOICE", "it_IT-paola-medium")
VDIR = os.path.join(HERE, ".voices")
HF = "https://huggingface.co/rhasspy/piper-voices/resolve/main/it/it_IT/{spk}/{q}/{v}.onnx{ext}"

def ensure_voice():
    os.makedirs(VDIR, exist_ok=True)
    _, spk, q = VOICE.split("-")
    for ext in ("", ".json"):
        p = os.path.join(VDIR, VOICE + ".onnx" + ext)
        if not os.path.exists(p):
            urllib.request.urlretrieve(HF.format(spk=spk, q=q, v=VOICE, ext=ext), p)
    return os.path.join(VDIR, VOICE + ".onnx")

def main(src, out):
    from piper import PiperVoice, SynthesisConfig
    voice = PiperVoice.load(ensure_voice())
    text = open(src, encoding="utf-8").read()
    text = re.sub(r"[*_#>`]", "", text)          # niente markdown nella voce
    cfg = SynthesisConfig(length_scale=1.0, noise_scale=0.6, noise_w_scale=0.8)
    wav = out.rsplit(".", 1)[0] + ".wav"
    with wave.open(wav, "wb") as wf:
        first = True
        for para in [p.strip() for p in text.split("\n\n") if p.strip()]:
            for chunk in voice.synthesize(para, syn_config=cfg):
                if first:
                    wf.setnchannels(chunk.sample_channels); wf.setsampwidth(chunk.sample_width)
                    wf.setframerate(chunk.sample_rate); first = False
                wf.writeframes(chunk.audio_int16_bytes)
            wf.writeframes(b"\x00\x00" * int(voice.config.sample_rate * 0.6))  # pausa tra paragrafi
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-codec:a", "libmp3lame",
                    "-b:a", "64k", "-ac", "1", out], check=True)
    os.remove(wav)
    print(out)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
