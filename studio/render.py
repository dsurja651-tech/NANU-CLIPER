"""Turns a time range into a vertical clip: 9:16 layout, bouncy word captions, hook title, cover."""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from . import config, roman
from .media import NO_WINDOW, run

W, H = config.OUT_W, config.OUT_H

# ASS colours are &HBBGGRR. `size` is the ASS font size (line height); _Font turns it into real pixels.
STYLES = {
    "opus": {"label": "Opus Clip (Neon)", "font": "Poppins ExtraBold", "size": 136, "base": "FFFFFF", "active": "00FF66",
             "strong": "00FFFF", "outline": 8, "pop": 120, "upper": True, "per": 3},
    "glow": {"label": "Neon Glow (Viral)", "font": "Poppins ExtraBold", "size": 138, "base": "FFFFFF", "active": "00FFFF",
             "strong": "FF00FF", "outline": 9, "glow": True, "pop": 124, "upper": True, "per": 2},
    "beast": {"label": "MrBeast (Viral)", "font": "Archivo Black", "size": 138, "base": "FFFFFF", "active": "00F0FF",
              "strong": "00FFFF", "outline": 9, "pop": 125, "upper": True, "per": 2},
    "gaming": {"label": "Gaming (Arcade)", "font": "Anton", "size": 150, "base": "FFFFFF", "active": "3C3CFF",
               "strong": "00FFFF", "outline": 8, "pop": 120, "upper": True, "per": 2},
    "bounce": {"label": "Bounce", "font": "Poppins ExtraBold", "size": 132, "base": "FFFFFF", "active": "00F0FF",
               "strong": "FFFFFF", "outline": 7, "pop": 112, "upper": True, "per": 3},
    "hype": {"label": "Hype", "font": "Anton", "size": 152, "base": "FFFFFF", "active": "3C3CFF",
             "strong": "00D7FF", "outline": 7, "pop": 114, "upper": True, "per": 2},
    "clean": {"label": "Clean", "font": "Poppins ExtraBold", "size": 100, "base": "FFFFFF", "active": "6BD7FF",
              "strong": "FFFFFF", "outline": 5, "pop": 106, "upper": False, "per": 4},
}
HOOK = {"font": "Poppins ExtraBold", "size": 96, "ink": "14100E", "box": "FFFFFF", "pad_x": 36, "pad_y": 22, "radius": 26,
        "max_w": 900}
FONT_FILES = {"Poppins ExtraBold": "Poppins-ExtraBold.ttf", "Anton": "Anton-Regular.ttf", "Archivo Black": "ArchivoBlack-Regular.ttf"}
CAP_MAX_W = 960   # captions never run wider than this, whatever is said


class _Font:
    """Measures text exactly as the renderer will draw it, so every word can be placed by hand: the highlighted
    word can grow without pushing its neighbours, and the heading box fits its text."""
    _cache: dict = {}

    def __init__(self, name):
        import struct
        path = Path(__file__).resolve().parent / "fonts" / FONT_FILES.get(name, FONT_FILES["Poppins ExtraBold"])
        d = path.read_bytes()
        tables = {}
        for i in range(struct.unpack(">H", d[4:6])[0]):
            tag, _, off, _ = struct.unpack(">4sIII", d[12 + 16 * i: 28 + 16 * i])
            tables[tag] = off
        self.upm = struct.unpack(">H", d[tables[b"head"] + 18: tables[b"head"] + 20])[0]
        o = tables[b"OS/2"]
        self.asc, self.desc = struct.unpack(">HH", d[o + 74: o + 78])      # what the renderer sizes the font by
        self.cap = struct.unpack(">h", d[o + 88: o + 90])[0] or int(self.upm * 0.7)
        self.path = str(path)
        self._pil = {}

    @classmethod
    def get(cls, name):
        if name not in cls._cache:
            cls._cache[name] = cls(name)
        return cls._cache[name]

    def em(self, size):
        return size * self.upm / (self.asc + self.desc)

    def width(self, text, size):
        """Pixels wide at this ASS size."""
        try:
            from PIL import ImageFont
            if "f" not in self._pil:
                self._pil["f"] = ImageFont.truetype(self.path, 200)
            return self._pil["f"].getlength(text) * self.em(size) / 200
        except Exception:  # noqa: BLE001 - no measuring library: a fair estimate keeps clips rendering
            return len(text) * self.em(size) * 0.62

    def cap_shift(self, size):
        """How far below the anchor the middle of a capital letter sits when text is centred on a point."""
        return ((self.asc - self.desc) / 2 - self.cap / 2) * size / (self.asc + self.desc)


CAPTION_LEAD = 0.08  # 80ms acoustic lead for exact voice-synchronized caption onset
def install_fonts():
    """Copy the bundled caption fonts next to the data, so captions look the same on every machine and server."""
    src = Path(__file__).resolve().parent / "fonts"
    for f in src.glob("*.ttf"):
        if not (config.FONTS_DIR / f.name).exists():
            shutil.copyfile(f, config.FONTS_DIR / f.name)


LAYOUTS = {"blur": "Full frame + blurred fill", "zoom": "Zoomed in + blurred fill", "crop": "Fill the screen (centre crop)",
           "gameplay": "Gameplay fills the screen, facecam in the corner",
           "split": "Facecam on top, gameplay below, captions in between"}


def _ts(t):
    t = max(0.0, t)
    h, m = int(t // 3600), int(t % 3600 // 60)
    return f"{h}:{m:02d}:{t % 60:05.2f}"


def _clean(text):
    return re.sub(r"[\x00-\x1f\x7f]+", " ", re.sub(r"[{}\\]", "", str(text))).strip()


def _key(word):
    return re.sub(r"[^a-z0-9']", "", word.lower())


def _groups(words, per):
    out, cur = [], []
    for w in words:
        if cur and (len(cur) >= per or sum(len(x["w"]) for x in cur) + len(w["w"]) > 16
                    or w["s"] - cur[-1]["e"] > 0.45 or cur[-1]["w"][-1:] in ".?!"):
            out.append(cur)
            cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    return out


def geometry(src_w, src_h, layout):
    """Where the video sits in the 1080x1920 frame, and where hook and captions go."""
    if src_h >= src_w and layout not in ("crop", "split"):
        layout = "crop"  # already vertical or square: nothing to gain from a blurred fill
    if layout == "blur":
        fg_h = min(H, int(round(W * src_h / src_w / 2)) * 2)
    elif layout == "zoom":
        fg_h = 1000
    elif layout == "split":
        fg_h = 960
    else:
        fg_h = H
    top = (H - fg_h) // 2
    if layout == "split":
        # Facecam on top (0-960), Gameplay on bottom (960-1920).
        # Word-by-word captions positioned right in between at seam (960), hook title at top (130).
        return layout, fg_h, 130, 960
    if layout in ("crop", "gameplay"):
        return layout, fg_h, 300, 1380
    return layout, fg_h, max(230, top - 190), min(1640, top + fg_h + 180)


def _hook_events(hook, dur, y):
    """The heading: dark text in a white rounded box that fits it, on one line or two balanced ones."""
    f, size = _Font.get(HOOK["font"]), HOOK["size"]
    words = hook.split()
    if not words:
        return []
    lines = [" ".join(words)]
    if f.width(lines[0], size) > HOOK["max_w"] and len(words) > 1:      # two lines, split where they come out most even
        cut = min(range(1, len(words)), key=lambda i: max(f.width(" ".join(words[:i]), size), f.width(" ".join(words[i:]), size)))
        lines = [" ".join(words[:cut]), " ".join(words[cut:])]
    widest = max(f.width(l, size) for l in lines)
    if widest > HOOK["max_w"]:
        size = max(40, int(size * HOOK["max_w"] / widest))
        widest = max(f.width(l, size) for l in lines)
    line_h = f.em(size) * 1.16
    bw, bh = widest + 2 * HOOK["pad_x"], line_h * len(lines) + 2 * HOOK["pad_y"]
    x0, y0, r = (W - bw) / 2, y - bh / 2, min(HOOK["radius"], bh / 2)
    x1, y1 = x0 + bw, y0 + bh
    n = lambda v: f"{v:.0f}"                                                         # noqa: E731
    box = (f"m {n(x0 + r)} {n(y0)} l {n(x1 - r)} {n(y0)} b {n(x1)} {n(y0)} {n(x1)} {n(y0)} {n(x1)} {n(y0 + r)} "
           f"l {n(x1)} {n(y1 - r)} b {n(x1)} {n(y1)} {n(x1)} {n(y1)} {n(x1 - r)} {n(y1)} "
           f"l {n(x0 + r)} {n(y1)} b {n(x0)} {n(y1)} {n(x0)} {n(y1)} {n(x0)} {n(y1 - r)} "
           f"l {n(x0)} {n(y0 + r)} b {n(x0)} {n(y0)} {n(x0)} {n(y0)} {n(x0 + r)} {n(y0)}")
    span = f"{_ts(0)},{_ts(dur)}"
    ev = [f"Dialogue: 3,{span},Hook,,0,0,0,,{{\\an7\\pos(0,0)\\fad(160,0)\\c&H{HOOK['box']}&\\p1}}{box}{{\\p0}}"]
    for i, line in enumerate(lines):
        cy = y - line_h * (len(lines) - 1) / 2 + i * line_h - f.cap_shift(size)
        ev.append(f"Dialogue: 4,{span},Hook,,0,0,0,,{{\\an5\\pos({W // 2},{cy:.0f})\\fad(160,0)\\fs{size}}}{line}")
    return ev


def build_ass(words, start, end, hook, style_name, highlight, hook_y, cap_y) -> str:
    st = STYLES.get(style_name, STYLES["opus"])
    words = [dict(w, s=w["s"] - CAPTION_LEAD, e=w["e"] - CAPTION_LEAD) for w in words]
    strong = {_key(h) for h in highlight if _key(h)}
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{st['font']},{st['size']},&H00{st['base']},&H00{st['base']},&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,{st['outline']},0,5,0,0,0,1
Style: Hook,{HOOK['font']},{HOOK['size']},&H00{HOOK['ink']},&H00{HOOK['ink']},&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    dur = end - start
    ev = _hook_events(_clean(hook), dur, hook_y)
    f = _Font.get(st["font"])
    inside = [dict(w, w=_clean(w["w"])) for w in words if w["s"] >= start - 0.05 and w["s"] < end]
    inside = sorted((w for w in inside if w["w"]), key=lambda w: w["s"])
    for i, w in enumerate(inside[:-1]):
        # Keep word end strictly bound to speech; do not stretch into silent pauses
        w["e"] = max(w["s"] + 0.06, min(w["e"], inside[i + 1]["s"]))
    groups = _groups(inside, st["per"])
    for gi, g in enumerate(groups):
        g_start = max(0.0, g[0]["s"] - start)
        # End precisely when last word finishes, without lingering in silence
        g_end = max(g_start + 0.1, g[-1]["e"] - start + 0.04)
        if g_end - g_start < 0.02:
            continue
        texts = []
        for x in g:
            t = re.sub(r"[.,;:]+$", "", x["w"])
            texts.append(t.upper() if st["upper"] else t)
        if not all(roman.drawable(t) for t in texts):
            line = " ".join(texts)
            fs = max(44, min(int(st["size"] * 0.7), int(1500 / max(1, len(line)) * 1.6)))
            ev.append(f"Dialogue: 1,{_ts(g_start)},{_ts(g_end)},Cap,,60,60,0,,{{\\an5\\pos({W // 2},{cap_y:.0f})\\q0\\fs{fs}}}{line}")
            continue
        size = st["size"]
        gap = f.width("n n", size) - 2 * f.width("n", size) + (2 * st["outline"] + 6) * size / st["size"]
        total = sum(f.width(t, size) for t in texts) + gap * (len(texts) - 1)
        if total > CAP_MAX_W:
            size = max(36, int(size * CAP_MAX_W / total))
            gap = f.width("n n", size) - 2 * f.width("n", size) + (2 * st["outline"] + 6) * size / st["size"]
            total = sum(f.width(t, size) for t in texts) + gap * (len(texts) - 1)
        cy = cap_y - f.cap_shift(size)
        x = (W - total) / 2
        p = st["pop"]
        for i, (w, t) in enumerate(zip(g, texts)):
            wd = f.width(t, size)
            p = max(104, min(st["pop"], 100 + int(2200 / max(wd, 1))))
            pos = f"\\an5\\pos({x + wd / 2:.0f},{cy:.0f})\\fs{size}"
            x += wd + gap
            # Speech-synchronized timing: starts when word begins, ends when word is spoken
            a = max(g_start, w["s"] - start)
            b = max(a + 0.06, min(w["e"] - start, g_end))
            base = st["strong"] if _key(w["w"]) in strong else st["base"]
            # Active spoken word with vibrant pop & glow
            if b - a >= 0.02:
                if st.get("glow"):
                    ev.append(f"Dialogue: 1,{_ts(a)},{_ts(b)},Cap,,0,0,0,,{{{pos}\\c&H{st['active']}&\\3c&H00FF00FF&\\blur7\\fscx{p + 2}\\fscy{p + 2}}}{t}")
                ev.append(f"Dialogue: 2,{_ts(a)},{_ts(b)},Cap,,0,0,0,,{{{pos}\\c&H{st['active']}&\\fscx95\\fscy95"
                          f"\\t(0,80,\\fscx{p}\\fscy{p})\\t(80,180,\\fscx{p - 4}\\fscy{p - 4})}}{t}")
            # Said word remains in base color only until the current phrase ends
            if g_end - b >= 0.02:
                ev.append(f"Dialogue: 1,{_ts(b)},{_ts(g_end)},Cap,,0,0,0,,{{{pos}\\c&H{base}&\\fscx100\\fscy100}}{t}")
    return head + "\n".join(ev) + "\n"


PIP_W = 380            # how wide the facecam is in the 1080-wide frame
PIP_MARGIN = 26


def _filter(layout, fg_h, facecam=None, src_w=1920, src_h=1080):
    if layout == "split":
        # Top panel: ONLY Facecam (1080x960) - zoomed tightly on the face with ZERO gameplay!
        # Bottom panel: ONLY Gameplay (1080x960) - completely cutting out the facecam!
        # Middle: Captions placed at y=960 seam
        if facecam and len(facecam) == 4:
            fx, fy, fw, fh = (int(v) for v in facecam)
            if fw > 8 and fh > 8:
                cx = fx + fw / 2
                cy = fy + fh / 2
                # Tight zoom directly on the webcam so the face is large and prominent with 0% game leak
                crop_h = min(src_h, max(int(fh * 1.12), int(fw * 1.12 * 960 / 1080)))
                crop_w = int(round(crop_h * 1080 / 960))
                if crop_w > src_w:
                    crop_w = src_w
                    crop_h = int(round(crop_w * 960 / 1080))
                top_x = max(0, min(src_w - crop_w, int(round(cx - crop_w / 2))))
                top_y = max(0, min(src_h - crop_h, int(round(cy - crop_h / 2))))

                gw = min(src_w, int(round(src_h * 1080 / 960)))
                gh = src_h
                if cx >= src_w / 2:
                    gx = 0  # Face is on right -> crop gameplay from far left (zero facecam in gameplay)
                else:
                    gx = max(0, src_w - gw)  # Face is on left -> crop gameplay from far right (zero facecam in gameplay)

                fc_filter = f"[fc]crop={crop_w}:{crop_h}:{top_x}:{top_y},scale={W}:960:force_original_aspect_ratio=increase,crop={W}:960,setsar=1[top];"
                game_filter = f"[base]crop={gw}:{gh}:{gx}:0,scale={W}:960:force_original_aspect_ratio=increase,crop={W}:960,setsar=1[bot];"
                return f"[0:v]fps={config.OUT_FPS},split=2[base][fc];{fc_filter}{game_filter}[top][bot]vstack=inputs=2[v0];"
        return (f"[0:v]fps={config.OUT_FPS},split=2[t_raw][b_raw];"
                f"[t_raw]scale={W}:960:force_original_aspect_ratio=increase,crop={W}:960:0:0,setsar=1[top];"
                f"[b_raw]scale={W}:960:force_original_aspect_ratio=increase,crop={W}:960:(in_w-out_w)/2:in_h-960,setsar=1[bot];"
                f"[top][bot]vstack=inputs=2[v0];")
    if layout == "gameplay" and facecam:
        # The game fills the screen, and the webcam sits in the top corner of it, so a viewer sees
        # the play and the face at the same time.
        fx, fy, fw, fh = (int(v) for v in facecam)
        if fw > 8 and fh > 8:
            pip_h = max(2, int(round(PIP_W * fh / fw)))
            return (f"[0:v]fps={config.OUT_FPS},split=2[base][fc];"
                    f"[base]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1[b];"
                    f"[fc]crop={fw}:{fh}:{fx}:{fy},scale={PIP_W}:{pip_h},setsar=1[p];"
                    f"[b][p]overlay={W - PIP_W - PIP_MARGIN}:{PIP_MARGIN}[v0];")
    if layout == "crop" or (layout == "gameplay" and not facecam):
        return f"[0:v]fps={config.OUT_FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1[v0];"
    return (f"[0:v]fps={config.OUT_FPS},split=2[a][b];"
            f"[a]scale=270:480:force_original_aspect_ratio=increase,crop=270:480,boxblur=6:2,"
            f"scale={W}:{H},eq=brightness=-0.14:saturation=1.15[bg];"
            f"[b]scale={W}:{fg_h}:force_original_aspect_ratio=increase,crop={W}:{fg_h}[fg];"
            f"[bg][fg]overlay=0:(H-h)/2,setsar=1[v0];")


def _hook_y(layout, hook_y, facecam=None):
    if layout == "split":
        return 130
    if layout == "gameplay" and facecam and len(facecam) == 4 and facecam[2] > 8:
        return PIP_MARGIN + int(round(PIP_W * facecam[3] / facecam[2])) + 32
    return hook_y


_nvenc_ok = None
_qsv_ok = None
RENDER_SECONDS = 600      # one clip's video encode; far beyond normal, so a frozen encoder is stopped, not waited on


def render_clip(src: Path, out_dir: Path, name: str, clip: dict, words: list, src_w: int, src_h: int) -> dict:
    """Writes <name>.mp4, <name>.jpg and <name>.ass into out_dir. Returns file names."""
    out_dir.mkdir(parents=True, exist_ok=True)
    start, end = clip["start"], clip["end"]
    layout, fg_h, hook_y, cap_y = geometry(src_w, src_h, clip.get("layout", "blur"))
    face = clip.get("facecam")
    if (layout in ("split", "gameplay")) and not (face and len(face) == 4):
        try:
            from . import facecam as fc_mod
            face = fc_mod.detect_face_box(src)
            if not face:
                b = fc_mod.detect(src)
                if b and b.get("conf") == "high":
                    face = [b["x"], b["y"], b["w"], b["h"]]
            if face:
                clip["facecam"] = face
        except Exception:
            pass
    if layout == "gameplay" and not (face and len(face) == 4):
        layout = "crop"     # no webcam found: the game fills the screen, which is still the right shape
    hook_y = _hook_y(layout, hook_y, face)
    ass = build_ass(words if clip.get("captions", True) else [], start, end, clip.get("hook", ""), clip.get("style", "opus"),
                    clip.get("highlight_words", []), hook_y, cap_y)
    # The clip is made in a short work folder and moved into place afterwards. The caption step of ffmpeg cannot
    # open files whose full path is longer than 260 characters on Windows, which a data folder deep inside other
    # folders easily reaches. Inside the work folder every name is short and relative (a drive colon would also
    # break the filter syntax).
    work = Path(tempfile.mkdtemp(prefix="pk"))
    try:
        return _render_in(work, src, out_dir, name, start, end, layout, fg_h, ass, face=face, src_w=src_w, src_h=src_h)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _render_in(work: Path, src: Path, out_dir: Path, name: str, start, end, layout, fg_h, ass: str, face=None, src_w=1920, src_h=1080) -> dict:
    global _nvenc_ok, _qsv_ok
    (work / f"{name}.ass").write_text(ass, encoding="utf-8")
    (work / "f").mkdir()
    for f in config.FONTS_DIR.glob("*.ttf"):
        shutil.copyfile(f, work / "f" / f.name)
    fc = _filter(layout, fg_h, face, src_w=src_w, src_h=src_h) + f"[v0]ass={name}.ass:fontsdir=f[v]"
    meta_tags = [
        "-metadata", f"title={name}",
        "-metadata", "artist=Nanu Panda",
        "-metadata", "author=Nanu Panda (@dsurja651-tech)",
        "-metadata", "composer=Nanu Panda (@NANU-PANDA)",
        "-metadata", "copyright=Copyright (c) 2026 Nanu Panda. All rights reserved.",
        "-metadata", "comment=Created with NanuCut Clipper Engine • Architect: Nanu Panda (https://github.com/dsurja651-tech/NANU-CLIPER)",
        "-metadata", "encoded_by=NanuCut Clipper Core Engine (Nanu Panda)",
        "-metadata", "nanu_signature=NANU-PANDA-IMMUTABLE-ARCHITECT-2026"
    ]
    base = ["ffmpeg", "-y", "-v", "error", "-threads", "0", "-ss", f"{start:.2f}", "-t", f"{end - start:.2f}", "-i", str(src),
            "-filter_complex", fc, "-map", "[v]", "-map", "0:a:0", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
            "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-movflags", "+faststart"] + meta_tags + ["-pix_fmt"]
    encoders = []
    if _nvenc_ok is not False:
        # Superfast NVENC Hardware Encoder (Preset p2 + low latency, 500+ FPS)
        encoders.append(("nvenc", ["yuv420p", "-c:v", "h264_nvenc", "-preset", "p2", "-tune", "ull", "-cq", "22", "-b:v", "0"]))
    if _qsv_ok is not False:
        encoders.append(("qsv", ["nv12", "-c:v", "h264_qsv", "-global_quality", "23", "-preset", "veryfast"]))
    encoders.append(("x264", ["yuv420p", "-c:v", "libx264", "-crf", "21", "-preset", "ultrafast", "-threads", "0"]))
    err = None
    for label, enc in encoders:
        p = subprocess.run(base + enc + [f"{name}.mp4"], cwd=work, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", creationflags=NO_WINDOW, timeout=RENDER_SECONDS)
        if p.returncode == 0:
            if label == "nvenc":
                _nvenc_ok = True
            elif label == "qsv":
                _qsv_ok = True
            break
        err = p.stderr[-1200:]
        if label == "nvenc":
            _nvenc_ok = False
        elif label == "qsv":
            _qsv_ok = False
    else:
        raise RuntimeError(f"Render failed: {err}")
    cover_t = min(1.2, (end - start) / 2)
    run(["ffmpeg", "-y", "-v", "error", "-ss", f"{cover_t:.2f}", "-i", f"{name}.mp4", "-frames:v", "1",
         "-q:v", "3", f"{name}.jpg"], cwd=work)
    for ext in ("mp4", "jpg", "ass"):
        shutil.move(str(work / f"{name}.{ext}"), str(out_dir / f"{name}.{ext}"))
    return {"file": f"{name}.mp4", "cover": f"{name}.jpg", "layout": layout}
