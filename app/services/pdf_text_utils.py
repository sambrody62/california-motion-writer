"""
Text-fitting utilities for PDF form overlays.

Court forms have fixed boxes; user text does not. The rules here:
- single-line fields shrink to fit (down to a floor), then truncate VISIBLY
- multi-line boxes never lose text — overflow continues on attachment pages,
  matching California court practice (MC-025-style continuation)
"""
import io
from typing import List, Tuple

from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas as rl_canvas

FONT = "Helvetica"
DEFAULT_SIZE = 10
MIN_SIZE = 6
LINE_HEIGHT = 12
PAGE_WIDTH, PAGE_HEIGHT = letter
MARGIN = 72


def fit_single_line(
    text: str,
    max_width: float,
    font: str = FONT,
    size: int = DEFAULT_SIZE,
    min_size: int = MIN_SIZE,
) -> Tuple[int, str]:
    """Shrink font until the text fits; below min_size, truncate with an ellipsis."""
    for candidate in range(size, min_size - 1, -1):
        if stringWidth(text, font, candidate) <= max_width:
            return candidate, text
    truncated = text
    while truncated and stringWidth(truncated + "…", font, min_size) > max_width:
        truncated = truncated[:-1]
    return min_size, truncated + "…"


def wrap_text_accurate(
    text: str,
    width: float,
    font: str = FONT,
    size: int = DEFAULT_SIZE,
) -> List[str]:
    """Word-wrap using real string widths; blank lines preserve paragraph breaks."""
    lines: List[str] = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue
        current: List[str] = []
        for word in paragraph.split():
            candidate = " ".join(current + [word])
            if current and stringWidth(candidate, font, size) > width:
                lines.append(" ".join(current))
                current = [word]
            else:
                current.append(word)
        if current:
            lines.append(" ".join(current))
    return lines


def draw_lines_in_box(
    canvas_obj,
    lines: List[str],
    x: float,
    y: float,
    height: float,
    line_height: int = LINE_HEIGHT,
) -> List[str]:
    """
    Draw lines top-down from y within the box height; return the overflow.
    When overflow exists, the box's last line is replaced by a visible
    continuation marker so the reader knows to look for the attachment.
    """
    capacity = max(1, int(height // line_height) + 1)
    if len(lines) <= capacity:
        fitting, overflow = lines, []
    else:
        # Reserve the final slot for the continuation marker
        fitting, overflow = lines[: capacity - 1], lines[capacity - 1:]

    current_y = y
    for line in fitting:
        canvas_obj.drawString(x, current_y, line)
        current_y -= line_height
    if overflow:
        canvas_obj.drawString(x, current_y, "(continued on Attachment)")
    return overflow


def build_continuation_pages(
    lines: List[str],
    caption: str,
    case_number: str = "",
    font: str = FONT,
    size: int = DEFAULT_SIZE,
) -> bytes:
    """Render overflow lines onto captioned letter-size attachment pages."""
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=letter)
    body_top = PAGE_HEIGHT - MARGIN - 40
    body_bottom = MARGIN

    remaining = list(lines)
    while remaining:
        c.setFont(font, size)
        c.drawString(MARGIN, PAGE_HEIGHT - MARGIN, caption)
        if case_number:
            c.drawRightString(PAGE_WIDTH - MARGIN, PAGE_HEIGHT - MARGIN, f"Case No.: {case_number}")
        c.line(MARGIN, PAGE_HEIGHT - MARGIN - 8, PAGE_WIDTH - MARGIN, PAGE_HEIGHT - MARGIN - 8)

        current_y = body_top
        while remaining and current_y >= body_bottom:
            c.drawString(MARGIN, current_y, remaining.pop(0))
            current_y -= LINE_HEIGHT
        c.showPage()

    c.save()
    buf.seek(0)
    return buf.read()
