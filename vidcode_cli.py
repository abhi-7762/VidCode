#!/usr/bin/env python3
"""
VidCode — Ultimate Real Ad Video Generator CLI
==============================================
Fast, Bulletproof & 100% Automated.
- Asks user what kind of video/ad they want
- Generates high-converting ad script & smart stock keywords
- Downloads real 1080p footage from Pixabay
- Generates Indian / Global voiceover via Edge-TTS
- Combines into professional 1080p MP4 with subtitles & branding!
"""

import sys, os, asyncio, json, textwrap, subprocess, urllib.request, urllib.parse, re
from pathlib import Path
from datetime import datetime
from typing import List, Optional

BASE_DIR    = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
VENV_PYTHON = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if VENV_PYTHON.exists() and Path(sys.executable).resolve() != VENV_PYTHON.resolve():
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON)] + sys.argv)

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.table import Table
    from rich.text import Text
    from rich.rule import Rule
    from rich.align import Align
    import questionary
    from questionary import Style as QStyle
    import edge_tts
    import imageio_ffmpeg
except ImportError as e:
    print(f"Missing: {e}\nRun: cd backend; .venv\\Scripts\\pip install rich questionary edge-tts imageio-ffmpeg")
    sys.exit(1)

console     = Console()
OUTPUT_BASE = BASE_DIR / "output_videos"
OUTPUT_BASE.mkdir(exist_ok=True)
ENV_FILE    = BACKEND_DIR / ".env"
FFMPEG      = imageio_ffmpeg.get_ffmpeg_exe()

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

PIXABAY_KEY = "58479726-f72410b64fc9ec06492990f7d"

# ══════════════════════════════════════
# BANNER
# ══════════════════════════════════════
def banner():
    console.print()
    console.print(Panel(Align.center(Text.from_markup(
        "[bold cyan]🎬  V I D C O D E   A I   S T U D I O  🎬[/]\n"
        "[bold white]Automated Real Video Ad Creator[/]\n\n"
        "[yellow]Topic batao → Pixabay Real Footage → AI Voice → Final 1080p MP4 Ready![/]"
    )), border_style="bright_cyan", padding=(1,4)))
    console.print()

def step(n, title, emoji="▶"):
    console.print()
    console.print(Rule(f"[bold bright_yellow]{emoji}  Step {n}: {title}[/]", style="bright_yellow"))
    console.print()

# ══════════════════════════════════════
# STEP 1 — INTERACTIVE QUESTIONNAIRE
# ══════════════════════════════════════
def ask_requirements() -> dict:
    step(1, "Aapka Video Vision", "🎯")
    console.print("[dim]Neeche sawalon ke jawab dein. AI turant real video banayega![/]\n")

    vtype = questionary.select("📺  Kaisa video / ad banana hai?", style=custom_style, choices=[
        "Commercial Ad / Product Advertisement",
        "Social Media Reel / Short Video",
        "E-Commerce / Food / Service Showcase",
        "Explainer / Business Presentation",
    ]).ask() or sys.exit(0)

    console.print()
    topic = questionary.text(
        "🎯  Topic / Product / Brand naam?\n   (e.g. 'Ambika Rasoi Tiffin Service', 'Fitness Gym', 'Online Coding Course'):",
        validate=lambda t: True if len(t.strip()) > 2 else "Topic enter karo.",
        style=custom_style,
    ).ask() or sys.exit(0)

    console.print()
    dur = questionary.select("⏱️   Video duration?", style=custom_style, choices=[
        "15 seconds  (Quick Ad — 2 Scenes)",
        "30 seconds  (Standard Commercial — 4 Scenes)",
        "45 seconds  (Detailed Promo — 5 Scenes)",
    ]).ask()
    dur_map = {
        "15 seconds  (Quick Ad — 2 Scenes)": 15,
        "30 seconds  (Standard Commercial — 4 Scenes)": 30,
        "45 seconds  (Detailed Promo — 5 Scenes)": 45,
    }
    duration = dur_map.get(dur, 30)

    console.print()
    lang = questionary.select("🗣️   Language?", style=custom_style, choices=[
        "🇮🇳  Hinglish (Hindi + English mix — Best for Indian Ads)",
        "🇮🇳  Hindi (Shuddh Hindi)",
        "🇬🇧  English (International)",
    ]).ask()

    voice_opts = {
        "🇮🇳  Hinglish (Hindi + English mix — Best for Indian Ads)": [
            ("Prabhat (Indian English Male - Clear & Punchy)", "en-IN-PrabhatNeural"),
            ("Neerja (Indian English Female - Engaging)",      "en-IN-NeerjaNeural"),
            ("Madhur (Hindi Male - Deep & Warm)",             "hi-IN-MadhurNeural"),
            ("Swara (Hindi Female - Expressive)",             "hi-IN-SwaraNeural"),
        ],
        "🇮🇳  Hindi (Shuddh Hindi)": [
            ("Madhur (Hindi Male)",  "hi-IN-MadhurNeural"),
            ("Swara (Hindi Female)", "hi-IN-SwaraNeural"),
        ],
        "🇬🇧  English (International)": [
            ("Christopher (Deep US Male)", "en-US-ChristopherNeural"),
            ("Jenny (Warm US Female)",     "en-US-JennyNeural"),
            ("Ryan (British UK Male)",     "en-GB-RyanNeural"),
        ],
    }
    console.print()
    opts = voice_opts.get(lang, voice_opts["🇮🇳  Hinglish (Hindi + English mix — Best for Indian Ads)"])
    vname = questionary.select("🎙️   Voiceover selection?", style=custom_style, choices=[v[0] for v in opts]).ask()
    vid   = next((v[1] for v in opts if v[0] == vname), "en-IN-PrabhatNeural")

    console.print()
    extra = questionary.text(
        "✨  Special offer, price cut ya call-to-action? (Optional — Enter daba kar skip karein):\n   (e.g. '2999 cut 2499 only, Call 9876543210'):",
        style=custom_style,
    ).ask() or ""

    return {
        "type": vtype,
        "topic": topic.strip(),
        "duration": duration,
        "language": lang,
        "voice_name": vname,
        "voice_id": vid,
        "extra": extra.strip(),
    }

# ══════════════════════════════════════
# STEP 2 — FAST AD SCRIPT ENGINE (Instant & Reliable)
# ══════════════════════════════════════
def generate_smart_script(details: dict) -> dict:
    """
    Generates tailored, high-converting ad scenes instantly.
    Extracts relevant keywords for Pixabay video searches.
    """
    topic = details["topic"]
    offer = details["extra"]
    dur = details["duration"]
    lang = details["language"]

    # Number of scenes based on duration
    n = 2 if dur <= 15 else (4 if dur <= 30 else 5)
    sec_per_scene = dur // n

    # Extract keywords based on topic category
    tl = topic.lower()
    if any(k in tl for k in ["food", "tiffin", "rasoi", "restaurant", "meal", "kitchen", "cafe", "dhaba"]):
        kw_pool = ["indian food cooking", "healthy food delivery", "delicious dinner meal", "restaurant customer eating", "chef cooking kitchen"]
    elif any(k in tl for k in ["gym", "fit", "health", "workout", "protein", "training", "diet"]):
        kw_pool = ["fitness gym workout", "man running athletic", "healthy nutrition diet", "gym training weights"]
    elif any(k in tl for k in ["code", "tech", "software", "app", "web", "ai", "computer", "developer"]):
        kw_pool = ["person coding laptop", "technology cyber digital", "developer software office", "smartphone app modern"]
    elif any(k in tl for k in ["shop", "cloth", "fashion", "sale", "store", "product"]):
        kw_pool = ["fashion shopping store", "happy customer buying", "luxury clothing style", "delivery package unboxing"]
    else:
        kw_pool = ["business presentation professional", "happy people smiling", "modern office technology", "success celebrating team"]

    scenes = []

    # Scene 1: Hook
    if "Hinglish" in lang:
        hook_text = f"Kya aapko {topic} ki sabse best quality chahiye? To ab aur wait mat karo!"
    elif "Hindi" in lang:
        hook_text = f"Kya aap {topic} ki sabse behtareen service dhoondh rahe hain? Aapka intezaar khatam!"
    else:
        hook_text = f"Looking for the best {topic}? Your search ends right here!"
    scenes.append({
        "num": 1,
        "title": "Hook",
        "narration": hook_text,
        "keyword": kw_pool[0 % len(kw_pool)],
        "seconds": sec_per_scene,
    })

    # Middle Scene(s): Value & Benefits
    if n >= 3:
        if "Hinglish" in lang:
            val_text = f"Top-notch quality, 100% trusted service, aur customer satisfaction ki poori guarantee!"
        elif "Hindi" in lang:
            val_text = f"Shuddh aur vishwasniya suvidha, bilkul uchit daam par aapki poori santushti ke saath!"
        else:
            val_text = f"Premium quality and exceptional service designed to give you the ultimate experience!"
        scenes.append({
            "num": 2,
            "title": "Value",
            "narration": val_text,
            "keyword": kw_pool[1 % len(kw_pool)],
            "seconds": sec_per_scene,
        })

    if n >= 4:
        if offer:
            mid_text = f"Special limited time offer: {offer}! Aisa mauka baar baar nahi milta!"
        else:
            mid_text = f"{topic} ke saath judiye aur enjoy kijiye ekdum seamless aur behtareen suvidha!"
        scenes.append({
            "num": 3,
            "title": "Offer / Feature",
            "narration": mid_text,
            "keyword": kw_pool[2 % len(kw_pool)],
            "seconds": sec_per_scene,
        })

    if n >= 5:
        scenes.append({
            "num": 4,
            "title": "Customer Trust",
            "narration": f"Hazaron satisfied customers ka vishwas — {topic} hai aapka apna partner!",
            "keyword": kw_pool[3 % len(kw_pool)],
            "seconds": sec_per_scene,
        })

    # Final Scene: Call to action
    cta_extra = f" {offer}" if (offer and n < 4) else ""
    if "Hinglish" in lang:
        cta_text = f"Aaj hi order karein ya call karein! {topic} — aapki seva mein hamesha tayaar!{cta_extra}"
    elif "Hindi" in lang:
        cta_text = f"Aaj hi sampark karein! {topic} — aapka vishwas, hamari pehchan!{cta_extra}"
    else:
        cta_text = f"Order now or contact us today! {topic} — quality you can trust!{cta_extra}"

    scenes.append({
        "num": n,
        "title": "Call To Action",
        "narration": cta_text,
        "keyword": kw_pool[-1],
        "seconds": sec_per_scene,
    })

    return {
        "title": topic,
        "hook": hook_text,
        "call_to_action": cta_text,
        "scenes": scenes,
    }

# ══════════════════════════════════════
# STEP 3 — PIXABAY STOCK VIDEO ENGINE
# ══════════════════════════════════════
def pixabay_search_and_download(keyword: str, out_path: Path) -> bool:
    params = urllib.parse.urlencode({
        "key": PIXABAY_KEY,
        "q": keyword,
        "video_type": "film",
        "per_page": 8,
        "safesearch": "true",
        "order": "popular",
    })
    url = f"https://pixabay.com/api/videos/?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "VidCode/1.0"})
        with urllib.request.urlopen(req, timeout=12) as r:
            data = json.loads(r.read().decode())
        for hit in data.get("hits", []):
            for q in ["medium", "small", "large", "tiny"]:
                clip_url = hit.get("videos", {}).get(q, {}).get("url")
                if clip_url:
                    r2 = urllib.request.Request(clip_url, headers={"User-Agent": "VidCode/1.0"})
                    with urllib.request.urlopen(r2, timeout=30) as resp:
                        out_path.write_bytes(resp.read())
                    return out_path.exists() and out_path.stat().st_size > 2000
    except Exception:
        pass
    return False

# ══════════════════════════════════════
# STEP 4 — EDGE-TTS VOICEOVER
# ══════════════════════════════════════
SILENT_MP3 = b"\xff\xfb\x90\x64" + b"\x00" * 1024

async def _gen_voice_async(text: str, voice_id: str, out: Path):
    try:
        await edge_tts.Communicate(text, voice_id).save(str(out))
        if not out.exists() or out.stat().st_size < 100:
            raise ValueError
    except Exception:
        out.write_bytes(SILENT_MP3)

def gen_voice(text: str, voice_id: str, out: Path):
    asyncio.run(_gen_voice_async(text, voice_id, out))

def probe_duration(path: Path) -> float:
    try:
        r = subprocess.run([FFMPEG, "-i", str(path)], stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        for line in r.stderr.splitlines():
            if "Duration:" in line:
                d = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = d.split(":")
                return max(2.5, float(h) * 3600 + float(m) * 60 + float(s) + 0.3)
    except Exception:
        pass
    return 5.0

# ══════════════════════════════════════
# STEP 5 — FFMPEG SCENE RENDERING
# ══════════════════════════════════════
def render_scene(raw_clip: Path, audio: Path, narration: str, duration: float, out: Path, brand: str) -> bool:
    safe = narration[:100].replace("'", "\\'").replace(":", "\\:").replace("\\", "\\\\")
    wrapped = textwrap.fill(safe, 46).replace("\n", "\\n")
    brand_safe = brand[:35].upper().replace("'", "\\'").replace(":", "\\:")

    sub_filter = (
        "drawbox=x=0:y=ih-200:w=iw:h=200:color=black@0.80:t=fill,"
        f"drawtext=text='{wrapped}':"
        "fontsize=46:fontcolor=white:x=(w-text_w)/2:y=h-180:"
        "line_spacing=10:shadowcolor=black:shadowx=2:shadowy=2,"
        f"drawtext=text='{brand_safe}':"
        "fontsize=28:fontcolor=0x38bdf8:x=(w-text_w)/2:y=h-30:"
        "shadowcolor=black:shadowx=1:shadowy=1"
    )

    if raw_clip.exists() and raw_clip.stat().st_size > 2000:
        cmd = [
            FFMPEG, "-y",
            "-stream_loop", "-1", "-i", str(raw_clip),
            "-i", str(audio),
            "-vf", f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1,{sub_filter}",
            "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p", "-t", str(duration),
            "-map", "0:v:0", "-map", "1:a:0", "-shortest",
            str(out),
        ]
    else:
        cmd = [
            FFMPEG, "-y",
            "-f", "lavfi", "-i", "color=c=0x0d1b2a:s=1920x1080:r=30",
            "-i", str(audio),
            "-vf", (
                f"drawtext=text='{brand_safe}':"
                "fontsize=86:fontcolor=0x38bdf8:x=(w-text_w)/2:y=h/2-80:"
                "shadowcolor=black:shadowx=4:shadowy=4,"
                + sub_filter
            ),
            "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p", "-t", str(duration),
            "-map", "0:v:0", "-map", "1:a:0", "-shortest",
            str(out),
        ]

    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=90)
    return out.exists() and out.stat().st_size > 0

def final_assemble(clips: List[Path], out: Path) -> bool:
    concat = out.parent / "concat.txt"
    with open(concat, "w", encoding="utf-8") as f:
        f.writelines(f"file '{c.resolve().as_posix()}'\n" for c in clips)
    r = subprocess.run([
        FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
        "-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(out)
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
    return out.exists() and out.stat().st_size > 0

# ══════════════════════════════════════
# MAIN EXECUTION
# ══════════════════════════════════════
def run():
    banner()

    # Step 1: Q&A
    details = ask_requirements()

    console.print()
    console.print(Panel(
        f"[bold white]📌 Topic:[/]    [cyan]{details['topic']}[/]\n"
        f"[bold white]🎬 Type:[/]     {details['type']}\n"
        f"[bold white]⏱  Duration:[/] [yellow]{details['duration']} seconds[/]\n"
        f"[bold white]🎙  Voice:[/]    {details['voice_name']}\n"
        f"[bold white]🗣  Language:[/] {details['language']}"
        + (f"\n[bold white]✨ Offer:[/]    {details['extra']}" if details['extra'] else ""),
        title="✅ Confirm Details", border_style="bright_cyan",
    ))
    console.print()

    if not questionary.confirm("🚀 Video generation shuru karein?", default=True, style=custom_style).ask():
        return

    # Project directory
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_topic = "".join(c if c.isalnum() else "_" for c in details["topic"][:20]).strip("_")
    proj = OUTPUT_BASE / f"{clean_topic}_{ts}"
    sdir = proj / "scenes"
    sdir.mkdir(parents=True, exist_ok=True)

    # Step 2: Script
    step(2, "Generating Video Blueprint & Stock Keywords", "✍️")
    script = generate_smart_script(details)

    console.print(Panel(
        f"[bold green]🎬 Ad Title:[/] {script['title']}\n"
        f"[bold yellow]⚡ Opening Hook:[/] {script['hook']}\n"
        f"[bold cyan]📢 Call To Action:[/] {script['call_to_action']}",
        title="🌟 Blueprint Summary", border_style="bright_green"
    ))

    scenes = script["scenes"]
    console.print()

    # Step 3: Stock footage + Voiceover + Render
    step(3, "Downloading 1080p Stock Footage & Recording Voiceover", "🎬")
    clips = []
    stock_count = 0

    with Progress(
        SpinnerColumn(style="bright_yellow"),
        TextColumn("[bold white]{task.description}"),
        BarColumn(bar_width=30, style="bright_blue", complete_style="bright_green"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as prog:
        task = prog.add_task("Creating ad scenes...", total=len(scenes))

        for idx, scene in enumerate(scenes):
            sid  = scene["num"]
            narr = scene["narration"]
            kw   = scene["keyword"]

            # Voice
            prog.update(task, description=f"Scene {sid}/{len(scenes)}: AI Voice recording...")
            audio = sdir / f"audio_{sid}.mp3"
            gen_voice(narr, details["voice_id"], audio)
            actual_dur = probe_duration(audio)

            # Footage
            prog.update(task, description=f"Scene {sid}/{len(scenes)}: Pixabay footage ({kw[:18]})...")
            raw = sdir / f"raw_{sid}.mp4"
            got = pixabay_search_and_download(kw, raw)
            if got:
                stock_count += 1

            # Compile
            prog.update(task, description=f"Scene {sid}/{len(scenes)}: FFmpeg scene compile...")
            clip = sdir / f"clip_{sid}.mp4"
            render_scene(raw, audio, narr, actual_dur, clip, details["topic"])
            if clip.exists():
                clips.append(clip)

            prog.advance(task)

    # Step 4: Final Master Assembly
    step(4, "Stitching Master 1080p Video", "🎞️")
    final_video = proj / f"{clean_topic}_final_ad.mp4"

    with Progress(
        SpinnerColumn(style="bright_magenta"),
        TextColumn("[bold magenta]{task.description}"),
        TimeElapsedColumn(),
        console=console,
    ) as prog:
        t = prog.add_task(f"Assembling {len(clips)} scenes into final MP4...", total=None)
        ok = final_assemble(clips, final_video)
        prog.update(t, description="[bold green]✓ Master render complete!")

    # Save metadata
    (proj / "script.json").write_text(json.dumps(script, indent=2, ensure_ascii=False), encoding="utf-8")
    (proj / "script.txt").write_text(
        "\n\n".join(
            f"SCENE {s['num']}: {s['title']}\n"
            f"[NARRATION] {s['narration']}\n"
            f"[STOCK SEARCH] {s['keyword']}"
            for s in scenes
        ),
        encoding="utf-8"
    )

    # Deliver
    console.print()
    if ok and final_video.exists():
        size_mb = final_video.stat().st_size / (1024 * 1024)
        console.print(Panel(Align.center(Text.from_markup(
            "[bold bright_green]🎉🎉  AAPKA REAL AD VIDEO PURI TARAH READY HAI!  🎉🎉[/]\n\n"
            f"[bold white]{final_video.name}[/]\n"
            f"[dim]Size: {size_mb:.1f} MB  •  {stock_count}/{len(scenes)} Real Pixabay 1080p Clips Used[/]\n\n"
            f"[cyan]{final_video}[/]"
        )), border_style="bright_green", padding=(1, 4)))

        table = Table(title="📁 Generated Files", border_style="bright_cyan")
        table.add_column("File", style="bold cyan")
        table.add_column("Details", style="white")
        table.add_row(f"🎬 {final_video.name}", "Playable 1080p Master Video with Audio & Subtitles")
        table.add_row("📝 script.txt", "Complete scene-by-scene script")
        table.add_row("📂 scenes/", "Raw downloaded clips & audio tracks")
        console.print(table)
        console.print()

        try:
            os.startfile(str(final_video))
            console.print("[green]✓ Windows Media Player mein video start ho gaya![/]")
        except Exception:
            subprocess.Popen(["cmd", "/c", "start", "", str(final_video)])

        try:
            subprocess.Popen(["explorer", str(proj)])
        except Exception:
            pass

    console.print()
    if questionary.confirm("🔄 Ek aur video banana hai?", default=False, style=custom_style).ask():
        run()
    else:
        console.print()
        console.print(Panel(Align.center(Text.from_markup(
            "[bold bright_cyan]Thank you for using VidCode AI Studio! ❤️[/]\n"
            "[dim]Aapke videos output_videos/ folder mein surakshit hain[/]"
        )), border_style="bright_cyan", padding=(1, 4)))

if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Exited. 👋[/]")
