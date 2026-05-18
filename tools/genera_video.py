#!/usr/bin/env python3
"""
Genera un video 9:16 (1080x1920) partendo da:
- testo della favola (.txt)
- immagine quadrata del protagonista (.png/.jpg)
- voce ElevenLabs (richiede ELEVENLABS_API_KEY)

Output:
- audio/<slug>.mp3   (solo audio, per modalita podcast)
- video/<slug>.mp4   (video con immagine + titolo + sottotitoli + watermark)
"""
import argparse
import base64
import os
import re
import subprocess
import sys
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

ELEVENLABS_API = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"
DEFAULT_VOICE = "3DPhHWXDY263XJ1d2EPN"
DEFAULT_MODEL = "eleven_multilingual_v2"

# Layout video 9:16
W, H = 1080, 1920
IMG_TOP = 0
IMG_SIZE = 1080
TITLE_AREA = (1080, 1240)
SUBS_AREA = (1240, 1820)
WATERMARK_AREA = (1820, 1920)

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def slugify(s):
    s = re.sub(r"[^\w\s-]", "", s.lower())
    s = re.sub(r"[\s_-]+", "-", s)
    return s.strip("-")


def fmt_srt_time(s):
    h, rem = divmod(int(s), 3600)
    m, sec = divmod(rem, 60)
    ms = int((s - int(s)) * 1000)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


def genera_audio_e_timestamps(testo, voice_id, api_key, out_mp3):
    url = ELEVENLABS_API.format(voice_id=voice_id)
    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
    body = {
        "text": testo,
        "model_id": DEFAULT_MODEL,
        "output_format": "mp3_44100_128",
    }
    print(f"  Chiamata ElevenLabs ({len(testo)} caratteri)...")
    r = requests.post(url, headers=headers, json=body, timeout=180)
    if r.status_code != 200:
        sys.exit(f"  Errore ElevenLabs {r.status_code}: {r.text[:300]}")
    data = r.json()
    audio_bytes = base64.b64decode(data["audio_base64"])
    out_mp3.write_bytes(audio_bytes)
    print(f"  MP3 salvato: {out_mp3.name} ({len(audio_bytes)/1024:.0f} KB)")
    return data["alignment"]


def char_to_word_timestamps(alignment):
    """Aggrega timestamp di caratteri in parole intere."""
    chars = alignment["characters"]
    starts = alignment["character_start_times_seconds"]
    ends = alignment["character_end_times_seconds"]
    parole = []
    buf = []
    p_start = None
    p_end = None
    for c, s, e in zip(chars, starts, ends):
        if c.isspace() or c in '.,!?;:"“”()[]…':
            if buf:
                parole.append({"testo": "".join(buf), "start": p_start, "end": p_end})
                buf = []
                p_start = None
            # Punteggiatura che chiude frase: estendi end della parola precedente
            if parole and c in ".!?":
                parole[-1]["end"] = e
        else:
            if p_start is None:
                p_start = s
            buf.append(c)
            p_end = e
    if buf:
        parole.append({"testo": "".join(buf), "start": p_start, "end": p_end})
    return parole


def genera_srt(parole, out_srt, max_parole=6, max_chars=42):
    chunks = []
    current = []
    cur_chars = 0
    for p in parole:
        if current and (
            len(current) >= max_parole or cur_chars + len(p["testo"]) > max_chars
        ):
            chunks.append(current)
            current = []
            cur_chars = 0
        current.append(p)
        cur_chars += len(p["testo"]) + 1
    if current:
        chunks.append(current)

    lines = []
    for i, chunk in enumerate(chunks, 1):
        start = chunk[0]["start"]
        end = chunk[-1]["end"]
        text = " ".join(p["testo"] for p in chunk)
        lines.append(f"{i}\n{fmt_srt_time(start)} --> {fmt_srt_time(end)}\n{text}\n")
    out_srt.write_text("\n".join(lines), encoding="utf-8")
    print(f"  SRT generato: {out_srt.name} ({len(chunks)} sottotitoli)")


def wrap_titolo(testo, draw, font, max_width):
    """Spezza il titolo su 2 righe se non entra."""
    if draw.textbbox((0, 0), testo, font=font)[2] <= max_width:
        return [testo]
    parole = testo.split()
    riga1, riga2 = [], []
    for p in parole:
        candidato = " ".join(riga1 + [p])
        if draw.textbbox((0, 0), candidato, font=font)[2] <= max_width:
            riga1.append(p)
        else:
            riga2.append(p)
    return [" ".join(riga1), " ".join(riga2)] if riga2 else [" ".join(riga1)]


def crea_sfondo(img_path, titolo, out_path):
    # Gradiente notturno
    bg = Image.new("RGB", (W, H))
    gd = ImageDraw.Draw(bg)
    for y in range(H):
        t = y / H
        r = int(26 - 18 * t)
        g = int(26 - 20 * t)
        b = int(46 - 26 * t)
        gd.line([(0, y), (W, y)], fill=(r, g, b))

    # Immagine quadrata in alto (crop+resize per riempire 1080x1080)
    img = Image.open(img_path).convert("RGB")
    s = min(img.size)
    left = (img.width - s) // 2
    top = (img.height - s) // 2
    img = img.crop((left, top, left + s, top + s)).resize(
        (IMG_SIZE, IMG_SIZE), Image.LANCZOS
    )
    bg.paste(img, (0, IMG_TOP))

    draw = ImageDraw.Draw(bg)

    # Titolo
    font_size = 58
    while font_size >= 40:
        font_titolo = ImageFont.truetype(FONT_BOLD, font_size)
        righe = wrap_titolo(titolo, draw, font_titolo, W - 80)
        if len(righe) <= 2:
            break
        font_size -= 6

    altezza_riga = font_size + 10
    altezza_totale = altezza_riga * len(righe)
    y_start = TITLE_AREA[0] + (TITLE_AREA[1] - TITLE_AREA[0] - altezza_totale) // 2
    for i, riga in enumerate(righe):
        bbox = draw.textbbox((0, 0), riga, font=font_titolo)
        w_text = bbox[2] - bbox[0]
        draw.text(
            ((W - w_text) // 2, y_start + i * altezza_riga),
            riga,
            fill="#f4d35e",
            font=font_titolo,
        )

    # Watermark
    font_wm = ImageFont.truetype(FONT_REG, 28)
    wm = "favoleperdormire.it"
    bbox = draw.textbbox((0, 0), wm, font=font_wm)
    w_text = bbox[2] - bbox[0]
    draw.text(
        ((W - w_text) // 2, WATERMARK_AREA[0] + 30),
        wm,
        fill="#9ba4b5",
        font=font_wm,
    )

    bg.save(out_path, "PNG")
    print(f"  Sfondo creato: {out_path.name}")


def crea_video(sfondo, mp3, srt, out_mp4):
    margin_v = H - SUBS_AREA[1] + 20
    style = (
        "FontName=DejaVu Sans,FontSize=38,PrimaryColour=&Hffffff,"
        "OutlineColour=&H000000,BackColour=&Hcc1a1a2e,"
        "BorderStyle=4,Outline=2,Shadow=0,"
        f"MarginV={margin_v},MarginL=60,MarginR=60,"
        "Alignment=2,Spacing=0.5,Bold=1"
    )
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", "25",
        "-i", str(sfondo),
        "-i", str(mp3),
        "-vf", f"subtitles={srt}:force_style='{style}'",
        "-c:v", "libx264", "-preset", "fast", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(out_mp4),
    ]
    print("  Composizione video con ffmpeg...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"  Errore ffmpeg:\n{r.stderr[-800:]}")
    print(f"  MP4 salvato: {out_mp4.name}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--testo", required=True)
    p.add_argument("--immagine", required=True)
    p.add_argument("--titolo", default=None)
    p.add_argument("--voice-id", default=DEFAULT_VOICE)
    p.add_argument("--out-dir", default=".")
    p.add_argument("--api-key", default=None)
    args = p.parse_args()

    api_key = args.api_key or os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        sys.exit("ELEVENLABS_API_KEY non impostata.")

    testo_path = Path(args.testo)
    img_path = Path(args.immagine)
    out_root = Path(args.out_dir)

    if not testo_path.exists():
        sys.exit(f"File testo non trovato: {testo_path}")
    if not img_path.exists():
        sys.exit(f"Immagine non trovata: {img_path}")

    raw = testo_path.read_text(encoding="utf-8").strip()

    # Titolo: prima riga se corta, altrimenti dal nome file
    righe = [r.strip() for r in raw.split("\n") if r.strip()]
    if args.titolo:
        titolo = args.titolo
        testo = raw
    elif righe and len(righe[0]) < 60:
        titolo = righe[0]
        # Rimuovi titolo + eventuale sottotitolo (seconda riga in italico/spiegazione)
        body_start = raw.find(righe[0]) + len(righe[0])
        testo = raw[body_start:].strip()
    else:
        titolo = testo_path.stem.replace("-", " ").title()
        testo = raw

    slug = slugify(testo_path.stem)
    print(f"\n=== {titolo} ===")
    print(f"Slug: {slug}")
    print(f"Caratteri da generare: {len(testo)}")

    audio_dir = out_root / "audio"
    video_dir = out_root / "video"
    tmp_dir = out_root / ".tmp_video"
    audio_dir.mkdir(parents=True, exist_ok=True)
    video_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    mp3 = audio_dir / f"{slug}.mp3"
    srt = tmp_dir / f"{slug}.srt"
    sfondo = tmp_dir / f"{slug}-sfondo.png"
    mp4 = video_dir / f"{slug}.mp4"

    alignment = genera_audio_e_timestamps(testo, args.voice_id, api_key, mp3)
    parole = char_to_word_timestamps(alignment)
    print(f"  Parole estratte: {len(parole)}")
    genera_srt(parole, srt)
    crea_sfondo(img_path, titolo, sfondo)
    crea_video(sfondo, mp3, srt, mp4)

    # Cleanup file intermedi
    for f in tmp_dir.iterdir():
        f.unlink()
    tmp_dir.rmdir()

    print(f"\nFatto!")
    print(f"  audio/{mp3.name}")
    print(f"  video/{mp4.name}")


if __name__ == "__main__":
    main()
