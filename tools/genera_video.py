#!/usr/bin/env python3
"""
Genera un video 9:16 (1080x1920) partendo da:
- testo della favola (.txt)
- immagine quadrata del protagonista (.png/.jpg)
- voce ElevenLabs (richiede ELEVENLABS_API_KEY)

Output:
- audio/<slug>.mp3   (solo audio, per modalita podcast)
- video/<slug>.mp4   (video con immagine + titolo + sottotitoli + branding)

Branding: font Pacifico per il titolo, Coming Soon per i sottotitoli,
palette blu navy #103f65 + oro #ad9853, logo gufetto in basso.
Sottotitoli renderizzati via formato ASS con PlayResY=1920 esplicito
(coordinate in pixel veri, niente scaling imprevedibile di libass).
"""
import argparse
import base64
import os
import random
import re
import subprocess
import sys
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ELEVENLABS_API = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"
DEFAULT_VOICE = "3DPhHWXDY263XJ1d2EPN"
DEFAULT_MODEL = "eleven_multilingual_v2"

# ====== BRAND ======
BRAND_BLU = (16, 63, 101)          # #103f65
BRAND_BLU_SCURO = (8, 30, 50)
BRAND_ORO = (173, 152, 83)         # #ad9853

# ====== FONT (committati nel repo) ======
REPO_ROOT = Path(__file__).resolve().parent.parent
FONT_TITOLO = REPO_ROOT / "assets/fonts/Pacifico-Regular.ttf"
FONT_SOTT = REPO_ROOT / "assets/fonts/ComingSoon-Regular.ttf"
LOGO_PATH = REPO_ROOT / "assets/branding/logo.png"

# ====== LAYOUT VIDEO 9:16 (in pixel) ======
W, H = 1080, 1920
TITLE_AREA = (30, 250)             # 220 px titolo, leggermente piu in alto
IMG_TOP = 290                       # immagine subito sotto il titolo
IMG_SIZE = 880                      # immagine 880x880
IMG_LEFT = (W - IMG_SIZE) // 2
IMG_CORNER_RADIUS = 60
SUBS_AREA = (1210, 1730)            # 520 px area sottotitoli
FOOTER_AREA = (1740, 1920)          # 180 px footer

# ====== VOCE ======
VOICE_SPEED = 0.92
VOICE_STABILITY = 0.40
VOICE_SIMILARITY = 0.75
VOICE_STYLE = 0.45
PITCH_FACTOR = 0.97                 # -0.5 semitoni
PAUSA_FRASE_SEC = 0.35

# ====== SOTTOTITOLI (ASS style in pixel veri) ======
SUBS_FONTSIZE = 84                  # piu grande (era 72)
SUBS_OUTLINE = 5
SUBS_MAX_PAROLE = 4
SUBS_MAX_CHARS = 26
SUBS_MARGIN_L = 60
SUBS_MARGIN_R = 60

# ====== LOGO ======
LOGO_HEIGHT = 160                   # piu grande (era 130)


def slugify(s):
    s = re.sub(r"[^\w\s-]", "", s.lower())
    s = re.sub(r"[\s_-]+", "-", s)
    return s.strip("-")


def fmt_ass_time(s):
    """ASS time format: H:MM:SS.cs (centiseconds)."""
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = s % 60
    return f"{h}:{m:02d}:{sec:05.2f}"


def aggiungi_pause_narrative(testo, pausa_sec=PAUSA_FRASE_SEC):
    """Inserisce <break time="X"/> dopo ogni punto/exclamativo/interrogativo."""
    return re.sub(
        r'([.!?])(\s+)(?=[A-ZÀÈÉÌÒÙ"“])',
        rf'\1 <break time="{pausa_sec}s"/>\2',
        testo,
    )


def genera_audio_e_timestamps(testo, voice_id, api_key, out_mp3):
    url = ELEVENLABS_API.format(voice_id=voice_id)
    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
    body = {
        "text": testo,
        "model_id": DEFAULT_MODEL,
        "output_format": "mp3_44100_128",
        "voice_settings": {
            "stability": VOICE_STABILITY,
            "similarity_boost": VOICE_SIMILARITY,
            "style": VOICE_STYLE,
            "use_speaker_boost": True,
            "speed": VOICE_SPEED,
        },
    }
    print(f"  Chiamata ElevenLabs ({len(testo)} caratteri, speed={VOICE_SPEED}, style={VOICE_STYLE})...")
    r = requests.post(url, headers=headers, json=body, timeout=180)
    if r.status_code != 200:
        sys.exit(f"  Errore ElevenLabs {r.status_code}: {r.text[:300]}")
    data = r.json()
    audio_bytes = base64.b64decode(data["audio_base64"])
    out_mp3.write_bytes(audio_bytes)
    print(f"  MP3 raw salvato: {out_mp3.name} ({len(audio_bytes)/1024:.0f} KB)")
    return data["alignment"]


def pitch_shift_audio(mp3_in, mp3_out, pitch_factor=PITCH_FACTOR):
    """Abbassa il pitch dell'audio mantenendo durata invariata."""
    if abs(pitch_factor - 1.0) < 0.005:
        # Niente shift: copia diretta
        cmd = ["ffmpeg", "-y", "-i", str(mp3_in), "-c:a", "copy", str(mp3_out)]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"  Nessun pitch shift (factor=1.0)")
        return
    tempo = 1.0 / pitch_factor
    cmd = [
        "ffmpeg", "-y", "-i", str(mp3_in),
        "-af", f"asetrate=44100*{pitch_factor},aresample=44100,atempo={tempo:.4f}",
        "-c:a", "libmp3lame", "-b:a", "128k",
        str(mp3_out),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"  Errore pitch shift:\n{r.stderr[-400:]}")
    print(f"  Pitch shift applicato ({(1-pitch_factor)*-12:.1f} semitoni)")


def char_to_word_timestamps(alignment):
    chars = alignment["characters"]
    starts = alignment["character_start_times_seconds"]
    ends = alignment["character_end_times_seconds"]
    parole = []
    buf = []
    p_start = None
    p_end = None
    in_tag = False  # skippa i caratteri dentro <...> (tag SSML come <break.../>)

    for c, s, e in zip(chars, starts, ends):
        if c == "<":
            in_tag = True
            if buf:
                parole.append({"testo": "".join(buf), "start": p_start, "end": p_end})
                buf = []
                p_start = None
            continue
        if c == ">":
            in_tag = False
            continue
        if in_tag:
            continue
        if c.isspace() or c in '.,!?;:"“”()[]…':
            if buf:
                parole.append({"testo": "".join(buf), "start": p_start, "end": p_end})
                buf = []
                p_start = None
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


def genera_ass(parole, out_ass, max_parole=SUBS_MAX_PAROLE, max_chars=SUBS_MAX_CHARS):
    """Genera file ASS con PlayRes esplicito = pixel video reali."""
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

    # Posizione sottotitoli: centro orizzontale, MarginV in pixel dal basso
    centro_subs = (SUBS_AREA[0] + SUBS_AREA[1]) // 2
    margin_v_px = H - centro_subs

    # Colori ASS: &HAABBGGRR (alpha 00 = opaco, FF = trasparente)
    primary = "&H00FFFFFF"           # bianco opaco
    outline_color = "&H00081428"     # blu navy scuro outline
    back = "&H00000000"              # non usato (BorderStyle=1)

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Coming Soon,{SUBS_FONTSIZE},{primary},&H000000FF,{outline_color},{back},0,0,0,0,100,100,0,0,1,{SUBS_OUTLINE},2,2,{SUBS_MARGIN_L},{SUBS_MARGIN_R},{margin_v_px},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events = []
    for chunk in chunks:
        start = chunk[0]["start"]
        end = chunk[-1]["end"]
        text = " ".join(p["testo"] for p in chunk)
        events.append(
            f"Dialogue: 0,{fmt_ass_time(start)},{fmt_ass_time(end)},Default,,0,0,0,,{text}"
        )

    out_ass.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
    print(f"  ASS generato: {out_ass.name} ({len(chunks)} sottotitoli, font {SUBS_FONTSIZE}px)")


def wrap_titolo(testo, draw, font, max_width):
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


def arrotonda_angoli(img, radius):
    """Ritorna l'immagine con angoli arrotondati (RGBA)."""
    mask = Image.new("L", img.size, 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle((0, 0, img.size[0], img.size[1]), radius=radius, fill=255)
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.paste(img.convert("RGBA"), (0, 0))
    out.putalpha(mask)
    return out


def crea_sfondo(img_path, titolo, out_path):
    """Crea PNG 1080x1920 con titolo in alto, immagine arrotondata, footer."""
    bg = Image.new("RGB", (W, H))
    gd = ImageDraw.Draw(bg)

    # Gradiente notturno brand
    for y in range(H):
        t = y / H
        r = int(BRAND_BLU[0] - (BRAND_BLU[0] - BRAND_BLU_SCURO[0]) * t)
        g = int(BRAND_BLU[1] - (BRAND_BLU[1] - BRAND_BLU_SCURO[1]) * t)
        b = int(BRAND_BLU[2] - (BRAND_BLU[2] - BRAND_BLU_SCURO[2]) * t)
        gd.line([(0, y), (W, y)], fill=(r, g, b))

    # Stelline nella zona sotto l'immagine (atmosfera notturna)
    random.seed(7)
    stars_top = IMG_TOP + IMG_SIZE + 30
    for _ in range(70):
        x = random.randint(0, W)
        y = random.randint(stars_top, H - 30)
        s = random.choice([1, 1, 2])
        brightness = random.randint(140, 210)
        gd.ellipse([x - s, y - s, x + s, y + s], fill=(brightness, brightness, brightness))

    draw = ImageDraw.Draw(bg)

    # === TITOLO IN ALTO in Pacifico oro ===
    font_size = 84
    while font_size >= 48:
        font_titolo = ImageFont.truetype(str(FONT_TITOLO), font_size)
        righe = wrap_titolo(titolo, draw, font_titolo, W - 100)
        if len(righe) <= 2:
            break
        font_size -= 6

    altezza_riga = int(font_size * 1.05)
    altezza_totale = altezza_riga * len(righe)
    y_start = TITLE_AREA[0] + (TITLE_AREA[1] - TITLE_AREA[0] - altezza_totale) // 2
    for i, riga in enumerate(righe):
        bbox = draw.textbbox((0, 0), riga, font=font_titolo)
        w_text = bbox[2] - bbox[0]
        x = (W - w_text) // 2
        y = y_start + i * altezza_riga
        for ox, oy in [(3, 3), (-3, 3), (3, -3), (-3, -3)]:
            draw.text((x + ox, y + oy), riga, fill=(0, 0, 0), font=font_titolo)
        draw.text((x, y), riga, fill=BRAND_ORO, font=font_titolo)

    # === IMMAGINE quadrata centrata con angoli arrotondati + ombra ===
    img = Image.open(img_path).convert("RGB")
    s = min(img.size)
    left = (img.width - s) // 2
    top = (img.height - s) // 2
    img = img.crop((left, top, left + s, top + s)).resize((IMG_SIZE, IMG_SIZE), Image.LANCZOS)
    img_rounded = arrotonda_angoli(img, IMG_CORNER_RADIUS)

    # Ombra morbida dietro l'immagine
    shadow = Image.new("RGBA", (IMG_SIZE + 80, IMG_SIZE + 80), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((40, 40, IMG_SIZE + 40, IMG_SIZE + 40), radius=IMG_CORNER_RADIUS, fill=(0, 0, 0, 140))
    shadow = shadow.filter(ImageFilter.GaussianBlur(20))
    bg.paste(shadow, (IMG_LEFT - 40, IMG_TOP - 30), shadow)
    bg.paste(img_rounded, (IMG_LEFT, IMG_TOP), img_rounded)
    draw = ImageDraw.Draw(bg)

    # === FOOTER: logo gufetto + testo brand ===
    footer_y_centro = (FOOTER_AREA[0] + FOOTER_AREA[1]) // 2
    has_logo = LOGO_PATH.exists()
    if has_logo:
        try:
            logo = Image.open(LOGO_PATH).convert("RGBA")
            logo_h = LOGO_HEIGHT
            logo_w = int(logo.width * (logo_h / logo.height))
            logo = logo.resize((logo_w, logo_h), Image.LANCZOS)
            font_wm = ImageFont.truetype(str(FONT_SOTT), 44)
            wm = "favoleperdormire.it"
            bbox = draw.textbbox((0, 0), wm, font=font_wm)
            wm_w = bbox[2] - bbox[0]
            gap = 30
            total_w = logo_w + gap + wm_w
            x_start = (W - total_w) // 2
            bg.paste(logo, (x_start, footer_y_centro - logo_h // 2), logo)
            draw = ImageDraw.Draw(bg)
            draw.text(
                (x_start + logo_w + gap, footer_y_centro - 22),
                wm,
                fill=BRAND_ORO,
                font=font_wm,
            )
        except Exception as ex:
            print(f"  ATTENZIONE: errore caricamento logo ({ex}), uso solo testo")
            has_logo = False

    if not has_logo:
        font_wm = ImageFont.truetype(str(FONT_SOTT), 44)
        wm = "favoleperdormire.it"
        bbox = draw.textbbox((0, 0), wm, font=font_wm)
        wm_w = bbox[2] - bbox[0]
        draw.text(((W - wm_w) // 2, footer_y_centro - 24), wm, fill=BRAND_ORO, font=font_wm)

    bg.save(out_path, "PNG")
    print(f"  Sfondo creato: {Path(out_path).name} (logo {'incluso' if has_logo else 'mancante, solo testo'})")


def crea_video(sfondo, mp3, ass, out_mp4, fonts_dir):
    """FFmpeg: combina sfondo + audio + sottotitoli ASS."""
    vf = f"subtitles={ass}:fontsdir={fonts_dir}"
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", "25",
        "-i", str(sfondo),
        "-i", str(mp3),
        "-vf", vf,
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

    if not FONT_TITOLO.exists():
        sys.exit(f"Font titolo mancante: {FONT_TITOLO}")
    if not FONT_SOTT.exists():
        sys.exit(f"Font sottotitoli mancante: {FONT_SOTT}")

    testo_path = Path(args.testo)
    img_path = Path(args.immagine)
    out_root = Path(args.out_dir)

    if not testo_path.exists():
        sys.exit(f"File testo non trovato: {testo_path}")
    if not img_path.exists():
        sys.exit(f"Immagine non trovata: {img_path}")

    raw = testo_path.read_text(encoding="utf-8").strip()
    righe = [r.strip() for r in raw.split("\n") if r.strip()]
    if args.titolo:
        titolo = args.titolo
        testo = raw
    elif righe and len(righe[0]) < 60:
        titolo = righe[0]
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

    mp3_raw = tmp_dir / f"{slug}-raw.mp3"
    mp3 = audio_dir / f"{slug}.mp3"
    ass = tmp_dir / f"{slug}.ass"
    sfondo = tmp_dir / f"{slug}-sfondo.png"
    mp4 = video_dir / f"{slug}.mp4"

    # Aggiungi pause dopo ogni . ! ? nel testo storia
    testo_con_pause = aggiungi_pause_narrative(testo)

    # Struttura: [pausa] titolo [pausa lunga] storia [pausa finale]
    testo_per_api = (
        f'<break time="0.6s"/> {titolo}. '
        f'<break time="1.0s"/> {testo_con_pause} '
        f'<break time="1.0s"/>'
    )
    parole_titolo = len(titolo.split())
    n_pause_extra = testo_con_pause.count("<break")
    print(f"  Struttura: pausa -> '{titolo}' ({parole_titolo} parole) -> pausa -> storia ({n_pause_extra} pause extra)")

    alignment = genera_audio_e_timestamps(testo_per_api, args.voice_id, api_key, mp3_raw)
    parole_tutte = char_to_word_timestamps(alignment)
    parole_storia = parole_tutte[parole_titolo:]
    print(f"  Parole totali: {len(parole_tutte)} (titolo {parole_titolo}, storia {len(parole_storia)})")

    genera_ass(parole_storia, ass)
    pitch_shift_audio(mp3_raw, mp3)
    crea_sfondo(img_path, titolo, sfondo)
    crea_video(sfondo, mp3, ass, mp4, FONT_SOTT.parent)

    for f in tmp_dir.iterdir():
        f.unlink()
    tmp_dir.rmdir()

    print(f"\nFatto!")
    print(f"  audio/{mp3.name}")
    print(f"  video/{mp4.name}")


if __name__ == "__main__":
    main()
