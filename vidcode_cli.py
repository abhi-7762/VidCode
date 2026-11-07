#!/usr/bin/env python3
"""
VidCode — Real Ad Video Generator CLI
======================================
Pexels/Pixabay real stock footage + Edge-TTS voice + FFmpeg subtitles = Real video!
Gemini optional — agar kaam na kare to manual script bhi likhwa sakte ho.
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
    ("qmark",       "fg:#00d7ff bold"),("question","bold fg:#ffffff"),
    ("answer",      "fg:#00ff87 bold"),("pointer","fg:#ff5fd7 bold"),
    ("highlighted", "fg:#ff5fd7 bold"),("selected","fg:#00ff87"),
    ("instruction", "fg:#858585 italic"),("text","fg:#ffffff"),
])

PIXABAY_BASE = "https://pixabay.com/api/videos/"

# ══════════════════════════════════════
# ENV HELPERS
# ══════════════════════════════════════
def _env_get(key):
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if line.startswith(f"{key}="):
                val = line.split("=",1)[1].strip()
                if val and "your_" not in val:
                    return val
    return None

def _env_set(key, val):
    content = ENV_FILE.read_text(encoding="utf-8") if ENV_FILE.exists() else ""
    if f"{key}=" in content:
        lines = [f"{key}={val}" if l.startswith(f"{key}=") else l for l in content.splitlines()]
        ENV_FILE.write_text("\n".join(lines), encoding="utf-8")
    else:
        with open(ENV_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n{key}={val}\n")

# ══════════════════════════════════════
# BANNER
# ══════════════════════════════════════
def banner():
    console.print()
    console.print(Panel(Align.center(Text.from_markup(
        "[bold cyan]🎬  V I D C O D E   A I   S T U D I O  🎬[/]\n"
        "[bold white]Real Ad Video Generator[/]\n\n"
        "[yellow]Idea batao → Real Stock Footage → AI Voice → 1080p MP4![/]"
    )), border_style="bright_cyan", padding=(1,4)))
    console.print()

def step(n, title, emoji="▶"):
    console.print()
    console.print(Rule(f"[bold bright_yellow]{emoji}  Step {n}: {title}[/]", style="bright_yellow"))
    console.print()

# ══════════════════════════════════════
# STEP 1 — Q&A
# ══════════════════════════════════════
def ask_requirements() -> dict:
    step(1, "Video Details", "🎯")
    console.print("[dim]Jawab do — AI aapka real video banayega![/]\n")

    vtype = questionary.select("📺  Kaisa video banana hai?", style=custom_style, choices=[
        "Commercial Ad / Product Advertisement",
        "Social Media Reel / Short Video",
        "Explainer / Tutorial Video",
        "Corporate Brand Video",
        "E-Commerce Product Showcase",
    ]).ask() or sys.exit(0)

    console.print()
    topic = questionary.text(
        "🎯  Topic / Product / Brand naam?\n   (e.g. 'Ambika Rasoi Tiffin Service, Dumka'):",
        validate=lambda t: True if len(t.strip())>2 else "Topic enter karo.",
        style=custom_style,
    ).ask() or sys.exit(0)

    console.print()
    dur = questionary.select("⏱️   Duration?", style=custom_style, choices=[
        "15 seconds","30 seconds","45 seconds","60 seconds",
    ]).ask()
    dur_map = {"15 seconds":15,"30 seconds":30,"45 seconds":45,"60 seconds":60}
    duration = dur_map.get(dur, 30)

    console.print()
    lang = questionary.select("🗣️   Language?", style=custom_style, choices=[
        "🇮🇳  Hinglish (Hindi+English — Best for Indian Ads)",
        "🇮🇳  Hindi",
        "🇬🇧  English",
    ]).ask()

    voice_opts = {
        "🇮🇳  Hinglish (Hindi+English — Best for Indian Ads)": [
            ("Prabhat (Indian English Male)", "en-IN-PrabhatNeural"),
            ("Neerja (Indian English Female)","en-IN-NeerjaNeural"),
            ("Madhur (Hindi Male)",           "hi-IN-MadhurNeural"),
        ],
        "🇮🇳  Hindi": [
            ("Madhur (Hindi Male)",   "hi-IN-MadhurNeural"),
            ("Swara (Hindi Female)",  "hi-IN-SwaraNeural"),
        ],
        "🇬🇧  English": [
            ("Christopher (US Male)", "en-US-ChristopherNeural"),
            ("Jenny (US Female)",     "en-US-JennyNeural"),
            ("Ryan (UK Male)",        "en-GB-RyanNeural"),
        ],
    }
    console.print()
    opts = voice_opts.get(lang, voice_opts["🇬🇧  English"])
    vname = questionary.select("🎙️   Voice?", style=custom_style, choices=[v[0] for v in opts]).ask()
    vid   = next((v[1] for v in opts if v[0]==vname), "en-US-ChristopherNeural")

    console.print()
    extra = questionary.text(
        "✨  Special offer / phone number / USP? (Optional — Enter skip):", style=custom_style
    ).ask() or ""

    return {"type":vtype,"topic":topic.strip(),"duration":duration,"language":lang,
            "voice_name":vname,"voice_id":vid,"extra":extra.strip()}

# ══════════════════════════════════════
# STEP 2 — SCRIPT (Gemini OR Manual)
# ══════════════════════════════════════
def call_gemini_rest(prompt: str, api_key: str, timeout: int = 25) -> Optional[str]:
    """Direct REST call to Gemini — no SDK, no gRPC."""
    import urllib.request, urllib.error
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={api_key}"
    body = json.dumps({"contents":[{"parts":[{"text": prompt}]}]}).encode()
    req  = urllib.request.Request(url, data=body,
                                  headers={"Content-Type":"application/json","User-Agent":"VidCode/1.0"},
                                  method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return None

def build_script_via_gemini(details: dict, api_key: str) -> Optional[dict]:
    n = max(2, details["duration"] // 15)
    extra = f"\nSpecial info: {details['extra']}" if details["extra"] else ""
    prompt = f"""You are a world-class video scriptwriter.
Write a {details['duration']}-second high-converting {details['type']} about '{details['topic']}'.
Language: {details['language']} — STRICTLY write narration in this language.
Scenes: exactly {n}{extra}

Rules:
- Scene 1: Scroll-stopping hook (first 3 sec).
- Middle: Problem → Solution → Benefits.
- Last: Call-To-Action.
- Each scene: complete exact spoken narration.
- Each scene: add "keyword" field: 2-3 English words for stock video search.

Return ONLY valid JSON (no markdown):
{{"title":"...","hook":"...","call_to_action":"...","scenes":[{{"num":1,"title":"...","seconds":{details['duration']//n},"narration":"...","keyword":"..."}}]}}"""

    text = call_gemini_rest(prompt, api_key, timeout=25)
    if not text:
        return None
    try:
        text = re.sub(r"```(?:json)?\s*","",text).strip().rstrip("`").strip()
        s,e = text.find("{"), text.rfind("}")+1
        return json.loads(text[s:e])
    except Exception:
        return None

def build_script_manual(details: dict) -> dict:
    """Let user type their own script scenes."""
    console.print()
    console.print(Panel(
        "[yellow]Gemini API abhi available nahi hai.[/]\n"
        "[white]Aap khud apna script likh sakte ho — sirf narration type karo har scene ke liye.[/]",
        border_style="yellow", title="📝 Manual Script Mode"
    ))
    n = max(2, details["duration"] // 15)
    scenes = []
    console.print(f"\n[cyan]Aapka {details['duration']}s video {n} scenes ka hoga.[/]\n")
    for i in range(n):
        console.print(f"[bold yellow]─── Scene {i+1} of {n} ───[/]")
        if i == 0:
            console.print("[dim]Yeh pehla scene hai — ek catchy hook likhna! Dhyan kheenchne wala.[/]")
        elif i == n-1:
            console.print("[dim]Yeh aakhri scene hai — Call to Action! (e.g. 'Aaj hi order karo: 9876543210')[/]")

        narr = questionary.text(
            f"🎤  Scene {i+1} narration (jo bola jayega):",
            style=custom_style,
        ).ask() or f"{details['topic']} — Scene {i+1}."

        kw = questionary.text(
            f"🔍  Scene {i+1} stock video keyword (English, 2-3 words):\n   (e.g. 'food delivery', 'happy family', 'restaurant kitchen'):",
            style=custom_style,
        ).ask() or details["topic"].split()[0]

        scenes.append({
            "num": i+1,
            "title": ["Hook","Story","Benefits","Call to Action"][min(i,3)],
            "seconds": details["duration"] // n,
            "narration": narr.strip(),
            "keyword": kw.strip(),
        })
        console.print()

    return {
        "title": details["topic"],
        "hook":  scenes[0]["narration"][:60],
        "call_to_action": scenes[-1]["narration"][:80],
        "scenes": scenes,
    }

def get_script(details: dict) -> dict:
    api_key = _env_get("GEMINI_API_KEY")
    script  = None

    if api_key:
        console.print("[cyan]  Gemini AI se script generate ho raha hai (25 sec timeout)...[/]")
        script = build_script_via_gemini(details, api_key)
        if script:
            console.print("[bold green]  ✓ Gemini script ready![/]")
        else:
            console.print("[yellow]  Gemini API slow/unavailable — Manual mode pe switch kar raha hai...[/]")

    if not script:
        script = build_script_manual(details)

    # Normalize scene keys
    for i, s in enumerate(script.get("scenes",[])):
        if "scene_number" not in s: s["scene_number"] = s.get("num", i+1)
        if "narration"    not in s: s["narration"]    = s.get("text","")
        if "keyword"      not in s: s["keyword"]      = details["topic"].split()[0]
        if "duration_seconds" not in s: s["duration_seconds"] = s.get("seconds", details["duration"]//max(2,len(script["scenes"])))

    return script

# ══════════════════════════════════════
# STEP 3 — PIXABAY STOCK VIDEO
# ══════════════════════════════════════
def get_pixabay_key() -> Optional[str]:
    key = _env_get("PIXABAY_API_KEY")
    if key:
        return key
    console.print()
    console.print(Panel(
        "[bold white]Real stock footage ke liye Pixabay API key chahiye![/]\n\n"
        "[cyan]1.[/] [link=https://pixabay.com/accounts/register/]pixabay.com/accounts/register[/] pe FREE signup karo\n"
        "[cyan]2.[/] [link=https://pixabay.com/api/docs/]pixabay.com/api/docs[/] pe API key copy karo\n\n"
        "[dim]Already key hai? Paste karo:[/]",
        title="🔑 Pixabay API Key", border_style="bright_yellow"
    ))
    console.print()
    key = questionary.text("🔑  Pixabay API key (ya Enter dabao colored background ke liye):",
                           style=custom_style).ask() or ""
    if key.strip():
        _env_set("PIXABAY_API_KEY", key.strip())
        return key.strip()
    return None

def pixabay_search(keyword: str, api_key: str) -> Optional[str]:
    params = urllib.parse.urlencode({"key":api_key,"q":keyword,"video_type":"film","per_page":8,"safesearch":"true","order":"popular"})
    req = urllib.request.Request(f"{PIXABAY_BASE}?{params}", headers={"User-Agent":"VidCode/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            data = json.loads(r.read().decode())
        for hit in data.get("hits",[]):
            for q in ["medium","small","large","tiny"]:
                url = hit.get("videos",{}).get(q,{}).get("url")
                if url: return url
    except Exception:
        pass
    return None

def download_clip(url: str, out: Path) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"VidCode/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            out.write_bytes(r.read())
        return out.exists() and out.stat().st_size > 2000
    except Exception:
        return False

# ══════════════════════════════════════
# STEP 4 — EDGE-TTS VOICE
# ══════════════════════════════════════
SILENT = b"\xff\xfb\x90\x64" + b"\x00"*1024

async def _voice(text, voice_id, out):
    try:
        await edge_tts.Communicate(text, voice_id).save(str(out))
        if not out.exists() or out.stat().st_size < 100: raise ValueError
    except Exception:
        out.write_bytes(SILENT)
    return out

def gen_voice(text, voice_id, out):
    return asyncio.run(_voice(text, voice_id, Path(out)))

def probe_dur(path: Path) -> float:
    try:
        r = subprocess.run([FFMPEG,"-i",str(path)], stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        for line in r.stderr.splitlines():
            if "Duration:" in line:
                d = line.split("Duration:")[1].split(",")[0].strip()
                h,m,s = d.split(":")
                return max(2.5, float(h)*3600+float(m)*60+float(s)+0.4)
    except Exception: pass
    return 4.5

# ══════════════════════════════════════
# STEP 5 — FFMPEG SCENE RENDER
# ══════════════════════════════════════
def render_scene(raw_clip: Optional[Path], audio: Path, narration: str,
                 duration: float, out: Path, topic: str) -> bool:
    safe = narration[:90].replace("'","\\'").replace(":","\\:").replace("\\","\\\\")
    if len(narration)>90: safe += "..."
    wrapped = textwrap.fill(safe, 48).replace("\n","\\n")

    sub_filter = (
        "drawbox=x=0:y=ih-190:w=iw:h=190:color=black@0.75:t=fill,"
        f"drawtext=text='{wrapped}':fontsize=44:fontcolor=white:"
        "x=(w-text_w)/2:y=h-170:line_spacing=12:"
        "shadowcolor=black:shadowx=2:shadowy=2"
    )

    if raw_clip and raw_clip.exists() and raw_clip.stat().st_size > 2000:
        cmd = [
            FFMPEG, "-y",
            "-stream_loop","-1","-i", str(raw_clip),
            "-i", str(audio),
            "-vf", f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1,{sub_filter}",
            "-c:v","libx264","-c:a","aac","-b:a","192k",
            "-pix_fmt","yuv420p","-t",str(duration),
            "-map","0:v:0","-map","1:a:0","-shortest",
            str(out),
        ]
    else:
        # Color background fallback with brand name
        brand = topic.upper()[:30]
        brand_safe = brand.replace("'","\\'").replace(":","\\:")
        cmd = [
            FFMPEG, "-y",
            "-f","lavfi","-i",f"color=c=0x0d1b2a:s=1920x1080:r=30",
            "-i", str(audio),
            "-vf", (
                f"drawtext=text='{brand_safe}':fontsize=72:fontcolor=0x38bdf8:"
                f"x=(w-text_w)/2:y=h/2-120:shadowcolor=black:shadowx=3:shadowy=3,"
                f"{sub_filter}"
            ),
            "-c:v","libx264","-c:a","aac","-b:a","192k",
            "-pix_fmt","yuv420p","-t",str(duration),
            "-map","0:v:0","-map","1:a:0","-shortest",
            str(out),
        ]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    return out.exists() and out.stat().st_size > 0

def final_assemble(clips: List[Path], out: Path) -> bool:
    concat = out.parent/"concat.txt"
    with open(concat,"w",encoding="utf-8") as f:
        f.writelines(f"file '{c.resolve().as_posix()}'\n" for c in clips)
    r = subprocess.run([
        FFMPEG,"-y","-f","concat","-safe","0","-i",str(concat),
        "-c:v","libx264","-c:a","aac","-pix_fmt","yuv420p",
        "-movflags","+faststart",str(out)
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
    return out.exists() and out.stat().st_size > 0

# ══════════════════════════════════════
# MAIN
# ══════════════════════════════════════
def run():
    banner()

    # Pixabay key
    pixabay_key = get_pixabay_key()

    # Step 1
    details = ask_requirements()

    console.print()
    console.print(Panel(
        f"[bold white]📌 Topic:[/]    [cyan]{details['topic']}[/]\n"
        f"[bold white]🎬 Type:[/]     {details['type']}\n"
        f"[bold white]⏱  Duration:[/] [yellow]{details['duration']} seconds[/]\n"
        f"[bold white]🎙  Voice:[/]    {details['voice_name']}\n"
        f"[bold white]🗣  Language:[/] {details['language']}"
        + (f"\n[bold white]✨ Offer:[/]    {details['extra']}" if details['extra'] else ""),
        title="✅  Your Video", border_style="bright_cyan",
    ))
    console.print()

    if not questionary.confirm("🚀  Shuru karein?", default=True, style=custom_style).ask():
        return

    # Setup
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = "".join(c if c.isalnum() else "_" for c in details["topic"][:20]).strip("_")
    proj = OUTPUT_BASE / f"{slug}_{ts}"
    sdir = proj/"scenes"
    sdir.mkdir(parents=True, exist_ok=True)

    # Step 2: Script
    step(2, "Script Generation", "✍️")
    with Progress(SpinnerColumn(spinner_name="dots12",style="bright_cyan"),
                  TextColumn("[bold cyan]{task.description}"),
                  TimeElapsedColumn(), console=console) as prog:
        t = prog.add_task("Script ban raha hai...", total=None)
        script = get_script(details)
        prog.update(t, description="[bold green]✓ Script ready!")

    console.print()
    console.print(Panel(
        f"[bold green]🎬 Title:[/] {script.get('title','')}\n"
        f"[bold yellow]⚡ Hook:[/]  {script.get('hook','')[:100]}\n"
        f"[bold cyan]📢 CTA:[/]   {script.get('call_to_action','')[:80]}",
        title="🌟 Script", border_style="bright_green",
    ))

    scenes = script.get("scenes", [])

    # Step 3+4+5: Per scene — voice + footage + compile
    step(3, "Real Footage + Voiceover + Subtitles per Scene", "🎬")
    clips = []
    stock_count = 0

    with Progress(
        SpinnerColumn(style="bright_yellow"),
        TextColumn("[bold white]{task.description}"),
        BarColumn(bar_width=25, style="bright_blue", complete_style="bright_green"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as prog:
        task = prog.add_task("Rendering...", total=len(scenes))

        for idx, scene in enumerate(scenes):
            snum  = scene.get("scene_number", idx+1)
            narr  = scene.get("narration","").strip() or f"{details['topic']} scene {snum}."
            kw    = scene.get("keyword","") or details["topic"].split()[0]

            # Voice
            prog.update(task, description=f"Scene {snum}/{len(scenes)}: AI voice ({details['voice_name'][:15]})...")
            audio = sdir/f"audio_{snum}.mp3"
            gen_voice(narr, details["voice_id"], audio)
            duration = probe_dur(audio)

            # Stock footage
            raw = sdir/f"raw_{snum}.mp4"
            got_stock = False
            if pixabay_key:
                prog.update(task, description=f"Scene {snum}/{len(scenes)}: Pixabay ({kw[:20]})...")
                url = pixabay_search(kw, pixabay_key)
                if url:
                    got_stock = download_clip(url, raw)
                    if got_stock: stock_count += 1

            # Render clip
            prog.update(task, description=f"Scene {snum}/{len(scenes)}: FFmpeg render...")
            clip = sdir/f"clip_{snum}.mp4"
            render_scene(raw if got_stock else None, audio, narr, duration, clip, details["topic"])
            if clip.exists():
                clips.append(clip)
            prog.advance(task)

    # Final assembly
    step(4, "Final Video Assembly", "🎞️")
    final = proj/f"{slug}_FINAL.mp4"
    with Progress(SpinnerColumn(style="bright_magenta"),
                  TextColumn("[bold magenta]{task.description}"),
                  TimeElapsedColumn(), console=console) as prog:
        t = prog.add_task(f"Joining {len(clips)} scenes → 1080p MP4...", total=None)
        ok = final_assemble(clips, final)
        prog.update(t, description="[bold green]✓ Done!")

    # Save files
    (proj/"script.json").write_text(json.dumps(script,indent=2,ensure_ascii=False),encoding="utf-8")
    (proj/"script.txt").write_text(
        "\n\n".join(f"SCENE {s.get('scene_number',i+1)}: {s.get('title','')}\n"
                    f"[NARRATION] {s.get('narration','')}\n"
                    f"[KEYWORD]   {s.get('keyword','')}"
                    for i,s in enumerate(scenes)),
        encoding="utf-8"
    )

    # Delivery
    console.print()
    console.print(Panel(Align.center(Text.from_markup(
        "[bold bright_green]🎉🎉  REAL VIDEO TAYYAR HAI!  🎉🎉[/]\n\n"
        + (f"[bold white]{final.name}[/]\n[dim]{final}[/]" if ok else "[yellow]scenes/ folder check karo[/]")
    )), border_style="bright_green", padding=(1,4)))

    t2 = Table(title="📁 Deliverables", border_style="bright_cyan")
    t2.add_column("File", style="bold cyan", min_width=28)
    t2.add_column("Info", style="white")
    t2.add_row("🎬 "+final.name, f"Real 1080p MP4 ({stock_count}/{len(scenes)} Pixabay clips)")
    t2.add_row("📝 script.txt", "Full scene narration")
    t2.add_row("📂 scenes/", "Individual clips & audio")
    console.print(t2)
    console.print()
    console.print(Panel(f"[bold yellow]📂 Folder:[/]\n{proj}", border_style="bright_yellow", padding=(0,2)))
    console.print()

    if ok and final.exists():
        if questionary.confirm("▶️   Video abhi play karein?", default=True, style=custom_style).ask():
            try: os.startfile(str(final))
            except Exception: subprocess.Popen(["cmd","/c","start","",str(final)])

    if questionary.confirm("📂  Folder kholein?", default=True, style=custom_style).ask():
        try: subprocess.Popen(["explorer", str(proj)])
        except Exception: pass

    console.print()
    if questionary.confirm("🔄  Ek aur video?", default=False, style=custom_style).ask():
        run()
    else:
        console.print()
        console.print(Panel(Align.center(Text.from_markup(
            "[bold bright_cyan]Thank you! VidCode AI Studio ❤️[/]\n"
            "[dim]Video output_videos/ folder me save hai[/]"
        )), border_style="bright_cyan", padding=(1,4)))

if __name__ == "__main__":
    try: run()
    except KeyboardInterrupt: console.print("\n[yellow]Stopped. 👋[/]")
