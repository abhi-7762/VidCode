#!/usr/bin/env python3
"""
VidCode — Real AI Video Generator CLI Wizard
=============================================
Pexels/Pixabay se real stock footage + Edge-TTS voiceover + FFmpeg subtitles
= Professional real video ad, bilkul free!

Flow:
  1. Interactive Q&A (questions poochhe)
  2. Gemini AI → perfect script + scene keywords
  3. Pixabay API → real stock video clips download
  4. Edge-TTS → AI voiceover
  5. FFmpeg → clips + audio + subtitles = final 1080p MP4
"""

import sys
import os
import asyncio
import json
import textwrap
import subprocess
import time
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# ── Path & venv auto-switch ────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
VENV_PYTHON = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if VENV_PYTHON.exists() and Path(sys.executable).resolve() != VENV_PYTHON.resolve():
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON)] + sys.argv)

# ── Library imports ────────────────────────────────────────────────────
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, DownloadColumn
    from rich.table import Table
    from rich.text import Text
    from rich.rule import Rule
    from rich.align import Align
    import questionary
    from questionary import Style as QStyle
    import httpx
    import edge_tts
except ImportError as e:
    print(f"[ERROR] Missing library: {e}")
    print("Run:  cd backend; .venv\\Scripts\\pip install rich questionary httpx edge-tts")
    sys.exit(1)

# ── App imports ────────────────────────────────────────────────────────
from app.services.gemini_service import GeminiService
from app.models.script import ScriptGenerateRequest, ScriptTone, ScriptStyle

# ── Config ─────────────────────────────────────────────────────────────
console     = Console()
OUTPUT_BASE = BASE_DIR / "output_videos"
OUTPUT_BASE.mkdir(exist_ok=True)
ENV_FILE    = BACKEND_DIR / ".env"

custom_style = QStyle([
    ("qmark",       "fg:#00d7ff bold"),
    ("question",    "bold fg:#ffffff"),
    ("answer",      "fg:#00ff87 bold"),
    ("pointer",     "fg:#ff5fd7 bold"),
    ("highlighted", "fg:#ff5fd7 bold"),
    ("selected",    "fg:#00ff87"),
    ("instruction", "fg:#858585 italic"),
    ("text",        "fg:#ffffff"),
    ("disabled",    "fg:#858585 italic"),
])

PIXABAY_BASE = "https://pixabay.com/api/videos/"


# ══════════════════════════════════════════════════════════════════════
# API KEY MANAGEMENT
# ══════════════════════════════════════════════════════════════════════

def load_pixabay_key() -> Optional[str]:
    """Read Pixabay API key from .env file."""
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if line.startswith("PIXABAY_API_KEY="):
                val = line.split("=", 1)[1].strip()
                if val and val != "your_pixabay_key_here":
                    return val
    return None


def save_pixabay_key(key: str):
    """Append or update Pixabay API key in .env file."""
    content = ENV_FILE.read_text(encoding="utf-8") if ENV_FILE.exists() else ""
    if "PIXABAY_API_KEY=" in content:
        lines = []
        for line in content.splitlines():
            if line.startswith("PIXABAY_API_KEY="):
                lines.append(f"PIXABAY_API_KEY={key}")
            else:
                lines.append(line)
        ENV_FILE.write_text("\n".join(lines), encoding="utf-8")
    else:
        with open(ENV_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n# Pixabay Stock Video API\nPIXABAY_API_KEY={key}\n")
    console.print(f"[green]✓ API key saved to .env[/]")


def ask_for_pixabay_key() -> str:
    """Interactively ask user for Pixabay API key."""
    console.print()
    console.print(Panel(
        "[bold white]Real video banane ke liye Pixabay API key chahiye![/]\n\n"
        "[cyan]1.[/] [link=https://pixabay.com/accounts/register/]pixabay.com/accounts/register[/] pe FREE account banao\n"
        "[cyan]2.[/] Login ke baad [link=https://pixabay.com/api/docs/]pixabay.com/api/docs[/] pe jao\n"
        "[cyan]3.[/] Wahan apni API key dikhegi — copy karo aur yahan paste karo\n\n"
        "[dim]API key free hai, koi credit card nahi chahiye![/]",
        title="🔑 Pixabay API Key Required",
        border_style="bright_yellow",
    ))
    console.print()

    key = questionary.text(
        "🔑 Apni Pixabay API key paste karo:",
        validate=lambda k: True if len(k.strip()) > 10 else "Valid API key paste karein.",
        style=custom_style,
    ).ask()

    if not key:
        sys.exit(0)

    key = key.strip()
    save_pixabay_key(key)
    return key


# ══════════════════════════════════════════════════════════════════════
# UI HELPERS
# ══════════════════════════════════════════════════════════════════════

def show_banner():
    console.print()
    console.print(Panel(
        Align.center(Text.from_markup(
            "[bold cyan]🎬  V I D C O D E   A I   S T U D I O  🎬[/]\n"
            "[bold white]Real Video Generator — Stock Footage + AI Voice[/]\n\n"
            "[yellow]Idea batao → Gemini Script → Real Footage → Voiceover → Professional MP4![/]"
        )),
        border_style="bright_cyan",
        padding=(1, 4),
    ))
    console.print()

def step_header(num: int, title: str, emoji: str = "▶"):
    console.print()
    console.print(Rule(f"[bold bright_yellow]{emoji}  Step {num}: {title}[/]", style="bright_yellow"))
    console.print()


# ══════════════════════════════════════════════════════════════════════
# STEP 1 — INTERACTIVE Q&A (Synchronous)
# ══════════════════════════════════════════════════════════════════════

def ask_user_requirements() -> dict:
    step_header(1, "Aapka Video Vision", "🎯")
    console.print("[dim]Neeche diye gaye sawalon ke jawab dein. AI aapke liye perfect video tayyar karega![/]\n")

    video_type = questionary.select(
        "📺  Aapko kaisa ad ya video banana hai?",
        choices=[
            "📢  Commercial Ad / Product Advertisement",
            "📱  Viral Social Media Reel / Short",
            "🎓  Explainer / Tutorial Video",
            "🏢  Corporate Brand Story",
            "🛍️  E-Commerce / Product Showcase",
            "🚀  Startup Pitch / Teaser Video",
            "🎥  YouTube Content",
        ],
        style=custom_style,
    ).ask()
    if not video_type:
        sys.exit(0)

    console.print()
    topic = questionary.text(
        "🎯  Topic, product ya brand ka naam?\n   (e.g. 'Ambika Rasoi Tiffin Service', 'Gym Supplement', 'App Launch'):",
        validate=lambda t: True if len(t.strip()) > 2 else "Kripya topic enter karein.",
        style=custom_style,
    ).ask()
    if not topic:
        sys.exit(0)

    console.print()
    audience = questionary.select(
        "👥  Target Audience kaun hai?",
        choices=[
            "🧑‍💻  Techies & Gadget Lovers",
            "🧑‍🎓  Students (18-24)",
            "💼  Professionals & Business Owners",
            "💪  Fitness & Health Enthusiasts",
            "🛍️  Online Shoppers",
            "👨‍👩‍👧  Families & Parents",
            "🌍  General Public",
        ],
        style=custom_style,
    ).ask()

    console.print()
    duration_choice = questionary.select(
        "⏱️   Video kitne seconds ka?",
        choices=[
            "15 seconds  (Fast Reel/Ad)",
            "30 seconds  (Standard Ad)",
            "45 seconds  (Detailed Ad)",
            "60 seconds  (Full Story Video)",
        ],
        style=custom_style,
    ).ask()
    dur_map = {"15 seconds  (Fast Reel/Ad)": 15, "30 seconds  (Standard Ad)": 30,
               "45 seconds  (Detailed Ad)": 45, "60 seconds  (Full Story Video)": 60}
    duration_seconds = dur_map.get(duration_choice, 30)

    console.print()
    tone_choice = questionary.select(
        "🎭  Video ka tone?",
        choices=[
            "🔥  Energetic & Bold",
            "💼  Professional & Premium",
            "😂  Funny & Relatable",
            "🌟  Inspiring & Emotional",
            "🔬  Informative & Educational",
        ],
        style=custom_style,
    ).ask()

    console.print()
    language_choice = questionary.select(
        "🗣️   Language?",
        choices=[
            "🇮🇳  Hinglish (Hindi + English mix — Best for Indian Ads)",
            "🇮🇳  Hindi",
            "🇬🇧  English",
        ],
        style=custom_style,
    ).ask()

    voice_map = {
        "🇮🇳  Hinglish (Hindi + English mix — Best for Indian Ads)": [
            ("Prabhat (Indian English Male)",  "en-IN-PrabhatNeural"),
            ("Neerja (Indian English Female)", "en-IN-NeerjaNeural"),
            ("Madhur (Hindi Male)",            "hi-IN-MadhurNeural"),
            ("Swara (Hindi Female)",           "hi-IN-SwaraNeural"),
        ],
        "🇮🇳  Hindi": [
            ("Madhur (Deep Hindi Male)",  "hi-IN-MadhurNeural"),
            ("Swara (Warm Hindi Female)", "hi-IN-SwaraNeural"),
        ],
        "🇬🇧  English": [
            ("Christopher (Cinematic US Male)", "en-US-ChristopherNeural"),
            ("Jenny (Engaging US Female)",      "en-US-JennyNeural"),
            ("Ryan (Sophisticated UK Male)",    "en-GB-RyanNeural"),
        ],
    }

    console.print()
    voice_options = voice_map.get(language_choice, voice_map["🇬🇧  English"])
    voice_selection = questionary.select(
        "🎙️   Voiceover voice?",
        choices=[v[0] for v in voice_options],
        style=custom_style,
    ).ask()
    voice_id = next((v[1] for v in voice_options if v[0] == voice_selection), "en-US-ChristopherNeural")

    console.print()
    extra = questionary.text(
        "✨  Special offer / USP / phone number jo video me aaye? (Optional):",
        style=custom_style,
    ).ask() or ""

    return {
        "video_type":       video_type.strip(),
        "topic":            topic.strip(),
        "audience":         audience.strip(),
        "duration_seconds": duration_seconds,
        "duration_label":   duration_choice,
        "tone":             tone_choice.strip(),
        "language":         language_choice.strip(),
        "voice_name":       voice_selection,
        "voice_id":         voice_id,
        "extra":            extra.strip(),
    }


# ══════════════════════════════════════════════════════════════════════
# STEP 2 — GEMINI: SCRIPT + SCENE KEYWORDS
# ══════════════════════════════════════════════════════════════════════

async def _generate_script(details: dict) -> dict:
    gemini = GeminiService()
    extra_line = f"\nSpecial info: {details['extra']}" if details["extra"] else ""
    n_scenes = max(2, details["duration_seconds"] // 15)

    prompt = (
        f"Create a {details['duration_seconds']}-second high-converting {details['video_type']} "
        f"about '{details['topic']}'.\n"
        f"Target Audience: {details['audience']}\n"
        f"Tone: {details['tone']}\n"
        f"Script Language: {details['language']} — write narration STRICTLY in this language.\n"
        f"Number of scenes: exactly {n_scenes}\n"
        f"{extra_line}\n\n"
        "Rules:\n"
        "- Scene 1: Irresistible hook that stops scrolling.\n"
        "- Middle scenes: Problem → Solution → Benefits.\n"
        "- Final scene: Clear Call-To-Action.\n"
        "- Write complete exact spoken narration for every scene.\n"
        "- Add a 'video_search_keyword' field for each scene: 1-3 English words "
        "  to search stock video (e.g. 'food delivery', 'happy family', 'gym workout')."
    )

    req = ScriptGenerateRequest(
        project_id="cli_wizard",
        prompt=prompt,
        duration_seconds=details["duration_seconds"],
        tone=ScriptTone.INSPIRATIONAL,
        style=ScriptStyle.STORYTELLING,
        target_audience=details["audience"],
    )

    nlu         = await gemini.analyse_prompt(prompt, details["duration_seconds"])
    script_data = await gemini.generate_script(req, nlu)

    # Inject video_search_keywords if Gemini didn't add them
    for i, scene in enumerate(script_data.get("scenes", [])):
        if not scene.get("video_search_keyword"):
            topic_words = details["topic"].split()[:2]
            fallback_keywords = [
                " ".join(topic_words),
                "food delivery",
                "happy customer",
                "product showcase",
                "call to action",
            ]
            scene["video_search_keyword"] = fallback_keywords[i % len(fallback_keywords)]

    return script_data


def generate_script(details: dict) -> dict:
    return asyncio.run(_generate_script(details))


# ══════════════════════════════════════════════════════════════════════
# STEP 3 — PIXABAY: REAL STOCK VIDEO DOWNLOAD
# ══════════════════════════════════════════════════════════════════════

def search_pixabay_video(keyword: str, api_key: str, duration_hint: float = 5.0) -> Optional[str]:
    """Search Pixabay for a video clip matching keyword. Returns download URL."""
    params = urllib.parse.urlencode({
        "key":        api_key,
        "q":          keyword,
        "video_type": "film",
        "per_page":   10,
        "safesearch": "true",
        "order":      "popular",
    })
    url = f"{PIXABAY_BASE}?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "VidCode/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        hits = data.get("hits", [])
        if not hits:
            return None
        # Pick best matching clip (prefer medium quality, ~720p)
        for hit in hits:
            videos = hit.get("videos", {})
            for quality in ["medium", "small", "large", "tiny"]:
                clip = videos.get(quality, {})
                url  = clip.get("url")
                if url:
                    return url
    except Exception:
        return None
    return None


def download_video_clip(url: str, out_path: Path) -> bool:
    """Download a video clip from URL to out_path."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "VidCode/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            out_path.write_bytes(resp.read())
        return out_path.exists() and out_path.stat().st_size > 1000
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════
# STEP 4 — EDGE-TTS VOICEOVER (Synchronous wrappers)
# ══════════════════════════════════════════════════════════════════════

SILENT_MP3 = b"\xff\xfb\x90\x64" + b"\x00" * 1024

async def _gen_voice(text: str, voice_id: str, out: Path) -> Path:
    if not text.strip():
        out.write_bytes(SILENT_MP3)
        return out
    try:
        communicate = edge_tts.Communicate(text, voice_id)
        await communicate.save(str(out))
        if not out.exists() or out.stat().st_size < 100:
            raise ValueError("Empty")
    except Exception:
        out.write_bytes(SILENT_MP3)
    return out

def gen_voice(text: str, voice_id: str, out: Path) -> Path:
    return asyncio.run(_gen_voice(text, voice_id, out))


def probe_duration(path: Path) -> float:
    ffmpeg = get_ffmpeg()
    try:
        res = subprocess.run([ffmpeg, "-i", str(path)],
                             stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        for line in res.stderr.splitlines():
            if "Duration:" in line:
                dur_str = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = dur_str.split(":")
                return max(2.5, float(h) * 3600 + float(m) * 60 + float(s) + 0.4)
    except Exception:
        pass
    return 5.0

def get_ffmpeg() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


# ══════════════════════════════════════════════════════════════════════
# STEP 5 — FFMPEG: TRIM CLIP + MERGE AUDIO + BURN SUBTITLES
# ══════════════════════════════════════════════════════════════════════

def process_scene_clip(
    raw_clip: Path,
    audio:    Path,
    narration: str,
    duration: float,
    out:      Path,
) -> bool:
    """
    - Trim/loop the stock video to match audio duration
    - Merge voiceover audio  
    - Burn subtitle text onto video
    """
    ffmpeg = get_ffmpeg()

    # Escape narration for FFmpeg drawtext
    safe_text = narration[:80].replace("'", "\\'").replace(":", "\\:").replace("\\", "\\\\")
    if len(narration) > 80:
        safe_text += "..."

    # Wrap text at ~40 chars per line
    wrapped_lines = textwrap.fill(safe_text, width=48).replace("\n", "\n")

    # Build filter: loop video if shorter than audio, then overlay subtitle bar + text
    vf = (
        f"scale=1920:1080:force_original_aspect_ratio=increase,"
        f"crop=1920:1080,"
        f"setsar=1,"
        # Dark gradient bar at bottom for subtitle
        f"drawbox=x=0:y=ih-180:w=iw:h=180:color=black@0.72:t=fill,"
        # Subtitle text
        f"drawtext=text='{wrapped_lines}':"
        f"fontsize=42:fontcolor=white:"
        f"x=(w-text_w)/2:y=h-160:"
        f"line_spacing=12:"
        f"shadowcolor=black:shadowx=2:shadowy=2"
    )

    cmd = [
        ffmpeg, "-y",
        "-stream_loop", "-1",        # Loop video if needed
        "-i", str(raw_clip),         # Stock video
        "-i", str(audio),            # Voiceover
        "-vf", vf,
        "-c:v", "libx264",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-t", str(duration),         # Trim to audio length
        "-map", "0:v:0",             # Video from stock clip
        "-map", "1:a:0",             # Audio from voiceover
        "-shortest",
        str(out),
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    return out.exists() and out.stat().st_size > 0


def fallback_color_clip(
    narration: str,
    duration: float,
    audio: Path,
    out: Path,
    color: str = "0x0a0f23",
) -> bool:
    """Generate a solid-color clip with subtitle if no stock video found."""
    ffmpeg = get_ffmpeg()
    safe_text = narration[:80].replace("'", "\\'").replace(":", "\\:").replace("\\", "\\\\")
    wrapped   = textwrap.fill(safe_text, width=48)

    colors = ["0x0a0f23", "0x1a0a0a", "0x0a1a0a", "0x1a0a1a", "0x0f0f1a"]
    import random
    bg = random.choice(colors)

    cmd = [
        ffmpeg, "-y",
        "-f", "lavfi",
        "-i", f"color=c={bg}:s=1920x1080:r=30",
        "-i", str(audio),
        "-vf", (
            f"drawbox=x=0:y=ih-180:w=iw:h=180:color=black@0.8:t=fill,"
            f"drawtext=text='{wrapped}':fontsize=48:fontcolor=white:"
            f"x=(w-text_w)/2:y=h-155:line_spacing=14:"
            f"shadowcolor=black:shadowx=2:shadowy=2"
        ),
        "-c:v", "libx264",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-t", str(duration),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        str(out),
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    return out.exists() and out.stat().st_size > 0


def assemble_final(clips: List[Path], out_mp4: Path) -> bool:
    ffmpeg = get_ffmpeg()
    concat = out_mp4.parent / "concat.txt"
    with open(concat, "w", encoding="utf-8") as f:
        for c in clips:
            f.write(f"file '{c.resolve().as_posix()}'\n")
    cmd = [
        ffmpeg, "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat),
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(out_mp4),
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
    return out_mp4.exists() and out_mp4.stat().st_size > 0


# ══════════════════════════════════════════════════════════════════════
# MAIN PIPELINE — 100% SYNCHRONOUS
# ══════════════════════════════════════════════════════════════════════

def run_pipeline():
    show_banner()

    # ── API Key ────────────────────────────────────────────────────────
    pixabay_key = load_pixabay_key()
    if not pixabay_key:
        pixabay_key = ask_for_pixabay_key()

    # ── Step 1: Q&A ───────────────────────────────────────────────────
    details = ask_user_requirements()

    console.print()
    console.print(Panel(
        f"[bold white]📌 Topic:[/]       [cyan]{details['topic']}[/]\n"
        f"[bold white]🎬 Type:[/]        {details['video_type']}\n"
        f"[bold white]⏱  Duration:[/]    [yellow]{details['duration_label']}[/]\n"
        f"[bold white]👥 Audience:[/]    {details['audience']}\n"
        f"[bold white]🎭 Tone:[/]        [magenta]{details['tone']}[/]\n"
        f"[bold white]🗣  Language:[/]    [green]{details['language']}[/]\n"
        f"[bold white]🎙  Voice:[/]       {details['voice_name']}",
        title="✅  Confirm Your Video",
        border_style="bright_cyan",
    ))
    console.print()

    if not questionary.confirm(
        "🚀  Sab theek hai? Real video generation shuru karein?",
        default=True, style=custom_style,
    ).ask():
        console.print("[yellow]Cancelled.[/]")
        return

    # Setup dirs
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = "".join(c if c.isalnum() else "_" for c in details["topic"][:25]).strip("_")
    proj = OUTPUT_BASE / f"{slug}_{ts}"
    scenes_dir = proj / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)

    # ── Step 2: AI Script ─────────────────────────────────────────────
    step_header(2, "AI Script Generation — Gemini", "🧠")
    with Progress(SpinnerColumn(spinner_name="dots12", style="bright_cyan"),
                  TextColumn("[bold cyan]{task.description}"),
                  TimeElapsedColumn(), console=console) as prog:
        t = prog.add_task("Gemini AI se script ban raha hai (~15-20 sec)...", total=None)
        script_data = generate_script(details)
        prog.update(t, description="[bold green]✓  Script ready!")

    console.print()
    console.print(Panel(
        f"[bold bright_green]🎬 Title:[/]   {script_data.get('title', details['topic'])}\n"
        f"[bold yellow]⚡ Hook:[/]    {script_data.get('hook', '')}\n"
        f"[bold cyan]📋 Logline:[/] {script_data.get('logline', '')}\n"
        f"[bold magenta]📢 CTA:[/]     {script_data.get('call_to_action', '')}",
        title="🌟 AI Script",
        border_style="bright_green",
    ))

    scenes = script_data.get("scenes", [])
    if not scenes:
        n = max(2, details["duration_seconds"] // 15)
        scenes = [{
            "scene_number": i + 1,
            "title": ["Hook", "Problem", "Solution", "CTA"][i % 4],
            "duration_seconds": details["duration_seconds"] // n,
            "narration": f"{details['topic']} — Scene {i+1}",
            "action": "product shot",
            "video_search_keyword": details["topic"].split()[0],
        } for i in range(n)]

    # ── Step 3: Voiceover + Stock Video + Scene Compile ───────────────
    step_header(3, "Real Stock Footage + Voiceover + Subtitles", "🎬")
    scene_clips: List[Path] = []
    stock_found = 0

    with Progress(
        SpinnerColumn(style="bright_yellow"),
        TextColumn("[bold white]{task.description}"),
        BarColumn(bar_width=28, style="bright_blue", complete_style="bright_green"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as prog:
        render_task = prog.add_task("Scenes rendering...", total=len(scenes))

        for idx, scene in enumerate(scenes):
            snum  = scene.get("scene_number", idx + 1)
            narr  = (scene.get("narration") or scene.get("dialogue") or f"{details['topic']}.").strip()
            kw    = scene.get("video_search_keyword") or details["topic"].split()[0]

            # Voiceover
            prog.update(render_task, description=f"Scene {snum}/{len(scenes)}: AI Voiceover...")
            audio_path = scenes_dir / f"audio_{snum}.mp3"
            gen_voice(narr, details["voice_id"], audio_path)
            duration = probe_duration(audio_path)

            # Stock video
            prog.update(render_task, description=f"Scene {snum}/{len(scenes)}: Stock footage ({kw[:20]})...")
            raw_clip  = scenes_dir / f"raw_{snum}.mp4"
            clip_url  = search_pixabay_video(kw, pixabay_key, duration)
            got_stock = False

            if clip_url:
                got_stock = download_video_clip(clip_url, raw_clip)
                if got_stock:
                    stock_found += 1

            # Compile scene clip
            prog.update(render_task, description=f"Scene {snum}/{len(scenes)}: FFmpeg compile...")
            clip_path = scenes_dir / f"clip_{snum}.mp4"

            if got_stock:
                ok = process_scene_clip(raw_clip, audio_path, narr, duration, clip_path)
            else:
                ok = fallback_color_clip(narr, duration, audio_path, clip_path)

            if ok:
                scene_clips.append(clip_path)
            prog.advance(render_task)

    # ── Step 4: Final Assembly ─────────────────────────────────────────
    step_header(4, "Final Master Video Assembly", "🎞️")
    final_mp4 = proj / f"{slug}_FINAL.mp4"

    with Progress(SpinnerColumn(style="bright_magenta"),
                  TextColumn("[bold magenta]{task.description}"),
                  TimeElapsedColumn(), console=console) as prog:
        t = prog.add_task(f"Sabhi {len(scene_clips)} scenes → 1080p MP4...", total=None)
        ok = assemble_final(scene_clips, final_mp4)
        prog.update(t, description="[bold green]✓  Master video ready!")

    # Save script
    (proj / "script.txt").write_text(
        "\n\n".join(
            f"SCENE {s.get('scene_number')}: {s.get('title','')}\n"
            f"[NARRATION] {s.get('narration','')}\n"
            f"[STOCK KEYWORD] {s.get('video_search_keyword','')}"
            for s in scenes
        ),
        encoding="utf-8"
    )
    (proj / "script.json").write_text(json.dumps(script_data, indent=2, ensure_ascii=False), encoding="utf-8")

    # ── Delivery ──────────────────────────────────────────────────────
    console.print()
    console.print(Panel(
        Align.center(Text.from_markup(
            "[bold bright_green]🎉🎉  REAL VIDEO TAYYAR HAI!  🎉🎉[/]\n\n"
            + (f"[bold white]{final_mp4.name}[/]\n[dim]{final_mp4}[/]" if ok else "[yellow]scenes/ folder check karein[/]")
        )),
        border_style="bright_green", padding=(1, 4),
    ))

    table = Table(title="📁  Deliverables", border_style="bright_cyan")
    table.add_column("File", style="bold cyan", min_width=28)
    table.add_column("Description", style="white")
    table.add_row(f"🎬 {final_mp4.name}", f"Real 1080p MP4 Video ({stock_found}/{len(scenes)} real footage clips)")
    table.add_row("📝 script.txt",   "Scene-wise narration + stock keywords")
    table.add_row("📂 scenes/",      "Individual clips + audio files")
    console.print(table)

    if stock_found < len(scenes):
        console.print(f"\n[yellow]ℹ  {len(scenes) - stock_found} scene(s) mein stock footage nahi mila — colored background use kiya gaya.[/]")
        console.print("[dim]Tip: Keyword aur specific rakhein jaise 'food delivery india' instead of brand name.[/]")

    console.print()
    console.print(Panel(f"[bold bright_yellow]📂 Folder:[/]\n[white]{proj}[/]",
                        border_style="bright_yellow", padding=(0, 2)))

    console.print()
    if ok and final_mp4.exists():
        if questionary.confirm("▶️   Abhi video play karein?", default=True, style=custom_style).ask():
            try:
                os.startfile(str(final_mp4))
            except Exception:
                subprocess.Popen(["cmd", "/c", "start", "", str(final_mp4)])

    if questionary.confirm("📂  Output folder kholein?", default=True, style=custom_style).ask():
        try:
            subprocess.Popen(["explorer", str(proj)])
        except Exception:
            pass

    console.print()
    if questionary.confirm("🔄  Ek aur video banana hai?", default=False, style=custom_style).ask():
        run_pipeline()
    else:
        console.print()
        console.print(Panel(
            Align.center(Text.from_markup(
                "[bold bright_cyan]Thank you for using VidCode AI Studio! ❤️[/]\n"
                "[dim]Real video output_videos/ folder me save hai[/]"
            )),
            border_style="bright_cyan", padding=(1, 4),
        ))


if __name__ == "__main__":
    try:
        run_pipeline()
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped. Phir milenge! 👋[/]")
