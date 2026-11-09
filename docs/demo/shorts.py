#!/usr/bin/env python3
"""YouTube Shorts cut from the voiced videos: vertical, captioned, with a hook and an end card.

    python3 docs/demo/shorts.py            # every short in SHORTS
    python3 docs/demo/shorts.py green      # one of them

Each short is a run of whole scenes (scenes start and end on a pause, so cuts are clean),
written to docs/shorts/<name>.mp4. Most Shorts are watched muted, so the words are on
screen: the scenes' own narration, timed from captions.py.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import captions  # noqa: E402

DOCS = Path(__file__).resolve().parent.parent
OUT = DOCS / "shorts"
W, H = 1080, 1920
VIDEO_Y = 640                       # where the 16:9 picture sits
END = 2.5                           # seconds of end card after the last line
FONTS = "/System/Library/Fonts/Supplemental/"
INK, ACCENT, BG = (232, 238, 247), (255, 196, 61), (11, 18, 28)

SHORTS = {
    "green": {
        "from": "visual-demo", "scenes": [[23, 25]],
        "hook": "My AI checker passed this.\nLook closer.",
        "title": "Every Box Green, Still Wrong: AI Visual Verification #shorts",
    },
    "planted": {
        "from": "visual-demo", "scenes": [[9, 14]],
        "hook": "I planted 6 bugs to test\nmy AI's checker.",
        "title": "I Planted 6 Bugs to Test My AI Code Checker #shorts",
    },
    "receipt": {
        "from": "engineers-demo", "scenes": [[23, 24], [27, 27]],
        "hook": "AI agents built this feature.\nHere's the receipt.",
        "title": "17 Minutes, About $1.24: An AI Software Factory's Receipt #shorts",
    },
}


def font(name, size):
    return ImageFont.truetype(FONTS + name, size)


def wrap(draw, text, face, width):
    lines = []
    for paragraph in text.split("\n"):
        line = ""
        for word in paragraph.split():
            trial = (line + " " + word).strip()
            if draw.textlength(trial, font=face) <= width:
                line = trial
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


def text_png(path, text, face, colour, box=None, width=960, align_top=0):
    """Centred text on a transparent 1080-wide strip, optionally on a rounded box."""
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    lines = wrap(probe, text, face, width)
    step = int(face.size * 1.22)
    height = step * len(lines) + 48
    image = Image.new("RGBA", (W, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    if box:
        widest = max(draw.textlength(l, font=face) for l in lines)
        draw.rounded_rectangle([(W - widest) / 2 - 28, 4, (W + widest) / 2 + 28, height - 4], radius=24, fill=box)
    for i, line in enumerate(lines):
        draw.text((W / 2, 24 + i * step), line, font=face, fill=colour, anchor="ma")
    image.save(path)
    return height


def windows(story, ranges):
    """(start, end) in the source video for each run of scenes."""
    starts, t = [], 0.0
    for scene in story["scenes"]:
        starts.append(t)
        t += scene["seconds"]
    starts.append(t)
    return [(starts[a - 1], starts[b]) for a, b in ranges]


def build(name, spec):
    import json
    folder = DOCS / spec["from"]
    story = json.loads((folder / "story.json").read_text())
    spans = windows(story, spec["scenes"])
    cues, offset = [], 0.0
    for a, b in spans:
        for start, end, text in captions.timeline(folder):
            if start >= a - 0.01 and end <= b + 0.01:
                cues.append((start - a + offset, end - a + offset, text))
        offset += b - a
    length = offset
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        text_png(tmp / "hook.png", spec["hook"], font("Arial Black.ttf", 56), INK, width=1000)
        text_png(tmp / "end.png", "Full video on the channel:\nSoftware Factories with Claude Code",
                 font("Arial Bold.ttf", 52), BG, box=ACCENT + (255,))
        for i, (_, _, text) in enumerate(cues):
            text_png(tmp / "c{}.png".format(i), text, font("Arial Bold.ttf", 54), INK, box=(0, 0, 0, 170), width=940)
        inputs = ["-i", str(folder / story["video"].replace(".mp4", "-voiced.mp4"))]
        graph = []
        # The runs of scenes, joined.
        for i, (a, b) in enumerate(spans):
            graph.append("[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}];[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS[a{i}]".format(a=a, b=b, i=i))
        graph.append("".join("[v{0}][a{0}]".format(i) for i in range(len(spans))) +
                     "concat=n={}:v=1:a=1[vc][ac]".format(len(spans)))
        # Vertical: the picture on a blurred, darkened copy of itself, held still for the end card.
        graph.append("[vc]tpad=stop_mode=clone:stop_duration={e},split[x][y];"
                     "[x]scale=-2:{h},crop={w}:{h},gblur=sigma=40,eq=brightness=-0.25[bgd];"
                     "[y]scale={w}:-2[fg];[bgd][fg]overlay=0:{vy}[base]".format(e=END, w=W, h=H, vy=VIDEO_Y))
        layers = [("hook.png", "(W-w)/2", "150", None),
                  ("end.png", "(W-w)/2", "(H-h)/2", (length + 0.2, length + END))]
        layers += [("c{}.png".format(i), "(W-w)/2", str(VIDEO_Y + 640), (a, b)) for i, (a, b, _) in enumerate(cues)]
        last = "base"
        for n, (png, x, y, when) in enumerate(layers):
            inputs += ["-i", str(tmp / png)]
            enable = ":enable='between(t,{:.3f},{:.3f})'".format(*when) if when else ""
            graph.append("[{last}][{i}:v]overlay={x}:{y}{en}[l{n}]".format(last=last, i=n + 1, x=x, y=y, en=enable, n=n))
            last = "l{}".format(n)
        graph.append("[ac]apad=pad_dur={}[aout]".format(END))
        OUT.mkdir(exist_ok=True)
        out = OUT / (name + ".mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(graph),
                        "-map", "[" + last + "]", "-map", "[aout]", "-r", "30", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-crf", "20", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out)], check=True)
    print("{}  {:.0f}s  {} captions".format(out.relative_to(DOCS.parent), length + END, len(cues)))


def main():
    names = sys.argv[1:] or list(SHORTS)
    for name in names:
        build(name, SHORTS[name])


if __name__ == "__main__":
    main()
