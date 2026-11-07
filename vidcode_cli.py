#!/usr/bin/env python3
"""
VidCode — Ultimate AI Video Generator CLI Wizard
=================================================
Aapko terminal me interactively poochhega ki kaisa ad ya video chahiye,
Gemini AI se perfect script & storyboard likhwayega,
Edge-TTS se professional voiceover banayega,
aur FFmpeg se scene-by-scene 1080p final playable MP4 video bana kar deliver karega!
"""

import sys
import os
import asyncio
import json
import time
import textwrap
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Ensure backend directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Auto-switch to venv python if running under global python
VENV_PYTHON = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"
if VENV_PYTHON.exists() and Path(sys.executable).resolve() != VENV_PYTHON.resolve():
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON)] + sys.argv)

# Import required libraries
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
    from PIL import Image, ImageDraw
    import imageio_ffmpeg
    import edge_tts
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Run:  cd backend; .venv\\Scripts\\pip install rich questionary pillow edge-tts imageio-ffmpeg")
    sys.exit(1)

# Import VidCode app modules (from backend)
from app.config import get_settings
from app.services.gemini_service import GeminiService
from app.models.script import ScriptGenerateRequest, ScriptTone, ScriptStyle

# ─────────────────────────────────────────────────────────────────────
console = Console()
OUTPUT_BASE = BASE_DIR / "output_videos"
OUTPUT_BASE.mkdir(exist_ok=True)

custom_style = QStyle([
    ("qmark",        "fg:#00d7ff bold"),
    ("question",     "bold fg:#ffffff"),
    ("answer",       "fg:#00ff87 bold"),
    ("pointer",      "fg:#ff5fd7 bold"),
    ("highlighted",  "fg:#ff5fd7 bold"),
    ("selected",     "fg:#00ff87"),
    ("separator",    "fg:#6c6c6c"),
    ("instruction",  "fg:#858585 italic"),
    ("text",         "fg:#ffffff"),
    ("disabled",     "fg:#858585 italic"),
])

THEMES = [
    {"bg_top": (10, 15, 30),  "bg_bot": (20, 30, 60),  "accent": (56, 189, 248)},   # Blue
    {"bg_top": (25, 10, 25),  "bg_bot": (50, 15, 50),  "accent": (244, 114, 182)},  # Magenta
    {"bg_top": (15, 23, 42),  "bg_bot": (30, 41, 59),  "accent": (52, 211, 153)},   # Emerald
    {"bg_top": (28, 15, 10),  "bg_bot": (55, 25, 15),  "accent": (251, 146, 60)},   # Gold
    {"bg_top": (10, 25, 15),  "bg_bot": (15, 50, 30),  "accent": (163, 230, 53)},   # Lime
]

# ─────────────────────────────────────────────────────────────────────
# BANNER
# ─────────────────────────────────────────────────────────────────────

def show_banner():
    console.print()
    console.print(Panel(
        Align.center(Text.from_markup(
            "[bold cyan]🎬  V I D C O D E   A I   S T U D I O  🎬[/]\n"
            "[bold white]Automated Terminal Video Generator[/]\n\n"
            "[yellow]Idea batao → Gemini Script → Voiceover → 1080p MP4 Video Ready![/]"
        )),
        border_style="bright_cyan",
        padding=(1, 4),
    ))
    console.print()

def step_header(num: int, title: str, emoji: str = "▶"):
    console.print()
    console.print(Rule(f"[bold bright_yellow]{emoji}  Step {num}: {title}[/]", style="bright_yellow"))
    console.print()

# ─────────────────────────────────────────────────────────────────────
# STEP 1 — INTERACTIVE Q&A
# ─────────────────────────────────────────────────────────────────────

def ask_user_requirements() -> dict:
    step_header(1, "Aapka Video Vision", "🎯")
    console.print("[dim]Neeche diye gaye sawalon ke jawab dein. AI aapke liye perfect video tayyar karega![/]\n")

    # 1. Video Type
    video_type = questionary.select(
        "📺 Aapko kaisa ad ya video banana hai?",
        choices=[
            "📢  Commercial Ad / Product Advertisement (Instagram, FB, TV)",
            "📱  Viral Social Media Reel / Short (9:16 Vertical / Fast Hook)",
            "🎓  Explainer / Tutorial Video (Educational & Informative)",
            "🏢  Corporate Brand Story (Company Presentation)",
            "🛍️  E-Commerce / Product Showcase",
            "🚀  Startup Pitch / Teaser Video",
            "🎥  YouTube Long-Form Content",
        ],
        style=custom_style,
    ).ask()
    if not video_type:
        sys.exit(0)

    # 2. Topic
    console.print()
    topic = questionary.text(
        "🎯 Video ka topic, product ya brand ka naam?\n   (e.g. 'Aura Smart Watch Pro', 'AI Coding Course', 'Organic Protein Shake'):",
        validate=lambda t: True if len(t.strip()) > 2 else "Kripya topic enter karein.",
        style=custom_style,
    ).ask()
    if not topic:
        sys.exit(0)

    # 3. Target Audience
    console.print()
    audience = questionary.select(
        "👥 Aapka Target Audience kaun hai?",
        choices=[
            "🧑‍💻  Techies, Developers & Gadget Lovers",
            "🧑‍🎓  Students & Young Generation (18-24)",
            "💼  Professionals & Business Owners (25-45)",
            "💪  Fitness & Health Enthusiasts",
            "🛍️  Online Shoppers & Fashion Lovers",
            "👨‍👩‍👧  Parents & Families",
            "🌍  General Audience (Sabhi ke liye)",
        ],
        style=custom_style,
    ).ask()

    # 4. Duration
    console.print()
    duration_choice = questionary.select(
        "⏱️  Video kitne seconds ka hona chahiye?",
        choices=[
            "15 seconds  (Super Fast Ad / Reel / Hook)",
            "30 seconds  (Standard Commercial Ad)",
            "45 seconds  (Detailed Product Promo)",
            "60 seconds  (Full 1-Minute Story Video)",
            "90 seconds  (Deep Explainer)",
        ],
        style=custom_style,
    ).ask()

    dur_map = {
        "15 seconds  (Super Fast Ad / Reel / Hook)": 15,
        "30 seconds  (Standard Commercial Ad)": 30,
        "45 seconds  (Detailed Product Promo)": 45,
        "60 seconds  (Full 1-Minute Story Video)": 60,
        "90 seconds  (Deep Explainer)": 90,
    }
    duration_seconds = dur_map.get(duration_choice, 30)

    # 5. Tone
    console.print()
    tone_choice = questionary.select(
        "🎭  Video ka tone / vibe kaisa hona chahiye?",
        choices=[
            "🔥  Energetic, High-Paced & Bold (Aggressive Ad hook)",
            "💼  Professional, Premium & Trustworthy (Apple-style luxury)",
            "😂  Funny, Relatable & Entertaining (Viral humour)",
            "🌟  Inspiring, Emotional & Motivational",
            "🔬  Informative, Clear & Educational",
        ],
        style=custom_style,
    ).ask()

    # 6. Language & Voice
    console.print()
    language_choice = questionary.select(
        "🗣️  Script aur Voiceover kis language me chahiye?",
        choices=[
            "🇮🇳  Hinglish (Hindi + English mix — Best for Indian Ads)",
            "🇮🇳  Hindi (Shuddh Hindi)",
            "🇬🇧  English (International / Global)",
        ],
        style=custom_style,
    ).ask()

    voice_map = {
        "🇮🇳  Hinglish (Hindi + English mix — Best for Indian Ads)": [
            ("Prabhat (Indian English Male)", "en-IN-PrabhatNeural"),
            ("Neerja (Indian English Female)", "en-IN-NeerjaNeural"),
            ("Madhur (Hindi Male)", "hi-IN-MadhurNeural"),
            ("Swara (Hindi Female)", "hi-IN-SwaraNeural"),
        ],
        "🇮🇳  Hindi (Shuddh Hindi)": [
            ("Madhur (Deep Hindi Male)", "hi-IN-MadhurNeural"),
            ("Swara (Warm Hindi Female)", "hi-IN-SwaraNeural"),
        ],
        "🇬🇧  English (International / Global)": [
            ("Christopher (Cinematic US Male)", "en-US-ChristopherNeural"),
            ("Jenny (Engaging US Female)", "en-US-JennyNeural"),
            ("Ryan (Sophisticated UK Male)", "en-GB-RyanNeural"),
            ("Sonia (Clear UK Female)", "en-GB-SoniaNeural"),
        ],
    }

    console.print()
    voice_options = voice_map.get(language_choice, voice_map["🇬🇧  English (International / Global)"])
    voice_selection = questionary.select(
        "🎙️  Narration voice kaisi chahiye?",
        choices=[v[0] for v in voice_options],
        style=custom_style,
    ).ask()

    voice_id = next((v[1] for v in voice_options if v[0] == voice_selection), "en-US-ChristopherNeural")

    # 7. Extra Info
    console.print()
    extra = questionary.text(
        "✨  Koi special offer, discount ya USP jo video me zaroor aaye?\n   (Optional — seedha Enter dabayein skip karne ke liye):",
        style=custom_style,
    ).ask() or ""

    return {
        "video_type":       video_type.strip().split("  ", 1)[-1],
        "topic":            topic.strip(),
        "audience":         audience.strip().split("  ", 1)[-1],
        "duration_seconds": duration_seconds,
        "duration_label":   duration_choice,
        "tone":             tone_choice.strip().split("  ", 1)[-1],
        "language":         language_choice.strip().split("  ", 1)[-1],
        "voice_name":       voice_selection,
        "voice_id":         voice_id,
        "extra":            extra.strip(),
    }

# ─────────────────────────────────────────────────────────────────────
# STEP 2 — GEMINI AI: SCRIPT + STORYBOARD
# ─────────────────────────────────────────────────────────────────────

async def generate_ai_assets(details: dict) -> tuple[dict, dict]:
    gemini = GeminiService()

    extra_line = f"\nSpecial highlight / Offer: {details['extra']}" if details["extra"] else ""
    prompt = (
        f"Create a {details['duration_seconds']}-second high-converting {details['video_type']} "
        f"about '{details['topic']}'.\n"
        f"Target Audience: {details['audience']}\n"
        f"Tone: {details['tone']}\n"
        f"Script Language: {details['language']} — write narration STRICTLY in this language.\n"
        f"{extra_line}\n\n"
        "Rules:\n"
        "- Scene 1: Irresistible 3-second scroll-stopping hook.\n"
        "- Middle scenes: Show the problem, solution, key benefits.\n"
        "- Final scene: Clear, compelling Call-To-Action.\n"
        "- Write complete exact spoken words in 'narration' for every scene."
    )

    req = ScriptGenerateRequest(
        project_id="cli_wizard",
        prompt=prompt,
        duration_seconds=details["duration_seconds"],
        tone=ScriptTone.INSPIRATIONAL,
        style=ScriptStyle.STORYTELLING,
        target_audience=details["audience"],
    )

    nlu = await gemini.analyse_prompt(prompt, details["duration_seconds"])
    script_data = await gemini.generate_script(req, nlu)
    storyboard_data = await gemini.generate_storyboard(script_data)

    return script_data, storyboard_data

# ─────────────────────────────────────────────────────────────────────
# STEP 3 — EDGE-TTS VOICEOVER
# ─────────────────────────────────────────────────────────────────────

SILENT_MP3 = b"\xff\xfb\x90\x64" + b"\x00" * 512

async def generate_voiceover(text: str, voice_id: str, out: Path) -> Path:
    if not text.strip():
        out.write_bytes(SILENT_MP3)
        return out
    try:
        communicate = edge_tts.Communicate(text, voice_id)
        await communicate.save(str(out))
        if not out.exists() or out.stat().st_size < 100:
            raise ValueError("Empty file")
    except Exception:
        out.write_bytes(SILENT_MP3)
    return out

def probe_duration(path: Path) -> float:
    """Get audio duration with ffprobe-style parsing."""
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    try:
        res = subprocess.run(
            [ffmpeg, "-i", str(path)],
            stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
        )
        for line in res.stderr.splitlines():
            if "Duration:" in line:
                dur_str = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = dur_str.split(":")
                return max(2.0, float(h) * 3600 + float(m) * 60 + float(s) + 0.5)
    except Exception:
        pass
    return 4.0

# ─────────────────────────────────────────────────────────────────────
# STEP 4 — RENDER 1080P SCENE SLIDE (PILLOW)
# ─────────────────────────────────────────────────────────────────────

def render_slide(
    scene_num: int, total: int,
    title: str, action: str, narration: str,
    duration: float, out_png: Path,
    theme_idx: int = 0,
):
    W, H = 1920, 1080
    t = THEMES[theme_idx % len(THEMES)]
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)

    # Gradient background
    r1, g1, b1 = t["bg_top"]
    r2, g2, b2 = t["bg_bot"]
    for y in range(H):
        f = y / H
        draw.line([(0, y), (W, y)], fill=(
            int(r1 + (r2 - r1) * f),
            int(g1 + (g2 - g1) * f),
            int(b1 + (b2 - b1) * f),
        ))

    ac = t["accent"]

    # Top bar
    draw.rectangle([(0, 0), (W, 90)], fill=(5, 8, 18))
    draw.line([(0, 90), (W, 90)], fill=ac, width=3)
    draw.text((70, 25), "🎬  VIDCODE AI STUDIO", fill=ac)
    draw.text((W - 350, 25), f"SCENE {scene_num} / {total}  •  {duration:.1f}s", fill=(160, 170, 190))

    # Main visual box
    bx1, by1, bx2, by2 = 100, 160, W - 100, 720
    draw.rectangle([(bx1, by1), (bx2, by2)], fill=(10, 15, 28), outline=ac, width=2)

    # Decorative accent corner lines
    for offset in [0, 6, 12]:
        draw.line([(bx1, by1 + offset), (bx1 + 60, by1 + offset)], fill=ac, width=1)
        draw.line([(bx1 + offset, by1), (bx1 + offset, by1 + 60)], fill=ac, width=1)
        draw.line([(bx2, by2 - offset), (bx2 - 60, by2 - offset)], fill=ac, width=1)
        draw.line([(bx2 - offset, by2), (bx2 - offset, by2 - 60)], fill=ac, width=1)

    # Scene number big
    draw.text((bx1 + 50, by1 + 40), f"SCENE {scene_num}", fill=ac)
    draw.text((bx1 + 50, by1 + 90), title.upper(), fill=(241, 245, 249))

    # Divider
    draw.line([(bx1 + 50, by1 + 150), (bx2 - 50, by1 + 150)], fill=(30, 41, 59), width=1)

    # Action text
    draw.text((bx1 + 50, by1 + 175), "📷  VISUAL / CAMERA:", fill=(148, 163, 184))
    wrapped_action = textwrap.fill(action, width=85)
    draw.text((bx1 + 50, by1 + 220), wrapped_action, fill=(209, 213, 219))

    # Bottom subtitle bar
    sb1, sb2 = 750, 1010
    draw.rectangle([(100, sb1), (W - 100, sb2)], fill=(6, 10, 20), outline=(30, 41, 59), width=1)
    draw.line([(100, sb1), (W - 100, sb1)], fill=ac, width=2)
    draw.text((140, sb1 + 20), "🎙️  NARRATION / VOICEOVER:", fill=(250, 204, 21))
    wrapped_narr = textwrap.fill(f'"{narration}"', width=95)
    draw.text((140, sb1 + 65), wrapped_narr, fill=(255, 255, 255))

    img.save(str(out_png), "PNG")

# ─────────────────────────────────────────────────────────────────────
# STEP 5 — FFMPEG SCENE CLIP + MASTER ASSEMBLE
# ─────────────────────────────────────────────────────────────────────

def render_clip(slide: Path, audio: Path, duration: float, out: Path) -> bool:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg, "-y",
        "-loop", "1", "-i", str(slide),
        "-i", str(audio),
        "-c:v", "libx264", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-t", str(duration),
        str(out),
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return out.exists() and out.stat().st_size > 0

def assemble_video(clips: List[Path], out_mp4: Path) -> bool:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    concat = out_mp4.parent / "concat.txt"
    with open(concat, "w", encoding="utf-8") as f:
        for c in clips:
            f.write(f"file '{c.resolve().as_posix()}'\n")

    cmd = [
        ffmpeg, "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat),
        "-c:v", "libx264", "-c:a", "aac",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(out_mp4),
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return out_mp4.exists() and out_mp4.stat().st_size > 0

# ─────────────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────────────

async def run_pipeline():
    show_banner()

    # 1. Gather requirements from user
    details = ask_user_requirements()

    # Confirm
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

    go = questionary.confirm(
        "🚀 Sab kuch theek lag raha hai? Video generation shuru karein?",
        default=True,
        style=custom_style,
    ).ask()

    if not go:
        console.print("[yellow]Cancelled. Dobara chalane ke liye script run karein.[/]")
        return

    # Setup project folder
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = "".join(c if c.isalnum() else "_" for c in details["topic"][:25]).strip("_")
    project_dir = OUTPUT_BASE / f"{slug}_{ts}"
    scenes_dir  = project_dir / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)

    # 2. AI: Script + Storyboard
    step_header(2, "AI Script & Storyboard Generation — Gemini 3.8 Flash", "🧠")

    with Progress(
        SpinnerColumn(spinner_name="dots12", style="bright_cyan"),
        TextColumn("[bold cyan]{task.description}"),
        TimeElapsedColumn(),
        console=console,
    ) as prog:
        t = prog.add_task("Gemini AI se script aur storyboard banwaya ja raha hai...", total=None)
        script_data, storyboard_data = await generate_ai_assets(details)
        prog.update(t, description="[bold green]✓  Script & Storyboard ready!")

    # Print summary
    console.print()
    console.print(Panel(
        f"[bold bright_green]🎬 Title:[/]   {script_data.get('title', details['topic'])}\n"
        f"[bold yellow]⚡ Hook:[/]    {script_data.get('hook', 'Opening hook')}\n"
        f"[bold cyan]📋 Logline:[/] {script_data.get('logline', '')}\n"
        f"[bold magenta]📢 CTA:[/]     {script_data.get('call_to_action', 'Contact us today!')}",
        title="🌟 AI Script Summary",
        border_style="bright_green",
    ))

    scenes = script_data.get("scenes", [])
    if not scenes:
        # Fallback if Gemini returns no scenes
        n_scenes = max(2, details["duration_seconds"] // 15)
        scenes = [
            {
                "scene_number": i + 1,
                "title": ["Hook", "Problem", "Solution", "Benefits", "CTA"][i % 5],
                "duration_seconds": details["duration_seconds"] // n_scenes,
                "narration": f"Scene {i+1}: {details['topic']}.",
                "action": f"Dynamic cinematic shot of {details['topic']}.",
            }
            for i in range(n_scenes)
        ]

    # 3. Voiceover + Slide rendering per scene
    step_header(3, "Scene Rendering — Voiceover + 1080p Slides + Clips", "🎬")

    scene_clips: List[Path] = []

    with Progress(
        SpinnerColumn(style="bright_yellow"),
        TextColumn("[bold white]{task.description}"),
        BarColumn(bar_width=30, style="bright_blue", complete_style="bright_green"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as prog:
        render_task = prog.add_task("Scenes rendering...", total=len(scenes))

        for idx, scene in enumerate(scenes):
            snum  = scene.get("scene_number", idx + 1)
            title = scene.get("title", f"Scene {snum}")
            narr  = (scene.get("narration") or scene.get("dialogue") or f"{details['topic']} scene {snum}.").strip()
            action = (scene.get("action") or "Cinematic product shot").strip()

            prog.update(render_task, description=f"Scene {snum}/{len(scenes)}: Audio...")

            # Audio
            audio_path = scenes_dir / f"audio_{snum}.mp3"
            await generate_voiceover(narr, details["voice_id"], audio_path)
            duration = probe_duration(audio_path)

            prog.update(render_task, description=f"Scene {snum}/{len(scenes)}: Slide frame...")

            # 1080p slide
            slide_path = scenes_dir / f"frame_{snum}.png"
            render_slide(
                scene_num=snum, total=len(scenes),
                title=title, action=action, narration=narr,
                duration=duration, out_png=slide_path,
                theme_idx=idx,
            )

            prog.update(render_task, description=f"Scene {snum}/{len(scenes)}: FFmpeg clip...")

            # Scene MP4 clip
            clip_path = scenes_dir / f"clip_{snum}.mp4"
            render_clip(slide_path, audio_path, duration, clip_path)
            if clip_path.exists():
                scene_clips.append(clip_path)

            prog.advance(render_task)

    # 4. Final Assembly
    step_header(4, "Final Master Video Assembly — FFmpeg", "🎞️")
    final_mp4 = project_dir / f"{slug}_final.mp4"

    with Progress(
        SpinnerColumn(style="bright_magenta"),
        TextColumn("[bold magenta]{task.description}"),
        TimeElapsedColumn(),
        console=console,
    ) as prog:
        t = prog.add_task(f"Sabhi {len(scene_clips)} clips ko master 1080p MP4 mein stitch kar raha hai...", total=None)
        ok = assemble_video(scene_clips, final_mp4)
        prog.update(t, description="[bold green]✓  Master render complete!")

    if not ok or not final_mp4.exists():
        console.print("[red]Video assembly failed. Scenes folder mein individual clips check karein.[/]")
        final_mp4 = scene_clips[0] if scene_clips else None

    # 5. Save production files
    (project_dir / "script.json").write_text(
        json.dumps(script_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (project_dir / "storyboard.json").write_text(
        json.dumps(storyboard_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    script_txt_lines = [
        f"VIDEO TITLE: {script_data.get('title', details['topic'])}",
        f"DURATION: {details['duration_label']}",
        f"HOOK: {script_data.get('hook', '')}",
        f"LOGLINE: {script_data.get('logline', '')}",
        "",
    ]
    for s in scenes:
        script_txt_lines += [
            f"─── SCENE {s.get('scene_number')}: {s.get('title')} ({s.get('duration_seconds', '?')}s) ───",
            f"[VISUAL] {s.get('action', '')}",
            f"[NARRATION] {s.get('narration', '')}",
            "",
        ]
    script_txt_lines.append(f"CALL TO ACTION: {script_data.get('call_to_action', '')}")
    (project_dir / "script.txt").write_text("\n".join(script_txt_lines), encoding="utf-8")

    # Build production brief with AI image prompts from storyboard
    storyboard_scenes = storyboard_data.get("scenes", [])
    brief_lines = [
        f"# 🎬 Video Production Brief\n",
        f"**Topic:** {details['topic']}",
        f"**Type:** {details['video_type']}",
        f"**Duration:** {details['duration_label']}",
        f"**Language:** {details['language']}",
        f"**Voice:** {details['voice_name']}\n",
        "---\n",
        "## Storyboard Scene Prompts (Midjourney / DALL-E / Runway)\n",
    ]
    for i, s in enumerate(storyboard_scenes, 1):
        vp = s.get("visual_prompt") or s.get("action_description") or ""
        brief_lines.append(f"**Scene {i}:** `{vp}, cinematic, 4K, professional photography`")
    (project_dir / "production_brief.md").write_text("\n".join(brief_lines), encoding="utf-8")

    # 6. DELIVERY 🎉
    console.print()
    console.print(Panel(
        Align.center(Text.from_markup(
            "[bold bright_green]🎉🎉  AAPKA VIDEO PURI TARAH TAYYAR HAI!  🎉🎉[/]\n\n"
            + (f"[bold white]{final_mp4.name}[/]\n[dim]{final_mp4}[/]" if final_mp4 else "[yellow]Scenes available in scenes/ folder[/]")
        )),
        border_style="bright_green",
        padding=(1, 4),
    ))

    table = Table(title="📁  Delivered Files", border_style="bright_cyan", show_header=True)
    table.add_column("File", style="bold cyan", min_width=28)
    table.add_column("Description", style="white")
    table.add_row("🎬 " + (final_mp4.name if final_mp4 else "see scenes/"), "Playable 1080p Master MP4 Video")
    table.add_row("📝 script.txt",           "Full readable script with narration")
    table.add_row("🎨 storyboard.json",      "Scene-by-scene cinematography plan")
    table.add_row("🧪 production_brief.md",  "AI image prompts for Midjourney/DALL-E")
    table.add_row("📂 scenes/",              "Individual scene clips + audio files")
    console.print(table)

    console.print()
    console.print(Panel(
        f"[bold bright_yellow]📂 Output Folder:[/]\n"
        f"[white]{project_dir}[/]",
        border_style="bright_yellow",
        padding=(0, 2),
    ))

    # Play & Open options
    console.print()
    if final_mp4 and final_mp4.exists():
        play = questionary.confirm(
            "▶️  Kya video abhi play karke dekhna chahte hain?",
            default=True, style=custom_style,
        ).ask()
        if play:
            try:
                os.startfile(str(final_mp4))
            except Exception:
                subprocess.Popen(["cmd", "/c", "start", "", str(final_mp4)])
            console.print("[green]✓ Video player me open ho gaya![/]")

    open_folder = questionary.confirm(
        "📂  Windows Explorer me output folder kholein?",
        default=True, style=custom_style,
    ).ask()
    if open_folder:
        try:
            subprocess.Popen(["explorer", str(project_dir)])
        except Exception:
            pass

    # Another video?
    console.print()
    again = questionary.confirm(
        "🔄  Ek aur video banana hai?",
        default=False, style=custom_style,
    ).ask()
    if again:
        await run_pipeline()
    else:
        console.print()
        console.print(Panel(
            Align.center(Text.from_markup(
                "[bold bright_cyan]Thank you for using VidCode AI Studio! ❤️[/]\n"
                "[dim]Aapka video output_videos/ folder me save hai[/]"
            )),
            border_style="bright_cyan",
            padding=(1, 4),
        ))


if __name__ == "__main__":
    try:
        asyncio.run(run_pipeline())
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped. Phir milenge! 👋[/]")
