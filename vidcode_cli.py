#!/usr/bin/env python3
"""
VidCode — 9:16 High-Converting Commercial Generator CLI
=========================================================
Generates real 1080x1920 vertical commercial reels (Instagram Reels / YouTube Shorts)
where EVERY scene's visual footage matches the narration 100%.

Features:
- Real HD Stock footage sourced from Pixabay matching the exact scene context
- Studio AI voiceover in natural Hinglish / Hindi / Indian English (Edge-TTS)
- Modern kinetic subtitle cards & high-impact brand overlays
- Instant generation with zero hang / freeze
"""

import sys, os, asyncio, subprocess, urllib.request, urllib.parse, json, textwrap, re
from datetime import datetime
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
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from rich.align import Align
import questionary
from questionary import Style as QStyle

console = Console()
FFMPEG  = imageio_ffmpeg.get_ffmpeg_exe()
OUTPUT_BASE = BASE_DIR / "output_videos" / "commercials"
OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

PIXABAY_KEY = "58479726-f72410b64fc9ec06492990f7d"

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
        "[bold white]9:16 Viral Commercial Generator (Instagram Reels / YouTube Shorts)[/]\n\n"
        "[bold bright_green]✓ Real Matched HD Footage[/]  •  "
        "[bold bright_yellow]✓ Studio AI Voiceover[/]  •  "
        "[bold bright_cyan]✓ Modern Brand Overlays[/]"
    )), border_style="bright_cyan", padding=(1, 4)))
    console.print()

def step(n, title, emoji="▶"):
    console.print()
    console.print(Rule(f"[bold bright_yellow]{emoji}  Step {n}: {title}[/]", style="bright_yellow"))
    console.print()

# ── USER QUESTIONNAIRE ─────────────────────────────────────────────────
def ask_user():
    step(1, "Apne Brand / Ad Ki Details Dein", "🎯")
    console.print("[dim]Neeche diye gaye sawalon ke jawab dein. Visuals aur voice 100% match karenge![/]\n")

    brand = questionary.text(
        "🏢 1. Brand / Business ka naam?\n   (e.g. 'Ambika Rasoi', 'Apex Fitness', 'Digital Gurukul'):",
        validate=lambda t: True if len(t.strip()) > 1 else "Brand naam zaroori hai.",
        style=custom_style,
    ).ask()
    if not brand:
        sys.exit(0)

    console.print()
    service = questionary.text(
        "🎯 2. Kya service / product promote karna hai?\n   (e.g. 'Daily Tiffin & Mess Service', 'Gym Membership', 'Full Stack Web Dev Course'):",
        validate=lambda t: True if len(t.strip()) > 2 else "Service enter karein.",
        style=custom_style,
    ).ask()
    if not service:
        sys.exit(0)

    console.print()
    location = questionary.text(
        "📍 3. City / Area?\n   (e.g. 'Dumka, Jharkhand', 'Delhi NCR', 'Online / Pan India'):",
        style=custom_style,
    ).ask() or "India"

    console.print()
    offer = questionary.text(
        "⚡ 4. Special Offer / Price / Discount?\n   (e.g. 'Monthly Rs. 2499 (Save Rs. 500)', 'Flat 50% Off Today', 'Free Demo Class'):",
        style=custom_style,
    ).ask() or "Special Limited Time Offer"

    console.print()
    phone = questionary.text(
        "📞 5. Contact Number ya Website jo screen pe dikhani hai?\n   (e.g. '9876543210' ya 'www.mybrand.in'):",
        style=custom_style,
    ).ask() or "CALL NOW"

    console.print()
    voice_choice = questionary.select(
        "🎙️ 6. Voiceover Artist & Language?",
        choices=[
            "Prabhat (Indian English Male - Clear & Energetic)",
            "Neerja (Indian English Female - Corporate & Sweet)",
            "Madhur (Hindi Male - Deep, Warm & Friendly)",
            "Swara (Hindi Female - Expressive & Clear)",
        ],
        style=custom_style,
    ).ask()

    voice_map = {
        "Prabhat (Indian English Male - Clear & Energetic)": "en-IN-PrabhatNeural",
        "Neerja (Indian English Female - Corporate & Sweet)":  "en-IN-NeerjaNeural",
        "Madhur (Hindi Male - Deep, Warm & Friendly)":        "hi-IN-MadhurNeural",
        "Swara (Hindi Female - Expressive & Clear)":         "hi-IN-SwaraNeural",
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

# ── SMART MULTI-DOMAIN SCENE GENERATOR ─────────────────────────────────
def generate_matched_storyboard(d: dict) -> list:
    brand = d["brand"]
    serv  = d["service"].lower()
    loc   = d["location"]
    offer = d["offer"]

    # Detect category from keywords
    if any(k in serv for k in ["tiffin", "mess", "food", "khana", "restaurant", "cafe", "meal", "kitchen", "rasoi", "diet"]):
        cat = "food"
    elif any(k in serv for k in ["gym", "fitness", "workout", "trainer", "muscle", "crossfit", "yoga"]):
        cat = "fitness"
    elif any(k in serv for k in ["course", "coding", "software", "academy", "class", "study", "learning", "python", "school"]):
        cat = "education"
    elif any(k in serv for k in ["cloth", "fashion", "boutique", "wear", "shirt", "saree", "dress", "salon"]):
        cat = "fashion"
    elif any(k in serv for k in ["property", "house", "flat", "real estate", "interior", "rent", "builder"]):
        cat = "realestate"
    else:
        cat = "business"

    if cat == "food":
        return [
            {
                "id": 1,
                "search": "indian food curry",
                "badge": "HOMESTYLE TASTE",
                "headline": f"Ghar Jaisa Khana {loc} Mein?",
                "narration": f"{loc} mein ghar jaisa swadisht aur poshtik khana dhoondh rahe hain? Aapka intezaar khatam!",
            },
            {
                "id": 2,
                "search": "vegetables cooking pan",
                "badge": "100% FRESH & HEALTHY",
                "headline": f"{brand} Daily Cooking",
                "narration": f"{brand} laaya hai daily fresh sabziyan, shuddh masale aur maa ke haath jaisa shandar swad!",
            },
            {
                "id": 3,
                "search": "food delivery package",
                "badge": "DOORSTEP DELIVERY",
                "headline": "Hot & Fresh Tiffin Delivery",
                "narration": "Hygienic packaging ke sath rozana aapke doorstep pe garam tiffin time par deliver hota hai!",
            },
            {
                "id": 4,
                "search": "eating delicious restaurant",
                "badge": "SPECIAL OFFER",
                "headline": f"{offer}",
                "narration": f"Special limited offer: {offer}! Aaj hi call karein aur apna slot book karein!",
            },
        ]
    elif cat == "fitness":
        return [
            {
                "id": 1,
                "search": "gym workout training",
                "badge": "TRANSFORM YOURSELF",
                "headline": f"Ready For Fitness in {loc}?",
                "narration": f"Kya aap apni body transform karna chahte hain? {loc} ka sabse modern gym ab aapke pass hai!",
            },
            {
                "id": 2,
                "search": "fitness dumbbell exercise",
                "badge": "WORLD-CLASS GEAR",
                "headline": f"{brand} Fitness Zone",
                "narration": f"{brand} mein milega top imported equipment, certified trainers aur personalized diet plans!",
            },
            {
                "id": 3,
                "search": "running treadmill athlete",
                "badge": "REAL RESULTS",
                "headline": "Power Workout & Cardio",
                "narration": "Fat loss ho ya muscle gain, yahan har goal achieve hota hai best guidance ke sath!",
            },
            {
                "id": 4,
                "search": "healthy body workout",
                "badge": "LIMITED PASSES",
                "headline": f"{offer}",
                "narration": f"Special deal: {offer}! Limited memberships bachi hain, aaj hi call karein!",
            },
        ]
    elif cat == "education":
        return [
            {
                "id": 1,
                "search": "laptop coding programming",
                "badge": "CAREER UPGRADE",
                "headline": f"Master {d['service']} Today",
                "narration": f"High paying career banana chahte hain? {brand} laaya hai most in-demand skills ka complete practical program!",
            },
            {
                "id": 2,
                "search": "student studying classroom",
                "badge": "100% PRACTICAL",
                "headline": "Hands-on Live Projects",
                "narration": "Sirf theory nahi, real-world industry projects par kaam karke portfolio build karein!",
            },
            {
                "id": 3,
                "search": "developer working computer",
                "badge": "JOB ASSISTANCE",
                "headline": "Mentorship & Placement",
                "narration": "Top industry experts se 1-on-1 guidance aur complete placement support payein!",
            },
            {
                "id": 4,
                "search": "online learning success",
                "badge": "SPECIAL OFFER",
                "headline": f"{offer}",
                "narration": f"Exclusive offer: {offer}! Batch seats limited hain, abhi visit ya call karein!",
            },
        ]
    elif cat == "fashion":
        return [
            {
                "id": 1,
                "search": "fashion clothes boutique",
                "badge": "NEW ARRIVALS",
                "headline": f"Trendiest Fashion in {loc}",
                "narration": f"Kya aap dhoondh rahe hain latest trending styles aur premium collection {loc} mein?",
            },
            {
                "id": 2,
                "search": "shopping clothing store",
                "badge": "PREMIUM QUALITY",
                "headline": f"{brand} Exclusive Wear",
                "narration": f"{brand} par payein finest fabric, stylish designs aur perfect fitting har occasion ke liye!",
            },
            {
                "id": 3,
                "search": "fashion model smiling",
                "badge": "LOOK STUNNING",
                "headline": "Elegance & Comfort",
                "narration": "Apne style statement ko upgrade karein hamare bestselling collection ke sath!",
            },
            {
                "id": 4,
                "search": "shopping clothing store",
                "badge": "SEASONAL OFFER",
                "headline": f"{offer}",
                "narration": f"Special festive offer: {offer}! Aaj hi visit karein ya order place karein!",
            },
        ]
    else:
        return [
            {
                "id": 1,
                "search": "business meeting team",
                "badge": "BEST SERVICE",
                "headline": f"Looking For {d['service']}?",
                "narration": f"{loc} mein trusted aur professional {d['service']} dhoondh rahe hain? Aapka safar yahan shuru hota hai!",
            },
            {
                "id": 2,
                "search": "digital marketing charts analytics",
                "badge": "PROVEN EXPERTISE",
                "headline": f"{brand} Solutions",
                "narration": f"{brand} deta hai aapko reliable, fast aur highest quality service jo aapke expectations se aage ho!",
            },
            {
                "id": 3,
                "search": "office handshake deal",
                "badge": "CUSTOMER TRUST",
                "headline": "100% Satisfaction Guaranteed",
                "narration": "Hamaare satisfied customers hamare trust ka sabse bada proof hain. Quality me no compromise!",
            },
            {
                "id": 4,
                "search": "business success growth",
                "badge": "LIMITED DEAL",
                "headline": f"{offer}",
                "narration": f"Special limited time discount: {offer}! Aaj hi contact karein aur apna deal lock karein!",
            },
        ]

# ── ASYNC VOICE GENERATOR ──────────────────────────────────────────────
async def generate_voice(text: str, voice_id: str, out_file: Path):
    comm = edge_tts.Communicate(text, voice_id)
    await comm.save(str(out_file))

def probe_duration(path: Path) -> float:
    try:
        r = subprocess.run([FFMPEG, "-i", str(path)], stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        for line in r.stderr.splitlines():
            if "Duration:" in line:
                d = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = d.split(":")
                return max(3.0, float(h)*3600 + float(m)*60 + float(s) + 0.3)
    except Exception:
        pass
    return 5.0

# ── PIXABAY HD FOOTAGE DOWNLOADER ──────────────────────────────────────
def fetch_stock_clip(query: str, out_file: Path) -> bool:
    params = urllib.parse.urlencode({
        "key": PIXABAY_KEY,
        "q": query,
        "video_type": "film",
        "per_page": 8,
        "safesearch": "true",
        "order": "popular",
    })
    url = f"https://pixabay.com/api/videos/?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=12) as r:
            data = json.loads(r.read().decode())
        for hit in data.get("hits", []):
            for q in ["large", "medium", "small"]:
                clip_url = hit.get("videos", {}).get(q, {}).get("url")
                if clip_url:
                    r2 = urllib.request.Request(clip_url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(r2, timeout=30) as resp:
                        out_file.write_bytes(resp.read())
                    return out_file.exists() and out_file.stat().st_size > 5000
    except Exception as e:
        console.print(f"[yellow]Notice: Download query '{query}' ({e})[/]")
    return False

# ── PILLOW OVERLAY RENDERER ────────────────────────────────────────────
def build_scene_overlay(scene: dict, d: dict, out_png: Path):
    """Draws a 1080x1920 transparent PNG overlay with high-converting graphics."""
    W, H = 1080, 1920
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_brand = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 44)
    font_sub   = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 26)
    font_badge = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 26)
    font_head  = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 42)
    font_body  = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 34)
    font_offer = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 30)

    # 1. Top Brand Header Card
    brand_text = f"[AD] {d['brand'].upper()}"
    info_text  = f"LOCATION: {d['location'].upper()}  |  CALL: {d['phone']}"
    draw.rounded_rectangle([(40, 50), (1040, 185)], radius=20, fill=(10, 15, 28, 225), outline=(56, 189, 248, 255), width=3)
    draw.text((70, 72), brand_text, fill=(56, 189, 248, 255), font=font_brand)
    draw.text((72, 134), info_text, fill=(226, 232, 240, 240), font=font_sub)

    # 2. Dynamic Center Badge
    badge_txt = f"* {scene['badge']} *"
    bbox = draw.textbbox((0, 0), badge_txt, font=font_badge)
    bw = bbox[2] - bbox[0]
    draw.rounded_rectangle([((W - bw)//2 - 25, 1220), ((W + bw)//2 + 25, 1275)], radius=15, fill=(245, 158, 11, 255))
    draw.text(((W - bw)//2, 1232), badge_txt, fill=(0, 0, 0, 255), font=font_badge)

    # 3. Caption Box
    lines = textwrap.fill(scene["narration"], width=32).splitlines()
    box_h = 90 + len(lines) * 46
    draw.rounded_rectangle([(50, 1290), (1030, 1290 + box_h)], radius=25, fill=(8, 12, 22, 230), outline=(250, 204, 21, 230), width=3)
    draw.text((80, 1315), scene["headline"].upper(), fill=(250, 204, 21, 255), font=font_head)
    y_text = 1375
    for l in lines:
        draw.text((80, y_text), l, fill=(255, 255, 255, 255), font=font_body)
        y_text += 46

    # 4. Bottom Offer Card
    draw.rounded_rectangle([(40, 1690), (1040, 1860)], radius=20, fill=(15, 23, 42, 235), outline=(52, 211, 153, 245), width=3)
    draw.text((75, 1720), f"🔥 {d['offer'].upper()}", fill=(250, 204, 21, 255), font=font_offer)
    draw.text((75, 1785), f"CALL NOW: {d['phone']}  |  DOORSTEP SERVICE", fill=(255, 255, 255, 255), font=font_badge)

    img.save(str(out_png), "PNG")

# ── COMPILATION PIPELINE ───────────────────────────────────────────────
def compile_video(d: dict, scenes: list):
    step(2, "Generating Video Assets & Rendering", "⚙️")

    slug = re.sub(r"[^a-zA-Z0-9]+", "_", d["brand"].lower()).strip("_")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    work_dir = OUTPUT_BASE / f"temp_{slug}_{ts}"
    work_dir.mkdir(parents=True, exist_ok=True)

    rendered_clips = []
    total_dur = 0.0

    for idx, s in enumerate(scenes, 1):
        console.print(f"[bold yellow]Scene {idx}/{len(scenes)}: '{s['headline']}'[/]")

        # 1. Voice
        audio_file = work_dir / f"voice_{idx}.mp3"
        console.print(f"  🎙️ Generating studio voice ({d['voice_name']})...")
        asyncio.run(generate_voice(s["narration"], d["voice_id"], audio_file))
        actual_dur = probe_duration(audio_file)
        total_dur += actual_dur

        # 2. Matching footage
        raw_clip = work_dir / f"raw_stock_{idx}.mp4"
        console.print(f"  🔍 Sourcing real footage matching '{s['search']}'...")
        got_clip = fetch_stock_clip(s["search"], raw_clip)

        # 3. Transparent Overlay
        overlay_png = work_dir / f"overlay_{idx}.png"
        build_scene_overlay(s, d, overlay_png)

        # 4. Render 9:16 Scene MP4
        scene_mp4 = work_dir / f"scene_{idx}_rendered.mp4"
        if got_clip and raw_clip.exists() and raw_clip.stat().st_size > 5000:
            console.print(f"  ✓ Real footage downloaded ({raw_clip.stat().st_size // 1024} KB)")
            cmd = [
                FFMPEG, "-y",
                "-stream_loop", "-1", "-i", str(raw_clip),
                "-i", str(overlay_png),
                "-i", str(audio_file),
                "-filter_complex", (
                    "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[bg];"
                    "[bg][1:v]overlay=0:0[vout]"
                ),
                "-map", "[vout]",
                "-map", "2:a",
                "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                "-c:a", "aac", "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-t", f"{actual_dur:.2f}",
                str(scene_mp4),
            ]
        else:
            console.print("  ℹ Using ambient background fallback")
            cmd = [
                FFMPEG, "-y",
                "-f", "lavfi", "-i", "color=c=0x111827:s=1080x1920:r=30",
                "-i", str(overlay_png),
                "-i", str(audio_file),
                "-filter_complex", "[0:v][1:v]overlay=0:0[vout]",
                "-map", "[vout]",
                "-map", "2:a",
                "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-t", f"{actual_dur:.2f}",
                str(scene_mp4),
            ]

        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        if scene_mp4.exists():
            rendered_clips.append(scene_mp4)
            console.print(f"  ✓ Scene {idx} rendered successfully ({actual_dur:.1f}s)")
        console.print()

    # Step 3: Stitching
    step(3, "Assembling Full Commercial Reel", "🎬")
    concat_txt = work_dir / "scenes_concat.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for c in rendered_clips:
            clean_p = str(c.resolve()).replace("\\", "/")
            f.write(f"file '{clean_p}'\n")

    final_ad = OUTPUT_BASE / f"{slug}_commercial_{ts}.mp4"
    cmd_stitch = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_txt),
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(final_ad),
    ]
    subprocess.run(cmd_stitch, check=True)

    if final_ad.exists() and final_ad.stat().st_size > 1000:
        size_mb = final_ad.stat().st_size / (1024 * 1024)
        console.print()
        console.print(Panel(Align.center(Text.from_markup(
            "[bold bright_green]🎉🎉  YOUR COMMERCIAL IS READY!  🎉🎉[/]\n\n"
            f"[bold white]{final_ad.name}[/]\n"
            f"[dim]Format: 1080x1920 (9:16 Vertical)  •  Size: {size_mb:.1f} MB  •  Duration: {total_dur:.1f}s[/]\n\n"
            f"[cyan]{final_ad}[/]"
        )), border_style="bright_green", padding=(1, 4)))

        # Launch video
        try:
            os.startfile(str(final_ad))
            console.print("[green]✓ Video player automatically opened![/]")
        except Exception:
            subprocess.Popen(["cmd", "/c", "start", "", str(final_ad)])

        try:
            subprocess.Popen(["explorer", str(OUTPUT_BASE)])
        except Exception:
            pass
        return final_ad
    else:
        console.print("[red]Video assembly failed.[/]")
        return None

# ── MAIN CLI ──────────────────────────────────────────────────────────
def main():
    show_banner()
    d = ask_user()

    # Summary Panel
    console.print()
    console.print(Panel(
        f"[bold white]🏢 Brand:[/]    [cyan]{d['brand']}[/]\n"
        f"[bold white]🎯 Service:[/]  {d['service']}\n"
        f"[bold white]📍 Location:[/] {d['location']}\n"
        f"[bold white]⚡ Offer:[/]    [yellow]{d['offer']}[/]\n"
        f"[bold white]📞 Contact:[/]  {d['phone']}\n"
        f"[bold white]🎙️ Voice:[/]    {d['voice_name']}",
        title="[bold green]✓ Ad Configuration[/]",
        border_style="green",
    ))
    console.print()

    # Generate Scenes
    scenes = generate_matched_storyboard(d)

    table = Table(title="📋 Generated Scene Storyboard (Visuals Matched to Narration)", border_style="cyan")
    table.add_column("#", style="bold yellow", width=4)
    table.add_column("Badge", style="cyan", width=18)
    table.add_column("Headline", style="bold white", width=25)
    table.add_column("Visual Stock Query", style="magenta", width=22)
    table.add_column("Narration (Voiceover)", style="green")

    for s in scenes:
        table.add_row(str(s["id"]), s["badge"], s["headline"], s["search"], s["narration"])

    console.print(table)
    console.print()

    confirm = questionary.confirm(
        "🚀 9:16 Matched Commercial generation shuru karein?",
        default=True,
        style=custom_style,
    ).ask()

    if not confirm:
        console.print("[yellow]Generation cancelled.[/]")
        return

    compile_video(d, scenes)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Program stopped by user.[/]")
        sys.exit(0)
