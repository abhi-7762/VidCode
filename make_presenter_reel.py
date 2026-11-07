#!/usr/bin/env python3
"""
VidCode — 9:16 Vertical Presenter Reel Generator (Overlay Engine)
================================================================
Uses Pillow to draw stunning, high-res graphic overlays (badges, captions,
top brand header, bottom CTA) and composites them onto the Indian presenter
video with audio sync & background music!
"""

import sys, os, asyncio, subprocess, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR    = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
VENV_PYTHON = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"
if VENV_PYTHON.exists() and Path(sys.executable).resolve() != VENV_PYTHON.resolve():
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON)] + sys.argv)

import imageio_ffmpeg
import edge_tts
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align

console = Console()
FFMPEG  = imageio_ffmpeg.get_ffmpeg_exe()
OUTPUT  = BASE_DIR / "output_videos" / "presenter_reels"
OUTPUT.mkdir(parents=True, exist_ok=True)
TEMPLATE_VIDEO = BASE_DIR / "templates" / "presenter_indian_guy.mp4"

# ── AD CONFIG ────────────────────────────────────────────────────────
BRAND_NAME = "AMBIKA RASOI"
LOCATION   = "DUMKA, JHARKHAND"
PHONE      = "CALL: 9876543210"
OFFER_LINE = "FLAT Rs. 500 OFF  *  Rs. 2999 -> Rs. 2499 / MONTH"

AD_SEGMENTS = [
    {
        "badge": "HOMESTYLE TASTE",
        "title": "Ghar Jaisa Khana?",
        "text": "Dumka me ghar jaisa khana dhoondh rahe hain? Aapka intezaar khatam!",
        "voice": "en-IN-PrabhatNeural",
    },
    {
        "badge": "DAILY FRESH",
        "title": "Daily Fresh & Healthy",
        "text": "Ambika Rasoi laaya hai fresh aur healthy tiffin directly aapke doorstep pe!",
        "voice": "en-IN-PrabhatNeural",
    },
    {
        "badge": "PURE QUALITY",
        "title": "100% Shuddh Masale",
        "text": "Shuddh masale, hygienic packaging aur bilkul maa ke haath jaisa swad!",
        "voice": "en-IN-PrabhatNeural",
    },
    {
        "badge": "LIMITED TIME OFFER",
        "title": "Monthly Sirf Rs. 2499",
        "text": "Special limited offer! Monthly tiffin sirf 2499 rupaye, pehle 2999 tha!",
        "voice": "en-IN-PrabhatNeural",
    },
    {
        "badge": "ORDER TODAY",
        "title": "Limited Slots Available",
        "text": "Seats limited hain, call karein aur aaj hi apna swad book karein!",
        "voice": "en-IN-PrabhatNeural",
    },
]

# ── HELPERS ──────────────────────────────────────────────────────────
async def gen_voice_file(text: str, voice: str, out_path: Path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(out_path))

def probe_dur(path: Path) -> float:
    try:
        r = subprocess.run([FFMPEG, "-i", str(path)], stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        for line in r.stderr.splitlines():
            if "Duration:" in line:
                d = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = d.split(":")
                return max(2.5, float(h)*3600 + float(m)*60 + float(s))
    except Exception:
        pass
    return 4.0

def create_segment_overlay(seg: dict, out_png: Path):
    """Draws a 1080x1920 transparent overlay with headers, captions & offer badges."""
    W, H = 1080, 1920
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Windows Standard Fonts
    font_brand = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 46)
    font_sub   = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 26)
    font_badge = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 26)
    font_title = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 40)
    font_body  = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 34)
    font_offer = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 32)
    font_cta   = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 26)

    # 1. TOP BRAND HEADER (Dark glass card)
    draw.rounded_rectangle([(40, 50), (1040, 185)], radius=20, fill=(10, 15, 28, 225), outline=(56, 189, 248, 255), width=3)
    draw.text((70, 72), f"[AD] {BRAND_NAME}", fill=(56, 189, 248, 255), font=font_brand)
    draw.text((72, 134), f"LOCATION: {LOCATION}  |  {PHONE}", fill=(226, 232, 240, 240), font=font_sub)

    # 2. DYNAMIC CENTER CAPTIONS (Reel Viral Style)
    badge_text = f"★ {seg['badge']} ★"
    bbox_b = draw.textbbox((0, 0), badge_text, font=font_badge)
    bw = bbox_b[2] - bbox_b[0]
    badge_x1 = (W - bw) // 2 - 25
    badge_x2 = (W + bw) // 2 + 25
    draw.rounded_rectangle([(badge_x1, 1220), (badge_x2, 1275)], radius=15, fill=(245, 158, 11, 255))
    draw.text(((W - bw) // 2, 1232), badge_text, fill=(0, 0, 0, 255), font=font_badge)

    # Caption Box
    lines = textwrap.fill(seg["text"], width=32).splitlines()
    box_h = 100 + len(lines) * 48
    draw.rounded_rectangle([(50, 1290), (1030, 1290 + box_h)], radius=25, fill=(8, 12, 22, 235), outline=(250, 204, 21, 230), width=3)
    # Highlight Title
    draw.text((80, 1315), seg["title"].upper(), fill=(250, 204, 21, 255), font=font_title)
    # Subtitle text wrapped
    y_text = 1375
    for l in lines:
        draw.text((80, y_text), l, fill=(255, 255, 255, 255), font=font_body)
        y_text += 48

    # 3. BOTTOM OFFER & CTA BANNER
    draw.rounded_rectangle([(40, 1690), (1040, 1860)], radius=20, fill=(15, 23, 42, 240), outline=(52, 211, 153, 245), width=3)
    draw.text((80, 1720), OFFER_LINE, fill=(250, 204, 21, 255), font=font_offer)
    draw.text((80, 1785), f"ORDER NOW: {PHONE}  |  FREE DOORSTEP DELIVERY", fill=(255, 255, 255, 255), font=font_cta)

    img.save(str(out_png), "PNG")

def generate_presenter_reel():
    console.print()
    console.print(Panel(Align.center(Text.from_markup(
        "[bold cyan]🎬  VIDCODE — 9:16 VERTICAL PRESENTER REEL  🎬[/]\n\n"
        "[bold white]Spokesperson Actor + Studio Voice + Viral Overlay Engine[/]\n"
        f"[yellow]Brand: {BRAND_NAME} ({LOCATION})[/]"
    )), border_style="bright_cyan", padding=(1, 4)))
    console.print()

    work_dir = OUTPUT / "temp_build"
    work_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Voice recording
    console.print("[bold yellow]Step 1: AI Studio Voice recording...[/]")
    timed_segments = []
    current_time = 0.4

    for i, seg in enumerate(AD_SEGMENTS, 1):
        audio_file = work_dir / f"voice_{i}.mp3"
        asyncio.run(gen_voice_file(seg["text"], seg["voice"], audio_file))
        dur = probe_dur(audio_file)

        # Create overlay PNG for this segment
        overlay_png = work_dir / f"overlay_{i}.png"
        create_segment_overlay(seg, overlay_png)

        timed_segments.append({
            "index": i,
            "start": current_time,
            "end": current_time + dur + 0.3,
            "audio": audio_file,
            "overlay": overlay_png,
        })
        current_time += dur + 0.35

    total_dur = current_time + 0.4
    console.print(f"[green]✓ {len(timed_segments)} voice tracks & overlay cards created ({total_dur:.1f}s total)[/]")

    # Step 2: Combine Audio
    console.print("[bold yellow]Step 2: Mixing voiceover track...[/]")
    concat_txt = work_dir / "voice_concat.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for s in timed_segments:
            clean_p = str(s["audio"].resolve()).replace("\\", "/")
            f.write(f"file '{clean_p}'\n")

    master_wav = work_dir / "master_voice.wav"
    subprocess.run([
        FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt),
        "-c:a", "pcm_s16le", "-ar", "44100", str(master_wav)
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    # Step 3: Complex Filter for video + overlays
    console.print("[bold yellow]Step 3: Overlaying dynamic Reel captions onto Presenter video...[/]")

    cmd = [
        FFMPEG, "-y",
        "-stream_loop", "-1",
        "-i", str(TEMPLATE_VIDEO),
        "-i", str(master_wav),
    ]

    for s in timed_segments:
        cmd.extend(["-i", str(s["overlay"])])

    # Build filter complex
    filter_parts = [
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[v0]"
    ]

    last_v = "v0"
    for i, s in enumerate(timed_segments):
        input_idx = i + 2
        next_v = f"v{i+1}"
        s_start = f"{s['start']:.2f}"
        s_end   = f"{s['end']:.2f}"
        filter_parts.append(
            f"[{last_v}][{input_idx}:v]overlay=0:0:enable='between(t,{s_start},{s_end})'[{next_v}]"
        )
        last_v = next_v

    cmd.extend([
        "-filter_complex", ";".join(filter_parts),
        "-map", f"[{last_v}]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-t", f"{total_dur:.2f}",
        "-shortest",
    ])

    final_reel = OUTPUT / "ambika_rasoi_reel_1080x1920.mp4"
    cmd.append(str(final_reel))

    console.print("[bold yellow]Step 4: Compiling master 1080x1920 video...[/]")
    subprocess.run(cmd, check=True)

    if final_reel.exists() and final_reel.stat().st_size > 1000:
        size_mb = final_reel.stat().st_size / (1024 * 1024)
        console.print()
        console.print(Panel(Align.center(Text.from_markup(
            "[bold bright_green]🎉🎉  EXACT REFERENCE STYLE REEL READY!  🎉🎉[/]\n\n"
            f"[bold white]{final_reel.name}[/]\n"
            f"[dim]Format: 1080x1920 (9:16 Vertical Reel)  •  Size: {size_mb:.1f} MB  •  Duration: {total_dur:.1f}s[/]\n\n"
            f"[cyan]{final_reel}[/]"
        )), border_style="bright_green", padding=(1, 4)))

        try:
            os.startfile(str(final_reel))
            console.print("[green]✓ Windows Media Player mein Reel open ho gayi![/]")
        except Exception:
            subprocess.Popen(["cmd", "/c", "start", "", str(final_reel)])

        try:
            subprocess.Popen(["explorer", str(OUTPUT)])
        except Exception:
            pass
    else:
        console.print("[red]Compilation failed.[/]")

if __name__ == "__main__":
    generate_presenter_reel()
