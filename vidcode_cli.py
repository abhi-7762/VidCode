#!/usr/bin/env python3
"""
VidCode — 9:16 Viral Presenter Reel CLI
========================================
Interactive terminal wizard that generates 1080x1920 Instagram/YouTube Reels:
- Continuous Indian creator/spokesperson talking directly to camera
- Studio AI voiceover in natural Hinglish/Hindi/English
- High-res kinetic subtitle cards
- Top brand header & bottom offer CTA
"""

import sys, os, asyncio, subprocess, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR    = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
VENV_PYTHON = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if VENV_PYTHON.exists() and Path(sys.executable).resolve() != VENV_PYTHON.resolve():
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON)] + sys.argv)

import imageio_ffmpeg
import edge_tts
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from rich.align import Align
import questionary
from questionary import Style as QStyle

console = Console()
FFMPEG  = imageio_ffmpeg.get_ffmpeg_exe()
OUTPUT_BASE = BASE_DIR / "output_videos" / "presenter_reels"
OUTPUT_BASE.mkdir(parents=True, exist_ok=True)
TEMPLATE_VIDEO = BASE_DIR / "templates" / "presenter_indian_guy.mp4"

custom_style = QStyle([
    ("qmark",       "fg:#00d7ff bold"),
    ("question",    "bold fg:#ffffff"),
    ("answer",      "fg:#00ff87 bold"),
    ("pointer",     "fg:#ff5fd7 bold"),
    ("highlighted", "fg:#ff5fd7 bold"),
    ("selected",    "fg:#00ff87"),
    ("instruction", "fg:#858585 italic"),
    ("text",        "fg:#ffffff"),
])

# ── BANNER ────────────────────────────────────────────────────────────
def show_banner():
    console.print()
    console.print(Panel(Align.center(Text.from_markup(
        "[bold cyan]🎬  V I D C O D E   A I   S T U D I O  🎬[/]\n"
        "[bold white]9:16 Viral Presenter Reel Generator (Instagram / YouTube Shorts)[/]\n\n"
        "[yellow]Real Indian Spokesperson + Studio Voice + Animated Captions = High-Converting Reel![/]"
    )), border_style="bright_cyan", padding=(1, 4)))
    console.print()

def step(n, title, emoji="▶"):
    console.print()
    console.print(Rule(f"[bold bright_yellow]{emoji}  Step {n}: {title}[/]", style="bright_yellow"))
    console.print()

# ── Q&A ───────────────────────────────────────────────────────────────
def ask_user():
    step(1, "Apne Brand / Ad Ki Details Dein", "🎯")
    console.print("[dim]Neeche diye gaye sawalon ke jawab dein. Turant 9:16 Reel tayyar hogi![/]\n")

    brand = questionary.text(
        "🏢 1. Brand / Business ka naam?\n   (e.g. 'Ambika Rasoi', 'Apex Fitness Gym', 'CodeSprint Academy'):",
        validate=lambda t: True if len(t.strip()) > 1 else "Brand naam zaroori hai.",
        style=custom_style,
    ).ask() or sys.exit(0)

    console.print()
    service = questionary.text(
        "🎯 2. Aap kya bech rahe hain / kya service hai?\n   (e.g. 'Daily Tiffin & Mess Service', 'Gym Membership', 'Online Python Course'):",
        validate=lambda t: True if len(t.strip()) > 2 else "Service enter karein.",
        style=custom_style,
    ).ask() or sys.exit(0)

    console.print()
    location = questionary.text(
        "📍 3. City / Location?\n   (e.g. 'Dumka, Jharkhand', 'Noida Sector 62', 'Pan India Online'):",
        style=custom_style,
    ).ask() or "India"

    console.print()
    offer = questionary.text(
        "⚡ 4. Special Offer / Discount / Price?\n   (e.g. 'Monthly Rs. 2499 (Save Rs. 500)', 'Free Trial Today', 'Flat 40% Off'):",
        style=custom_style,
    ).ask() or "Special Limited Offer"

    console.print()
    phone = questionary.text(
        "📞 5. Contact Number ya Website jo video par dikhani hai?\n   (e.g. '9876543210' ya 'www.mywebsite.com'):",
        style=custom_style,
    ).ask() or "CALL TODAY"

    console.print()
    voice_choice = questionary.select(
        "🎙️ 6. Presenter Voiceover selection?",
        choices=[
            "Prabhat (Indian English Male - Clear & Punchy)",
            "Neerja (Indian English Female - Professional)",
            "Madhur (Hindi Male - Deep & Warm)",
            "Swara (Hindi Female - Expressive)",
        ],
        style=custom_style,
    ).ask()

    voice_map = {
        "Prabhat (Indian English Male - Clear & Punchy)": "en-IN-PrabhatNeural",
        "Neerja (Indian English Female - Professional)":  "en-IN-NeerjaNeural",
        "Madhur (Hindi Male - Deep & Warm)":             "hi-IN-MadhurNeural",
        "Swara (Hindi Female - Expressive)":             "hi-IN-SwaraNeural",
    }
    voice_id = voice_map.get(voice_choice, "en-IN-PrabhatNeural")

    return {
        "brand": brand.strip(),
        "service": service.strip(),
        "location": location.strip(),
        "offer": offer.strip(),
        "phone": phone.strip(),
        "voice_name": voice_choice,
        "voice_id": voice_id,
    }

# ── SMART SCRIPT BUILDER ──────────────────────────────────────────────
def build_ad_script(d: dict) -> list:
    brand = d["brand"]
    serv  = d["service"]
    loc   = d["location"]
    offer = d["offer"]

    return [
        {
            "badge": "HOMESTYLE QUALITY",
            "title": f"Best {serv}?",
            "text": f"{loc} me sabse behtareen {serv} dhoondh rahe hain? Aapka intezaar khatam!",
        },
        {
            "badge": "100% TRUSTED",
            "title": f"{brand} Service",
            "text": f"{brand} laaya hai aapke liye top quality, fresh aur trusted {serv}!",
        },
        {
            "badge": "PURE & HYGIENIC",
            "title": "Customer Satisfaction",
            "text": f"Hygienic service, timely delivery aur poori santushti ki guarantee!",
        },
        {
            "badge": "SPECIAL OFFER",
            "title": f"{offer}",
            "text": f"Limited time deal: {offer}! Aisa shandar mauka baar baar nahi milta!",
        },
        {
            "badge": "ORDER TODAY",
            "title": "Book Your Slot Now",
            "text": f"Slots limited hain! Aaj hi call karein aur {brand} se judiye!",
        },
    ]

# ── HELPERS ───────────────────────────────────────────────────────────
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

def create_segment_overlay(seg: dict, d: dict, out_png: Path):
    """Draws a 1080x1920 transparent overlay with headers, captions & offer badges."""
    W, H = 1080, 1920
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_brand = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 46)
    font_sub   = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 26)
    font_badge = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 26)
    font_title = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 40)
    font_body  = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 34)
    font_offer = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 32)
    font_cta   = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 26)

    # 1. TOP BRAND HEADER
    brand_line = f"[AD] {d['brand'].upper()}"
    info_line  = f"📍 {d['location'].upper()}  |  📞 {d['phone']}"
    draw.rounded_rectangle([(40, 50), (1040, 185)], radius=20, fill=(10, 15, 28, 225), outline=(56, 189, 248, 255), width=3)
    draw.text((70, 72), brand_line, fill=(56, 189, 248, 255), font=font_brand)
    draw.text((72, 134), info_line, fill=(226, 232, 240, 240), font=font_sub)

    # 2. DYNAMIC CENTER CAPTIONS
    badge_text = f"★ {seg['badge']} ★"
    bbox_b = draw.textbbox((0, 0), badge_text, font=font_badge)
    bw = bbox_b[2] - bbox_b[0]
    badge_x1 = (W - bw) // 2 - 25
    badge_x2 = (W + bw) // 2 + 25
    draw.rounded_rectangle([(badge_x1, 1220), (badge_x2, 1275)], radius=15, fill=(245, 158, 11, 255))
    draw.text(((W - bw) // 2, 1232), badge_text, fill=(0, 0, 0, 255), font=font_badge)

    lines = textwrap.fill(seg["text"], width=32).splitlines()
    box_h = 100 + len(lines) * 48
    draw.rounded_rectangle([(50, 1290), (1030, 1290 + box_h)], radius=25, fill=(8, 12, 22, 235), outline=(250, 204, 21, 230), width=3)
    draw.text((80, 1315), seg["title"].upper(), fill=(250, 204, 21, 255), font=font_title)
    y_text = 1375
    for l in lines:
        draw.text((80, y_text), l, fill=(255, 255, 255, 255), font=font_body)
        y_text += 48

    # 3. BOTTOM OFFER & CTA BANNER
    draw.rounded_rectangle([(40, 1690), (1040, 1860)], radius=20, fill=(15, 23, 42, 240), outline=(52, 211, 153, 245), width=3)
    draw.text((80, 1720), f"🔥 {d['offer'].upper()}", fill=(250, 204, 21, 255), font=font_offer)
    draw.text((80, 1785), f"CALL NOW: {d['phone']}  |  DOORSTEP SERVICE", fill=(255, 255, 255, 255), font=font_cta)

    img.save(str(out_png), "PNG")

# ── MAIN PIPELINE ─────────────────────────────────────────────────────
def run_cli():
    show_banner()

    if not TEMPLATE_VIDEO.exists():
        console.print(f"[red]Error: Template video missing at {TEMPLATE_VIDEO}[/]")
        return

    # Step 1
    d = ask_user()

    console.print()
    console.print(Panel(
        f"[bold white]🏢 Brand:[/]    [cyan]{d['brand']}[/]\n"
        f"[bold white]🎯 Service:[/]  {d['service']}\n"
        f"[bold white]📍 Location:[/] {d['location']}\n"
        f"[bold white]⚡ Offer:[/]    [yellow]{d['offer']}[/]\n"
        f"[bold white]📞 Contact:[/]  {d['phone']}\n"
        f"[bold white]🎙 Voice:[/]    {d['voice_name']}",
        title="✅ Confirm Reel Details", border_style="bright_cyan"
    ))
    console.print()

    if not questionary.confirm("🚀 9:16 Presenter Reel generation shuru karein?", default=True, style=custom_style).ask():
        return

    # Work dir
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_brand = "".join(c if c.isalnum() else "_" for c in d["brand"][:20]).strip("_")
    proj = OUTPUT_BASE / f"{clean_brand}_{ts}"
    work_dir = proj / "build"
    work_dir.mkdir(parents=True, exist_ok=True)

    segments = build_ad_script(d)

    # Step 2: Voiceover & Overlays
    step(2, "AI Voice Recording & Typography Overlays", "🎙️")
    timed_segments = []
    current_time = 0.4

    with Progress(
        SpinnerColumn(style="bright_yellow"),
        TextColumn("[bold white]{task.description}"),
        BarColumn(bar_width=30, style="bright_blue", complete_style="bright_green"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as prog:
        task = prog.add_task("Creating Reel voice & graphic cards...", total=len(segments))

        for i, seg in enumerate(segments, 1):
            audio_file = work_dir / f"voice_{i}.mp3"
            asyncio.run(gen_voice_file(seg["text"], d["voice_id"], audio_file))
            dur = probe_dur(audio_file)

            overlay_png = work_dir / f"overlay_{i}.png"
            create_segment_overlay(seg, d, overlay_png)

            timed_segments.append({
                "index": i,
                "start": current_time,
                "end": current_time + dur + 0.3,
                "audio": audio_file,
                "overlay": overlay_png,
            })
            current_time += dur + 0.35
            prog.advance(task)

    total_dur = current_time + 0.4

    # Step 3: Combine Audio
    step(3, "Master Audio Mix", "🎧")
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
    console.print(f"[green]✓ Master audio track ready ({total_dur:.1f}s)[/]")

    # Step 4: Video Overlay & Assembly
    step(4, "Compositing 1080x1920 Vertical Presenter Reel", "🎬")

    cmd = [
        FFMPEG, "-y",
        "-stream_loop", "-1",
        "-i", str(TEMPLATE_VIDEO),
        "-i", str(master_wav),
    ]

    for s in timed_segments:
        cmd.extend(["-i", str(s["overlay"])])

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

    final_reel = proj / f"{clean_brand}_vertical_reel.mp4"

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
        str(final_reel),
    ])

    with Progress(
        SpinnerColumn(style="bright_magenta"),
        TextColumn("[bold magenta]{task.description}"),
        TimeElapsedColumn(),
        console=console,
    ) as prog:
        t = prog.add_task("Rendering 1080x1920 Reel video (~20 sec)...", total=None)
        subprocess.run(cmd, check=True)
        prog.update(t, description="[bold green]✓ 1080x1920 Reel ready!")

    # Delivery
    if final_reel.exists() and final_reel.stat().st_size > 1000:
        size_mb = final_reel.stat().st_size / (1024 * 1024)
        console.print()
        console.print(Panel(Align.center(Text.from_markup(
            "[bold bright_green]🎉🎉  EXACT REFERENCE STYLE REEL TAYYAR HAI!  🎉🎉[/]\n\n"
            f"[bold white]{final_reel.name}[/]\n"
            f"[dim]Format: 1080x1920 (9:16 Vertical Reel)  •  Size: {size_mb:.1f} MB  •  Duration: {total_dur:.1f}s[/]\n\n"
            f"[cyan]{final_reel}[/]"
        )), border_style="bright_green", padding=(1, 4)))

        # Launch
        try:
            os.startfile(str(final_reel))
            console.print("[green]✓ Windows Media Player mein Reel open ho gayi![/]")
        except Exception:
            subprocess.Popen(["cmd", "/c", "start", "", str(final_reel)])

        try:
            subprocess.Popen(["explorer", str(proj)])
        except Exception:
            pass

    console.print()
    if questionary.confirm("🔄 Ek aur brand ke liye Reel banana hai?", default=False, style=custom_style).ask():
        run_cli()
    else:
        console.print()
        console.print(Panel(Align.center(Text.from_markup(
            "[bold bright_cyan]Thank you for using VidCode AI Studio! ❤️[/]\n"
            "[dim]Aapke videos output_videos/presenter_reels/ folder mein surakshit hain[/]"
        )), border_style="bright_cyan", padding=(1, 4)))

if __name__ == "__main__":
    try:
        run_cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped. 👋[/]")
