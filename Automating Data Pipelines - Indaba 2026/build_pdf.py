"""
build_pdf.py — renders Workshop_Slide_Deck.md in the reference PPTX style:
dark background, amber/green/purple chips, ghost section numbers, → bullets.
Run: python3 build_pdf.py
"""

import re
from pathlib import Path
from fpdf import FPDF
from fpdf.enums import XPos, YPos

# ---------------------------------------------------------------------------
# Font paths (macOS system Arial)
# ---------------------------------------------------------------------------
_SYS = Path("/System/Library/Fonts/Supplemental")
FONT_R  = _SYS / "Arial.ttf"
FONT_B  = _SYS / "Arial Bold.ttf"
FONT_I  = _SYS / "Arial Italic.ttf"
FONT_BI = _SYS / "Arial Bold Italic.ttf"
FONT_UNI = Path("/Library/Fonts/Arial Unicode.ttf")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HERE     = Path(__file__).parent
MD_PATH  = HERE / "Workshop_Slide_Deck.md"
PDF_PATH = HERE / "Workshop_Slide_Deck.pdf"
BG_PATH  = HERE / "slide_bg.png"

# ---------------------------------------------------------------------------
# Colour palette  (R, G, B) — matches reference PPTX
# ---------------------------------------------------------------------------
C_BG        = ( 11,  15,  26)   # #0B0F1A near-black background
C_TEXT      = (232, 234, 240)   # #E8EAF0 off-white body text
C_AMBER     = (247, 183,  49)   # #F7B731 amber accent
C_GREY      = (136, 146, 164)   # #8892A4 muted blue-grey
C_GREEN     = ( 38, 217, 127)   # #26D97F checkpoint green
C_RED       = (255, 107, 107)   # #FF6B6B coral/warning
C_PURPLE    = (124, 110, 253)   # #7C6EFD discussion purple
C_CODE      = (168, 180, 208)   # #A8B4D0 code text
C_GHOST     = ( 14,  17,  24)   # #0E1118 ghost number (barely visible)
C_DIM       = ( 60,  70,  90)   # dark separator lines

CHIP_COLORS = {
    "POLL":             C_AMBER,
    "CHECKPOINT":       C_GREEN,
    "DISCUSSION":       C_PURPLE,
    "EXERCISE":         C_RED,
    "YOUR TURN":        C_RED,
    "STORY BEAT":       C_PURPLE,
    "SESSION 1":        C_AMBER,
    "SESSION 2":        C_AMBER,
    "SESSION 3":        C_AMBER,
    "SESSION 4":        C_AMBER,
    "SESSION 5":        C_AMBER,
    "SESSION 6":        C_AMBER,
    "SESSION 7":        C_AMBER,
    "SESSION 8":        C_AMBER,
    "WORKSHOP COMPLETE": C_GREEN,
    "INDABA 2026":      C_AMBER,
    "3-HOUR WORKSHOP":  C_GREY,
}

# ---------------------------------------------------------------------------
# Layout constants  (mm, A4 landscape 297 × 210)
# ---------------------------------------------------------------------------
PW, PH = 297, 210
MARGIN  = 14
COL_W   = PW - 2 * MARGIN

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def rgb(c):
    return c[0], c[1], c[2]


def sanitize(t: str) -> str:
    return (t.replace("•", "-").replace("–", "-")
             .replace("—", "--").replace("‘", "'")
             .replace("’", "'").replace("“", '"')
             .replace("”", '"').replace("…", "..."))


# ---------------------------------------------------------------------------
# Markdown parser
# ---------------------------------------------------------------------------

def _field(block: str, name: str) -> str:
    m = re.search(rf'\*\*{re.escape(name)}:\*\*[ \t]*(.+)', block)
    return m.group(1).strip() if m else ""


def _multifield(block: str, name: str) -> str:
    m = re.search(rf'\*\*{re.escape(name)}:\*\*\n(.*?)(?=\n\*\*|\Z)',
                  block, re.DOTALL)
    return m.group(1).strip() if m else ""


def _arrow_lines(text: str) -> list[str]:
    lines = []
    for ln in text.splitlines():
        ln = ln.strip()
        if ln.startswith("->") or ln.startswith("→"):
            lines.append(ln.lstrip("->").lstrip("→").strip())
        elif ln.startswith("A —") or re.match(r'^[ABCD] —', ln):
            lines.append(ln)
        elif ln and not ln.startswith("#"):
            lines.append(ln)
    return [l for l in lines if l]


def _check_lines(text: str) -> list[str]:
    lines = []
    for ln in text.splitlines():
        ln = ln.strip()
        if ln.startswith(">>"):
            lines.append(ln.lstrip(">").strip())
        elif ln.startswith(">"):
            lines.append(ln.lstrip(">").strip())
    return [l for l in lines if l]


def _labelled_sections(block: str) -> list[tuple[str, list[str]]]:
    """Return [(label, [bullet, ...]), ...] for Label N / Bullets N pairs."""
    sections = []
    for i in range(1, 6):
        label = _field(block, f"Label {i}")
        raw   = _multifield(block, f"Bullets {i}")
        if not label and not raw:
            break
        bullets = _arrow_lines(raw)
        if label or bullets:
            sections.append((label, bullets))
    return sections


def _col_section(block: str, side: str) -> tuple[str, list[str]]:
    label = _field(block, f"Col {side} label")
    raw   = _multifield(block, f"Col {side} bullets")
    return label, _arrow_lines(raw)


def _code_block(block: str) -> str:
    m = re.search(r'```(?:python|sql|bash)?\n(.*?)```', block, re.DOTALL)
    return m.group(1).rstrip() if m else ""


def parse_slides(path: Path) -> list[dict]:
    text   = path.read_text(encoding="utf-8")
    blocks = re.split(r'\n(?=## Slide \d+)', text)
    slides = []

    for block in blocks:
        if not re.match(r'## Slide \d+', block.strip()):
            continue

        m = re.match(r'## Slide (\d+): (.+)', block)
        if not m:
            continue

        s = {
            "number":       m.group(1),
            "heading":      m.group(2).strip(),
            "type":         _field(block, "Type").upper(),
            "chip":         _field(block, "Chip").upper(),
            "ghost":        _field(block, "Ghost number"),
            "section_title":_field(block, "Section title"),
            "section_sub":  _field(block, "Section subtitle"),
            "title":        _field(block, "Title"),
            "subtitle":     _field(block, "Subtitle"),
            "chip1":        _field(block, "Chip 1").upper(),
            "chip2":        _field(block, "Chip 2").upper(),
            "credit":       _field(block, "Credit"),
            "main_message": _field(block, "Main message"),
            "statement":    _field(block, "Statement"),
            "closing_line": _field(block, "Closing line"),
            "answer":       _field(block, "Answer"),
            "notes":        " ".join(_multifield(block, "Speaker notes").split()),
            "cue":          _field(block, "Instructor cue"),
            "sections":     _labelled_sections(block),
            "code":         _code_block(block),
            "items":        _check_lines(_multifield(block, "Items")),
        }

        # Poll options
        opts_raw = _multifield(block, "Options")
        s["options"] = _arrow_lines(opts_raw) if opts_raw else []

        # Scenario lines (DISCUSSION)
        scen_raw = _multifield(block, "Scenarios")
        s["scenarios"] = _arrow_lines(scen_raw) if scen_raw else []

        # Design questions (EXERCISE)
        dq_raw = _multifield(block, "Design questions")
        s["design_questions"] = _arrow_lines(dq_raw) if dq_raw else []

        # Exercise scenario text
        s["scenario_text"] = _field(block, "Scenario")

        # Tags line (CLOSING)
        tags_raw = _multifield(block, "Tags")
        s["tags"] = _arrow_lines(tags_raw) if tags_raw else []

        # WHO slide columns
        s["col_left"]  = _col_section(block, "left")
        s["col_right"] = _col_section(block, "right")
        s["bottom_label"] = _field(block, "Bottom label")
        s["bottom_text"]  = _field(block, "Bottom text")

        # Timer (EXERCISE)
        s["timer"] = _field(block, "Timer")

        # Story fields
        s["story_text"]     = _multifield(block, "Story text")
        s["story_fields"]   = _arrow_lines(_multifield(block, "Data fields"))
        s["her_problem"]    = _multifield(block, "Her problem")

        slides.append(s)

    return slides


# ---------------------------------------------------------------------------
# PDF renderer
# ---------------------------------------------------------------------------

class SlidePDF(FPDF):

    def __init__(self):
        super().__init__(orientation="L", unit="mm", format="A4")
        self.add_font("Ar",  style="",   fname=str(FONT_R))
        self.add_font("Ar",  style="B",  fname=str(FONT_B))
        self.add_font("Ar",  style="I",  fname=str(FONT_I))
        self.add_font("Ar",  style="BI", fname=str(FONT_BI))
        self.add_font("ArU", style="",   fname=str(FONT_UNI))
        self.set_auto_page_break(False)
        self.set_margins(0, 0, 0)
        self._has_bg = BG_PATH.exists()

    # ---- primitives --------------------------------------------------------

    def _page(self):
        self.add_page()
        if self._has_bg:
            self.image(str(BG_PATH), 0, 0, PW, PH)
        else:
            self.set_fill_color(*rgb(C_BG))
            self.rect(0, 0, PW, PH, style="F")

    def _f(self, style="", size=11):
        self.set_font("Ar", style=style, size=size)

    def _tc(self, c):
        self.set_text_color(*rgb(c))

    def _chip(self, label: str, x: float, y: float) -> float:
        """Draw a coloured chip, return its right edge."""
        if not label:
            return x
        color = CHIP_COLORS.get(label, C_AMBER)
        self._f("B", 8)
        w = self.get_string_width(sanitize(label)) + 8
        self.set_fill_color(*rgb(color))
        self.rect(x, y, w, 7, style="F")
        # chip text colour: dark on amber/green, white on purple/grey
        if color in (C_AMBER, C_GREEN):
            self._tc(C_BG)
        else:
            self._tc((255, 255, 255))
        self.set_xy(x, y + 0.8)
        self.cell(w, 5.5, sanitize(label), align="C",
                  new_x=XPos.RIGHT, new_y=YPos.TOP)
        return x + w

    def _slide_number(self, n: str, total: int):
        self._f("", 8)
        self._tc(C_GREY)
        self.set_xy(PW - MARGIN - 30, PH - 9)
        self.cell(30, 6, f"{n} / {total}", align="R")

    def _title(self, text: str, y: float, size=22, color=C_TEXT) -> float:
        self._f("B", size)
        self._tc(color)
        self.set_xy(MARGIN, y)
        self.multi_cell(COL_W, size * 0.45, sanitize(text),
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        return self.get_y() + 3

    def _label(self, text: str, y: float) -> float:
        self._f("B", 8)
        self._tc(C_AMBER)
        self.set_xy(MARGIN, y)
        self.cell(COL_W, 5, sanitize(text).upper(),
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        return self.get_y() + 1

    def _arrow_bullet(self, text: str, y: float, color=C_AMBER,
                      indent=MARGIN, width=None) -> float:
        width = width or COL_W - (indent - MARGIN)
        self.set_font("ArU", size=9)
        self._tc(C_AMBER)
        self.set_xy(indent, y)
        self.cell(6, 5.5, "→", new_x=XPos.RIGHT, new_y=YPos.TOP)
        self._tc(color)
        self.set_x(indent + 6)
        self.multi_cell(width - 6, 5.5, sanitize(text),
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        return self.get_y() + 0.5

    def _check_bullet(self, text: str, y: float) -> float:
        self.set_font("ArU", size=10)
        self._tc(C_GREEN)
        self.set_xy(MARGIN, y)
        self.cell(7, 6, "✓", new_x=XPos.RIGHT, new_y=YPos.TOP)
        self._tc(C_TEXT)
        self.set_x(MARGIN + 7)
        self.multi_cell(COL_W - 7, 6, sanitize(text),
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        return self.get_y() + 1

    def _notes_strip(self, notes: str):
        if not notes:
            return
        self.set_fill_color(20, 28, 50)
        self.rect(0, PH - 16, PW, 16, style="F")
        self._f("I", 7)
        self._tc(C_GREY)
        self.set_xy(MARGIN, PH - 13)
        snippet = sanitize(notes[:260]) + ("..." if len(notes) > 260 else "")
        self.multi_cell(COL_W, 4, snippet,
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def _divider_line(self, y: float):
        self.set_draw_color(*rgb(C_DIM))
        self.line(MARGIN, y, PW - MARGIN, y)

    # ---- slide type renderers ----------------------------------------------

    def render_cover(self, s: dict, total: int):
        self._page()
        # amber accent bar
        self.set_fill_color(*rgb(C_AMBER))
        self.rect(0, PH / 2 - 1.5, PW, 3, style="F")

        # chips
        cx = MARGIN
        cy = PH / 2 - 40
        if s["chip1"]:
            cx = self._chip(s["chip1"], cx, cy) + 5
        if s["chip2"]:
            self._chip(s["chip2"], cx, cy)

        # main title
        self._f("B", 30)
        self._tc(C_TEXT)
        self.set_xy(MARGIN, PH / 2 - 30)
        self.multi_cell(COL_W, 14, sanitize(s["title"]), align="C",
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # subtitle
        self._f("", 13)
        self._tc(C_GREY)
        self.set_xy(MARGIN, PH / 2 + 10)
        self.multi_cell(COL_W, 7, sanitize(s["subtitle"]), align="C",
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # credit
        if s["credit"]:
            self._f("I", 8)
            self._tc(C_GREY)
            self.set_xy(MARGIN, PH - 18)
            self.multi_cell(COL_W, 5, sanitize(s["credit"]), align="C")

        self._slide_number(s["number"], total)

    def render_who(self, s: dict, total: int):
        self._page()
        y = 12
        y = self._title(s["title"], y, size=20)
        self._divider_line(y)
        y += 4

        mid = PW / 2
        col = (mid - MARGIN - 4)

        # left column
        left_label, left_bullets = s["col_left"]
        if left_label:
            self._f("B", 8); self._tc(C_AMBER)
            self.set_xy(MARGIN, y)
            self.cell(col, 5, sanitize(left_label).upper())

        lby = y + 7
        for b in left_bullets:
            lby = self._arrow_bullet(b, lby, color=C_TEXT,
                                     indent=MARGIN, width=col - 4)

        # right column
        right_label, right_bullets = s["col_right"]
        if right_label:
            self._f("B", 8); self._tc(C_AMBER)
            self.set_xy(mid + 4, y)
            self.cell(col, 5, sanitize(right_label).upper())

        rby = y + 7
        for b in right_bullets:
            self.set_font("ArU", size=9); self._tc(C_AMBER)
            self.set_xy(mid + 4, rby)
            self.cell(6, 5.5, "→", new_x=XPos.RIGHT, new_y=YPos.TOP)
            self._f("", 9.5); self._tc(C_TEXT)
            self.set_x(mid + 10)
            self.multi_cell(col - 10, 5.5, sanitize(b),
                            new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            rby = self.get_y() + 0.5

        # bottom
        bot_y = max(lby, rby) + 6
        self._divider_line(bot_y)
        bot_y += 3
        if s["bottom_label"]:
            self._f("B", 8); self._tc(C_AMBER)
            self.set_xy(MARGIN, bot_y)
            self.cell(COL_W, 5, sanitize(s["bottom_label"]).upper())
            bot_y += 6
        if s["bottom_text"]:
            self._f("I", 10); self._tc(C_TEXT)
            self.set_xy(MARGIN, bot_y)
            self.multi_cell(COL_W, 6, sanitize(s["bottom_text"]))

        self._notes_strip(s["notes"])
        self._slide_number(s["number"], total)

    def render_story(self, s: dict, total: int):
        self._page()
        y = 12
        if s["chip"]:
            self._chip(s["chip"], MARGIN, y)
            y += 10
        y = self._title(s["title"], y, size=22, color=C_AMBER)

        if s["main_message"]:
            self._f("I", 11); self._tc(C_GREY)
            self.set_xy(MARGIN, y)
            self.multi_cell(COL_W, 6, sanitize(s["main_message"]),
                            new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            y = self.get_y() + 4

        if s["story_text"]:
            self._f("", 10); self._tc(C_TEXT)
            self.set_xy(MARGIN, y)
            self.multi_cell(COL_W, 5.5, sanitize(s["story_text"]),
                            new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            y = self.get_y() + 4

        if s["story_fields"]:
            self._label("THE DATA", y); y += 6
            for b in s["story_fields"]:
                y = self._arrow_bullet(b, y, color=C_TEXT)

        if s["her_problem"]:
            y += 3
            self._divider_line(y); y += 3
            self._label("HER PROBLEM", y); y += 6
            self._f("", 10); self._tc(C_RED)
            self.set_xy(MARGIN, y)
            self.multi_cell(COL_W, 5.5, sanitize(s["her_problem"]),
                            new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self._notes_strip(s["notes"])
        self._slide_number(s["number"], total)

    def render_poll(self, s: dict, total: int):
        self._page()
        y = 12
        self._chip(s["chip"] or "POLL", MARGIN, y)
        y += 11
        y = self._title(s["title"], y, size=20, color=C_TEXT)

        if s["main_message"]:
            self._f("I", 10); self._tc(C_GREY)
            self.set_xy(MARGIN, y)
            self.multi_cell(COL_W, 5.5, sanitize(s["main_message"]),
                            new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            y = self.get_y() + 5

        letters = ["A", "B", "C", "D"]
        for i, opt in enumerate(s["options"]):
            letter = letters[i] if i < len(letters) else str(i + 1)
            # split "A -- text" or use letter directly
            parts = re.split(r'\s*—\s*|\s*--\s*', opt, maxsplit=1)
            opt_text = parts[1] if len(parts) == 2 else opt
            # letter chip
            self.set_fill_color(*rgb(C_DIM))
            self.rect(MARGIN, y, 9, 7, style="F")
            self._f("B", 10); self._tc(C_AMBER)
            self.set_xy(MARGIN, y + 0.5)
            self.cell(9, 6, letter, align="C", new_x=XPos.RIGHT, new_y=YPos.TOP)
            # option text
            self._f("", 11); self._tc(C_TEXT)
            self.set_x(MARGIN + 12)
            self.multi_cell(COL_W - 12, 6.5, sanitize(opt_text),
                            new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            y = self.get_y() + 2

        if s["answer"]:
            y += 2
            self._divider_line(y); y += 3
            self._f("B", 8); self._tc(C_GREEN)
            self.set_xy(MARGIN, y)
            self.cell(COL_W, 5, "ANSWER")
            y += 5
            self._f("I", 9); self._tc(C_GREY)
            self.set_xy(MARGIN, y)
            self.multi_cell(COL_W, 5, sanitize(s["answer"]))

        self._notes_strip(s["notes"])
        self._slide_number(s["number"], total)

    def render_section(self, s: dict, total: int):
        self._page()
        # ghost section number — centred, very dark, massive
        if s["ghost"]:
            self._f("B", 90)
            self._tc(C_GHOST)
            self.set_xy(0, PH / 2 - 58)
            self.cell(PW, 80, sanitize(s["ghost"]), align="C")

        # chip
        cy = PH / 2 - 22
        self._chip(s["chip"] or "SESSION", MARGIN, cy)

        # section title
        self._f("B", 34)
        self._tc(C_TEXT)
        self.set_xy(MARGIN, cy + 11)
        self.multi_cell(COL_W, 16, sanitize(s["section_title"]),
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # subtitle
        if s["section_sub"]:
            self._f("", 12)
            self._tc(C_GREY)
            self.set_xy(MARGIN, self.get_y() + 1)
            self.multi_cell(COL_W, 6, sanitize(s["section_sub"]))

        self._slide_number(s["number"], total)

    def render_content(self, s: dict, total: int):
        self._page()
        y = 12
        y = self._title(s["title"], y, size=20)

        if s["main_message"]:
            self._f("I", 10); self._tc(C_GREY)
            self.set_xy(MARGIN, y)
            self.multi_cell(COL_W, 5.5, sanitize(s["main_message"]),
                            new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            y = self.get_y() + 4

        self._divider_line(y); y += 4

        for label, bullets in s["sections"]:
            if y > PH - 30:
                break
            if label:
                y = self._label(label, y)
            for b in bullets:
                if y > PH - 24:
                    break
                y = self._arrow_bullet(b, y, color=C_TEXT)
            y += 3

        if s["cue"]:
            self._f("B", 8); self._tc(C_RED)
            self.set_xy(MARGIN, PH - 22)
            self.cell(COL_W, 5, sanitize(s["cue"]))

        self._notes_strip(s["notes"])
        self._slide_number(s["number"], total)

    def render_code(self, s: dict, total: int):
        self._page()
        y = 12
        y = self._title(s["title"], y, size=18)

        if s["main_message"]:
            self._f("I", 10); self._tc(C_GREY)
            self.set_xy(MARGIN, y)
            self.multi_cell(COL_W * 0.66, 5.5, sanitize(s["main_message"]),
                            new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            y = self.get_y() + 3

        # Code block (left 2/3)
        code_w = COL_W * 0.64
        code_h = PH - y - 20
        if s["code"] and code_h > 10:
            self.set_fill_color(18, 24, 40)
            self.rect(MARGIN, y, code_w, code_h, style="F")
            self._f("", 8.5)
            self._tc(C_CODE)
            self.set_xy(MARGIN + 3, y + 3)
            lines = s["code"].split("\n")
            line_h = 4.8
            for ln in lines:
                if self.get_y() > y + code_h - 6:
                    break
                self.cell(code_w - 6, line_h, sanitize(ln),
                          new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # KEY DECISIONS sidebar (right 1/3)
        side_x = MARGIN + code_w + 5
        side_w = COL_W - code_w - 5
        sy = y
        for label, bullets in s["sections"]:
            if sy > PH - 25:
                break
            self._f("B", 8); self._tc(C_AMBER)
            self.set_xy(side_x, sy)
            self.cell(side_w, 5, sanitize(label or "KEY DECISIONS").upper())
            sy += 6
            for b in bullets:
                if sy > PH - 22:
                    break
                self.set_font("ArU", size=9); self._tc(C_AMBER)
                self.set_xy(side_x, sy)
                self.cell(5, 5, "→")
                self._tc(C_TEXT)
                self.set_x(side_x + 5)
                self.multi_cell(side_w - 5, 5, sanitize(b),
                                new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                sy = self.get_y() + 1

        if s["cue"]:
            self._f("B", 8); self._tc(C_RED)
            self.set_xy(MARGIN, PH - 22)
            self.cell(COL_W, 5, sanitize(s["cue"]))

        self._notes_strip(s["notes"])
        self._slide_number(s["number"], total)

    def render_discussion(self, s: dict, total: int):
        self._page()
        y = 12
        self._chip(s["chip"] or "DISCUSSION", MARGIN, y); y += 11
        y = self._title(s["title"], y, size=20, color=C_TEXT)

        if s["main_message"]:
            self._f("I", 10); self._tc(C_GREY)
            self.set_xy(MARGIN, y)
            self.multi_cell(COL_W, 5.5, sanitize(s["main_message"]),
                            new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            y = self.get_y() + 5

        for sc in s["scenarios"]:
            if y > PH - 28:
                break
            y = self._arrow_bullet(sc, y, color=C_TEXT)

        self._notes_strip(s["notes"])
        self._slide_number(s["number"], total)

    def render_checkpoint(self, s: dict, total: int):
        self._page()
        y = 12
        self._chip(s["chip"] or "CHECKPOINT", MARGIN, y); y += 11
        y = self._title(s["title"], y, size=20, color=C_GREEN)

        if s["main_message"]:
            self._f("I", 10); self._tc(C_GREY)
            self.set_xy(MARGIN, y)
            self.multi_cell(COL_W, 5.5, sanitize(s["main_message"]),
                            new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            y = self.get_y() + 5

        for item in s["items"]:
            if y > PH - 28:
                break
            y = self._check_bullet(item, y)

        self._notes_strip(s["notes"])
        self._slide_number(s["number"], total)

    def render_exercise(self, s: dict, total: int):
        self._page()
        y = 12
        self._chip(s["chip"] or "EXERCISE", MARGIN, y); y += 11
        y = self._title(s["title"], y, size=19, color=C_TEXT)

        if s["main_message"]:
            self._f("I", 10); self._tc(C_GREY)
            self.set_xy(MARGIN, y)
            self.multi_cell(COL_W, 5.5, sanitize(s["main_message"]),
                            new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            y = self.get_y() + 4

        if s["scenario_text"]:
            self._label("SCENARIO", y); y += 6
            self._f("", 10); self._tc(C_TEXT)
            self.set_xy(MARGIN, y)
            self.multi_cell(COL_W, 5.5, sanitize(s["scenario_text"]),
                            new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            y = self.get_y() + 4

        if s["design_questions"]:
            self._label("DESIGN QUESTIONS", y); y += 6
            for i, q in enumerate(s["design_questions"], 1):
                if y > PH - 28:
                    break
                self._f("B", 9); self._tc(C_AMBER)
                self.set_xy(MARGIN, y)
                self.cell(8, 5.5, str(i) + ".", new_x=XPos.RIGHT, new_y=YPos.TOP)
                self._tc(C_TEXT)
                self.set_x(MARGIN + 8)
                self.multi_cell(COL_W - 8, 5.5, sanitize(q),
                                new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                y = self.get_y() + 1

        if s["timer"]:
            y += 3
            self._f("B", 10); self._tc(C_RED)
            self.set_xy(MARGIN, min(y, PH - 28))
            self.cell(COL_W, 6, sanitize(s["timer"]))

        if s["cue"]:
            self._f("B", 8); self._tc(C_RED)
            self.set_xy(MARGIN, PH - 22)
            self.cell(COL_W, 5, sanitize(s["cue"]))

        self._notes_strip(s["notes"])
        self._slide_number(s["number"], total)

    def render_closing(self, s: dict, total: int):
        self._page()
        # amber accent bar
        self.set_fill_color(*rgb(C_AMBER))
        self.rect(0, PH / 2 - 1.5, PW, 3, style="F")

        cy = PH / 2 - 50
        self._chip(s["chip"] or "WORKSHOP COMPLETE", MARGIN, cy); cy += 11

        self._f("B", 26); self._tc(C_TEXT)
        self.set_xy(MARGIN, cy)
        self.multi_cell(COL_W, 13, sanitize(s["title"]),
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        cy = self.get_y() + 5

        if s["statement"]:
            self._f("", 12); self._tc(C_GREY)
            self.set_xy(MARGIN, cy)
            self.multi_cell(COL_W, 6, sanitize(s["statement"]),
                            new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            cy = self.get_y() + 6

        for tag in s["tags"]:
            self.set_font("ArU", size=10); self._tc(C_AMBER)
            self.set_xy(MARGIN, cy)
            self.cell(COL_W, 6, "→  " + sanitize(tag),
                      new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            cy = self.get_y()

        if s["closing_line"]:
            self._f("I", 11); self._tc(C_GREY)
            self.set_xy(MARGIN, PH - 24)
            self.multi_cell(COL_W, 6, '"' + sanitize(s["closing_line"]) + '"',
                            align="C")

        self._slide_number(s["number"], total)

    def render_appendix(self, s: dict, total: int):
        self.render_content(s, total)

    # ---- dispatch ----------------------------------------------------------

    RENDERERS = {
        "COVER":      render_cover,
        "WHO":        render_who,
        "STORY":      render_story,
        "POLL":       render_poll,
        "SECTION":    render_section,
        "CONTENT":    render_content,
        "CODE":       render_code,
        "DISCUSSION": render_discussion,
        "CHECKPOINT": render_checkpoint,
        "EXERCISE":   render_exercise,
        "CLOSING":    render_closing,
        "APPENDIX":   render_appendix,
    }

    def add_slide(self, s: dict, total: int):
        renderer = self.RENDERERS.get(s["type"], SlidePDF.render_content)
        renderer(self, s, total)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"Parsing {MD_PATH} ...")
    slides = parse_slides(MD_PATH)
    if not slides:
        raise SystemExit("No slides found.")
    print(f"  Found {len(slides)} slides.")

    if BG_PATH.exists():
        print(f"  Background: {BG_PATH}")
    else:
        print("  Background: solid dark colour (slide_bg.png not found)")

    pdf = SlidePDF()
    total = len(slides)
    for s in slides:
        pdf.add_slide(s, total)

    pdf.output(str(PDF_PATH))
    size_kb = PDF_PATH.stat().st_size // 1024
    print(f"  PDF written -> {PDF_PATH}  ({size_kb} KB, {total} pages)")


if __name__ == "__main__":
    main()
