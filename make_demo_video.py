#!/usr/bin/env python3
"""
VidCode — Instant Demo Video Maker
====================================
Ambika Rasoi Tiffin Service ka 30-second real ad video.
Koi questions nahi, koi Gemini nahi — seedha video!
"""

import sys, os, asyncio, subprocess, textwrap, urllib.request, urllib.parse, json
from pathlib import Path

BASE_DIR    = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
VENV_PYTHON = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"
if VENV_PYTHON.exists() and Path(sys.executable).resolve() != VENV_PYTHON.resolve():
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON)] + sys.argv)

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.text import Text
    from rich.align import Align
    import edge_tts
    import imageio_ffmpeg
except ImportError as e:
    print(f"Missing: {e}")
    sys.exit(1)

console = Console()
FFMPEG  = imageio_ffmpeg.get_ffmpeg_exe()
OUTPUT  = BASE_DIR / "output_videos"
OUTPUT.mkdir(exist_ok=True)

PIXABAY_KEY = "58479726-f72410b64fc9ec06492990f7d"

# ─── HARDCODED SCRIPT ──────────────────────────────────────────────────
SCENES = [
    {
        "id":       1,
        "narration":"Dumka mein ghar jaisa khana chahiye? Ambika Rasoi laaya hai aapke liye freshest tiffin service!",
        "keyword":  "indian food cooking",
        "duration": 8,
    },
    {
        "id":       2,
        "narration":"Daily fresh vegetables, no preservatives, bilkul maa ke haath jaisa swad — har din aapke doorstep pe!",
        "keyword":  "healthy food delivery",
        "duration": 9,
    },
    {
        "id":       3,
        "narration":"Monthly plan sirf 2499 rupaye! Normal price 2999 tha — aaj hi order karo, limited seats hain!",
        "keyword":  "food subscription deal",
        "duration": 7,
    },
    {
        "id":       4,
        "narration":"Ambika Rasoi — Dumka ka number one tiffin service. Call karo aur aaj se hi shuru karo!",
        "keyword":  "restaurant service customer",
        "duration": 6,
    },
]

BRAND = "AMBIKA RASOI"
VOICE = "en-IN-PrabhatNeural"

# ─── HELPERS ──────────────────────────────────────────────────────────
SILENT = b"\xff\xfb\x90\x64" + b"\x00" * 1024

async def _voice(text: str, out: Path):
    try:
        await edge_tts.Communicate(text, VOICE).save(str(out))
        if not out.exists() or out.stat().st_size < 100:
            raise ValueError
    except Exception:
        out.write_bytes(SILENT)

def gen_voice(text: str, out: Path):
    asyncio.run(_voice(text, out))

def probe_dur(path: Path) -> float:
    try:
        r = subprocess.run([FFMPEG, "-i", str(path)], stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        for line in r.stderr.splitlines():
            if "Duration:" in line:
                d = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = d.split(":")
                return max(2.5, float(h)*3600 + float(m)*60 + float(s) + 0.3)
    except Exception:
        pass
    return 5.0

def download_clip(keyword: str, out: Path) -> bool:
    params = urllib.parse.urlencode({
        "key": PIXABAY_KEY, "q": keyword,
        "video_type": "film", "per_page": 10,
        "safesearch": "true", "order": "popular",
    })
    try:
        req = urllib.request.Request(
            f"https://pixabay.com/api/videos/?{params}",
            headers={"User-Agent": "VidCode/1.0"},
        )
        with urllib.request.urlopen(req, timeout=12) as r:
            data = json.loads(r.read().decode())
        for hit in data.get("hits", []):
            for q in ["medium", "small", "large", "tiny"]:
                url = hit.get("videos", {}).get(q, {}).get("url")
                if url:
                    r2 = urllib.request.Request(url, headers={"User-Agent": "VidCode/1.0"})
                    with urllib.request.urlopen(r2, timeout=30) as resp:
                        out.write_bytes(resp.read())
                    return out.exists() and out.stat().st_size > 2000
    except Exception:
        pass
    return False

def render_scene(raw: Path, audio: Path, narration: str, duration: float, out: Path) -> bool:
    safe = narration[:100].replace("'", "\\'").replace(":", "\\:").replace("\\", "\\\\")
    wrapped = textwrap.fill(safe, 46).replace("\n", "\\n")
    brand_safe = BRAND.replace("'", "\\'")

    sub_filter = (
        "drawbox=x=0:y=ih-200:w=iw:h=200:color=black@0.80:t=fill,"
        f"drawtext=text='{wrapped}':"
        "fontsize=46:fontcolor=white:x=(w-text_w)/2:y=h-180:"
        "line_spacing=10:shadowcolor=black:shadowx=2:shadowy=2,"
        f"drawtext=text='{brand_safe}':"
        "fontsize=28:fontcolor=0x38bdf8:x=(w-text_w)/2:y=h-30:"
        "shadowcolor=black:shadowx=1:shadowy=1"
    )

    if raw.exists() and raw.stat().st_size > 2000:
        cmd = [
            FFMPEG, "-y",
            "-stream_loop", "-1", "-i", str(raw),
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
            "-f", "lavfi", "-i", f"color=c=0x0d1b2a:s=1920x1080:r=30",
            "-i", str(audio),
            "-vf", (
                f"drawtext=text='{brand_safe}':"
                "fontsize=90:fontcolor=0x38bdf8:x=(w-text_w)/2:y=h/2-80:"
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

def final_assemble(clips, out: Path) -> bool:
    concat = out.parent / "concat.txt"
    with open(concat, "w", encoding="utf-8") as f:
        f.writelines(f"file '{c.resolve().as_posix()}'\n" for c in clips)
    r = subprocess.run([
        FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
        "-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(out),
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
    return out.exists() and out.stat().st_size > 0


# ─── MAIN ──────────────────────────────────────────────────────────────
def main():
    console.print()
    console.print(Panel(Align.center(Text.from_markup(
        "[bold cyan]🎬  VIDCODE — INSTANT DEMO VIDEO  🎬[/]\n\n"
        "[bold white]Ambika Rasoi Tiffin Service — 30 Second Ad[/]\n"
        "[yellow]Real Pixabay footage + AI Hinglish voice + Subtitles[/]"
    )), border_style="bright_cyan", padding=(1, 4)))
    console.print()

    proj = OUTPUT / "ambika_rasoi_demo"
    proj.mkdir(exist_ok=True)
    sdir = proj / "scenes"
    sdir.mkdir(exist_ok=True)

    clips = []
    stock_count = 0

    with Progress(
        SpinnerColumn(style="bright_yellow"),
        TextColumn("[bold white]{task.description}"),
        BarColumn(bar_width=30, style="bright_blue", complete_style="bright_green"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as prog:
        task = prog.add_task("Building your video...", total=len(SCENES))

        for scene in SCENES:
            sid  = scene["id"]
            narr = scene["narration"]
            kw   = scene["keyword"]
            dur  = float(scene["duration"])

            # 1. Voice
            prog.update(task, description=f"[Scene {sid}/4] 🎙️ AI voice generating...")
            audio = sdir / f"audio_{sid}.mp3"
            gen_voice(narr, audio)
            actual_dur = probe_dur(audio)

            # 2. Stock footage
            prog.update(task, description=f"[Scene {sid}/4] 📹 Downloading '{kw}'...")
            raw = sdir / f"raw_{sid}.mp4"
            got = download_clip(kw, raw)
            if got:
                stock_count += 1

            # 3. Render
            prog.update(task, description=f"[Scene {sid}/4] 🎬 FFmpeg rendering...")
            clip = sdir / f"clip_{sid}.mp4"
            render_scene(raw, audio, narr, actual_dur, clip)
            if clip.exists():
                clips.append(clip)

            prog.advance(task)

    # Final
    final = proj / "ambika_rasoi_30s_ad.mp4"
    console.print()
    with Progress(
        SpinnerColumn(style="bright_magenta"),
        TextColumn("[bold magenta]{task.description}"),
        console=console,
    ) as prog:
        t = prog.add_task(f"Assembling {len(clips)} scenes → Final 1080p video...", total=None)
        ok = final_assemble(clips, final)
        prog.update(t, description="[bold green]✓ Video ready!")

    console.print()
    if ok and final.exists():
        size_mb = final.stat().st_size / (1024*1024)
        console.print(Panel(Align.center(Text.from_markup(
            "[bold bright_green]🎉  AMBIKA RASOI AD VIDEO READY!  🎉[/]\n\n"
            f"[bold white]{final.name}[/]\n"
            f"[dim]Size: {size_mb:.1f} MB  •  {stock_count}/4 real footage clips[/]\n\n"
            f"[cyan]{final}[/]"
        )), border_style="bright_green", padding=(1, 4)))

        console.print()
        console.print("[bold]Script used in video:[/]")
        for s in SCENES:
            console.print(f"  [yellow]Scene {s['id']}:[/] {s['narration']}")

        console.print()
        # Auto play
        try:
            os.startfile(str(final))
            console.print("[green]✓ Video player mein open ho gaya![/]")
        except Exception:
            subprocess.Popen(["cmd", "/c", "start", "", str(final)])

        # Open folder
        try:
            subprocess.Popen(["explorer", str(proj)])
        except Exception:
            pass
    else:
        console.print("[red]Assembly failed — scenes/ folder check karo[/]")
        console.print(f"[dim]Location: {proj}[/]")


if __name__ == "__main__":
    main()

