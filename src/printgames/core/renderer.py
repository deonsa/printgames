"""HTML document assembly, Headless Chrome PDF rendering, and page-fit verification."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import textwrap
from dataclasses import dataclass
from html import escape
from pathlib import Path

from .pages import PageSpec
from .themes import ThemeSpec, build_base_css


class PdfExportError(RuntimeError):
    """The configured browsers could not produce a PDF."""


@dataclass
class RenderedPage:
    """One physical printed page's HTML content."""

    title: str
    category: str
    body_html: str
    instructions: str | None = None
    subtitle: str | None = None
    difficulty: str | None = None
    is_answer_key: bool = False
    footer_left: str = ""
    footer_right: str = ""
    extra_badges: list[str] | None = None
    custom_page_html: str | None = None  # For cover / TOC pages that bypass standard frame


@dataclass
class ExportResult:
    output_paths: dict[str, str]
    expected_pages: int
    verified_pdf_pages: int | None
    page_size_label: str
    page_dimensions_mm: tuple[float, float]
    warnings: list[str]
    fit_verified: bool | None = None


def _render_standard_page(
    p: RenderedPage,
    page_num: int,
    total_pages: int,
) -> str:
    if p.custom_page_html is not None:
        return f'<section class="page">{p.custom_page_html}</section>'

    badges: list[str] = []
    if p.is_answer_key:
        badges.append('<span class="pill pill-key">Answer Key</span>')
    badges.append(f'<span class="pill">{escape(p.category)}</span>')
    if p.difficulty:
        badges.append(f'<span class="pill pill-muted">{escape(p.difficulty.replace("_", " "))}</span>')
    if p.extra_badges:
        for b in p.extra_badges:
            badges.append(f'<span class="pill pill-muted">{escape(b)}</span>')

    subtitle_html = f'<p class="game-subtitle">{escape(p.subtitle)}</p>' if p.subtitle else ""
    instr_html = ""
    if p.instructions:
        instr_html = (
            '<div class="instructions-box">'
            '<span class="instructions-label">How to Play:</span>'
            f"{escape(p.instructions)}"
            "</div>"
        )

    f_left = escape(p.footer_left) if p.footer_left else escape(p.category)
    f_right = escape(p.footer_right) if p.footer_right else f"Page {page_num} of {total_pages}"

    return f"""<section class="page">
  <div class="page-frame">
    <header class="page-header">
      <div class="header-meta">
        <div class="badge-group">{''.join(badges)}</div>
        <span style="font-size:0.78em;color:var(--muted, inherit);opacity:0.75;">{escape(f"#{page_num}" if total_pages > 1 else "")}</span>
      </div>
      <div class="title-row">
        <div>
          <h1 class="game-title">{escape(p.title)}</h1>
          {subtitle_html}
        </div>
      </div>
      {instr_html}
    </header>
    <main class="page-body">
      {p.body_html}
    </main>
    <footer class="page-footer">
      <span>{f_left}</span>
      <span>{f_right}</span>
    </footer>
  </div>
</section>"""


def build_cover_page_html(
    title: str,
    subtitle: str | None,
    author: str | None,
    game_count: int,
    theme: ThemeSpec,
    page: PageSpec,
) -> str:
    s = page.scale
    sub_html = (
        f'<p style="font-size:{12.5 * s:.1f}pt;color:{theme.ink_muted};font-style:italic;max-width:78%;margin:4mm auto 0;">{escape(subtitle)}</p>'
        if subtitle
        else ""
    )
    author_html = (
        f'<div style="margin-top:auto;font-size:{10 * s:.1f}pt;color:{theme.ink_muted};letter-spacing:0.08em;text-transform:uppercase;">Curated by {escape(author)}</div>'
        if author
        else ""
    )
    return f"""
<div class="page-frame" style="justify-content:center;align-items:center;text-align:center;padding:{14 * s:.1f}mm;background:radial-gradient(circle at 50% 42%, {theme.panel_bg}, {theme.paper} 72%);">
  <div style="margin-top:auto;"></div>
  <div style="border:0.9pt solid {theme.accent};padding:{1.5 * s:.1f}mm {5 * s:.1f}mm;border-radius:999px;font-size:{8 * s:.1f}pt;font-weight:700;letter-spacing:0.16em;text-transform:uppercase;color:{theme.accent};background:{theme.accent_soft};margin-bottom:{8 * s:.1f}mm;">
    Print Games Collection · {game_count} Activities
  </div>
  <div style="width:{36 * s:.1f}mm;height:1.5pt;background:{theme.accent};margin:0 auto {6 * s:.1f}mm;"></div>
  <h1 style="font-family:{theme.font_display};font-size:{32 * s:.1f}pt;line-height:1.12;margin:0;color:{theme.ink};max-width:86%;">{escape(title)}</h1>
  {sub_html}
  <div style="width:{36 * s:.1f}mm;height:1.5pt;background:{theme.accent};margin:{8 * s:.1f}mm auto;"></div>
  <div style="margin-top:{6 * s:.1f}mm;padding:{4 * s:.1f}mm {7 * s:.1f}mm;border:0.8pt dashed {theme.border_strong};border-radius:2mm;background:{theme.paper};font-size:{9.5 * s:.1f}pt;color:{theme.ink_muted};">
    This book belongs to: <span style="display:inline-block;width:{48 * s:.1f}mm;border-bottom:0.9pt solid {theme.ink};margin-left:2mm;"></span>
  </div>
  {author_html}
</div>"""


def paginate_toc(
    entries: list[tuple[str, str, int]], page: PageSpec, has_answer_section: bool
) -> list[list[tuple[str, str, int]]]:
    """Budget for wrapped titles, the category line, heading and footer in physical units."""
    s = page.scale
    text_width = page.content_width_mm - 16 * s - 33
    chars_per_line = max(1, int(text_width / (3.4 * s)))
    available = page.content_height_mm - 44 * s
    if has_answer_section:
        available -= 12 * s
    chunks: list[list[tuple[str, str, int]]] = [[]]
    used = 0.0
    for entry in entries:
        title, category, _ = entry
        lines = len(textwrap.wrap(title, chars_per_line)) + len(textwrap.wrap(category, chars_per_line))
        height = (3.3 + 4.8 * lines) * s
        if chunks[-1] and used + height > available:
            chunks.append([])
            used = 0.0
        chunks[-1].append(entry)
        used += height
    return chunks


def build_toc_page_html(
    entries: list[tuple[str, str, int]],
    answer_start_page: int | None,
    theme: ThemeSpec,
    page: PageSpec,
    first_index: int = 1,
) -> str:
    s = page.scale
    rows = []
    for idx, (title, category, pnum) in enumerate(entries, start=first_index):
        rows.append(
            f'<div style="display:grid;grid-template-columns:auto minmax(0,1fr) auto;gap:2.5mm;'
            f'padding:{1.4 * s:.2f}mm 0;border-bottom:0.5pt dotted {theme.border};">'
            f'<span style="font-weight:700;color:{theme.accent};min-width:6mm;">{idx:02d}.</span>'
            f'<div style="overflow-wrap:anywhere;"><b>{escape(title)}</b><br>'
            f'<span style="font-size:{7.6 * s:.1f}pt;color:{theme.ink_muted};">{escape(category)}</span></div>'
            f'<span style="font-weight:700;font-family:{theme.font_mono};">p. {pnum}</span></div>'
        )
    if answer_start_page is not None:
        rows.append(
            f'<div style="display:flex;align-items:baseline;gap:2.5mm;padding:{2.2 * s:.2f}mm 0 0;margin-top:2mm;border-top:1pt solid {theme.border_strong};">'
            f'<span style="font-weight:700;color:{theme.accent};">★</span>'
            f'<span style="font-weight:700;color:{theme.accent};text-transform:uppercase;letter-spacing:0.06em;">Answer Keys</span>'
            f'<span style="flex:1;"></span>'
            f'<span style="font-weight:700;font-family:{theme.font_mono};color:{theme.accent};">p. {answer_start_page}</span>'
            f"</div>"
        )
    return f"""
<div class="page-frame" style="padding:{8 * s:.1f}mm;">
  <div style="text-align:center;margin-bottom:{5 * s:.1f}mm;">
    <span class="pill">Contents</span>
    <h1 class="game-title" style="margin-top:2mm;">Table of Contents</h1>
  </div>
  <div style="flex:1;overflow:hidden;font-size:{9.4 * s:.1f}pt;">
    {''.join(rows)}
  </div>
  <div class="page-footer">
    <span>PrintGames Booklet</span>
    <span>{escape(page.label)}</span>
  </div>
</div>"""


def assemble_html_document(
    pages: list[RenderedPage],
    page_spec: PageSpec,
    theme: ThemeSpec,
    doc_title: str,
    extra_css: str = "",
    *,
    print_layout: bool = False,
) -> str:
    base_css = build_base_css(page_spec, theme, print_layout=print_layout)
    total = len(pages)
    rendered_sections = [
        _render_standard_page(p, idx + 1, total) for idx, p in enumerate(pages)
    ]
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{escape(doc_title)}</title>
  <style>
{base_css}
{extra_css}
  </style>
</head>
<body>
{''.join(rendered_sections)}
</body>
</html>"""


def _chrome_binaries() -> list[str]:
    preferred = os.environ.get("PRINTGAMES_CHROME")
    if preferred:
        executable = shutil.which(preferred)
        if not executable:
            raise PdfExportError(f"PRINTGAMES_CHROME executable unavailable: {preferred}")
        return [executable]

    binaries = []
    seen = set()
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
                 "chromium-headless-shell", "chrome-headless-shell", "/snap/bin/chromium"):
        path = shutil.which(name)
        if path and os.path.realpath(path) not in seen:
            binaries.append(path)
            seen.add(os.path.realpath(path))
    return binaries


def _inspect_pdf_pages(pdf_path: Path) -> int | None:
    pdfinfo = shutil.which("pdfinfo")
    if not pdfinfo:
        return None
    proc = subprocess.run(
        [pdfinfo, str(pdf_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    for line in proc.stdout.splitlines():
        if line.startswith("Pages:"):
            try:
                return int(line.split(":", 1)[1].strip())
            except ValueError:
                return None
    return None


# The probe is added only to the temporary measurement document. The public
# HTML and the PDF source contain no scripts.
_FIT_PROBE = """<script>
document.fonts.ready.then(() => {
  const pages = [...document.querySelectorAll('section.page')];
  const clipped = [];
  function contentIsClipped(el) {
    if (el instanceof SVGTextElement && el.getClientRects().length) {
      // Client rectangles include group transforms and viewBox scaling.
      const label = el.getBoundingClientRect();
      for (let parent = el.parentElement; parent; parent = parent.parentElement) {
        if (!(parent instanceof SVGSVGElement || parent instanceof HTMLElement)) continue;
        const style = getComputedStyle(parent);
        const bounds = parent.getBoundingClientRect();
        if (style.overflowX !== 'visible' &&
            (label.left < bounds.left - 1 || label.right > bounds.right + 1)) return true;
        if (style.overflowY !== 'visible' &&
            (label.top < bounds.top - 1 || label.bottom > bounds.bottom + 1)) return true;
      }
    }
    if (!(el instanceof HTMLElement) || !el.getClientRects().length) return false;
    const style = getComputedStyle(el);
    const clipX = ['hidden', 'clip', 'auto', 'scroll'].includes(style.overflowX);
    const clipY = ['hidden', 'clip', 'auto', 'scroll'].includes(style.overflowY);
    if (!clipX && !clipY) return false;
    if ((clipX && el.scrollWidth > el.clientWidth + 1) ||
        (clipY && el.scrollHeight > el.clientHeight + 1)) return true;
    // Centered flex children can overflow the start edge without increasing scrollHeight.
    const bounds = el.getBoundingClientRect();
    return [...el.children].some(child => {
      const rect = child.getBoundingClientRect();
      return rect.width && rect.height &&
        ((clipX && rect.left < bounds.left - 1) || (clipY && rect.top < bounds.top - 1));
    });
  }
  pages.forEach((page, i) => {
    if ([page, ...page.querySelectorAll('*')].some(contentIsClipped)) clipped.push(i + 1);
  });
  document.body.dataset.printgamesFit = pages.length + ':' + clipped.join(',');
});
</script>"""


def _render_html_to_pdf(html_content: str, pdf_path: Path, expected_pages: int) -> list[int] | None:
    """Print and measure the same fixed-size sheets. None means measurement was unavailable."""
    binaries = _chrome_binaries()
    if not binaries:
        raise PdfExportError(
            "No Chromium/Google Chrome binary found for PDF export. "
            "Install google-chrome or chromium, or set output_format='html'."
        )
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=pdf_path.parent) as work_dir:
        work = Path(work_dir)
        source = work / "worksheet.html"
        staged_pdf = work / "worksheet.pdf"
        source.write_text(html_content, encoding="utf-8")
        pdf_args = ["--no-pdf-header-footer", "--print-to-pdf-no-header", f"--print-to-pdf={staged_pdf}"]
        failures = []
        for index, chrome in enumerate(binaries):
            flags = [
                chrome, "--headless", "--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage",
                f"--user-data-dir={work / f'profile-{index}'}",
            ]
            try:
                proc = subprocess.run([*flags, *pdf_args, source.as_uri()], capture_output=True, text=True, timeout=60)
            except (OSError, subprocess.TimeoutExpired) as exc:
                staged_pdf.unlink(missing_ok=True)
                failures.append(f"{chrome}: {exc}")
                continue
            if proc.returncode == 0 and staged_pdf.is_file() and staged_pdf.stat().st_size:
                break
            staged_pdf.unlink(missing_ok=True)
            failures.append(f"{chrome} (exit {proc.returncode}): {proc.stderr.strip()}")
        else:
            raise PdfExportError("Headless Chrome PDF export failed. Set PRINTGAMES_CHROME to a working "
                               "Chromium-compatible executable.\n" + "\n".join(failures))
        staged_pdf.replace(pdf_path)

        source.write_text(html_content.replace("</body>", _FIT_PROBE + "</body>"), encoding="utf-8")
        try:
            probe = subprocess.run(
                [*flags, "--dump-dom", "--virtual-time-budget=2000", source.as_uri()],
                capture_output=True, text=True, timeout=60,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        result = re.search(r'<body data-printgames-fit="(\d+):([\d,]*)">', probe.stdout)
        if probe.returncode or result is None or int(result[1]) != expected_pages:
            return None
        return [int(n) for n in result[2].split(",") if n]


def _render_pdf_previews(pdf_path: Path, dpi: int = 130) -> list[str]:
    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        return []
    with tempfile.TemporaryDirectory(dir=pdf_path.parent) as temp:
        prefix = Path(temp) / "page"
        proc = subprocess.run(
            [pdftoppm, "-png", "-r", str(dpi), str(pdf_path), str(prefix)],
            capture_output=True, text=True, timeout=60,
        )
        if proc.returncode:
            return []
        previews = []
        for image in sorted(prefix.parent.glob("page-*.png"), key=lambda p: int(p.stem.split("-")[1])):
            target = pdf_path.with_name(pdf_path.stem + image.name[len("page"):])
            image.replace(target)
            previews.append(str(target))
        return previews


def export_document(
    pages: list[RenderedPage],
    page_spec: PageSpec,
    theme: ThemeSpec,
    doc_title: str,
    output_path: str | Path,
    output_format: str = "pdf",
    extra_css: str = "",
    render_preview_png: bool = False,
) -> ExportResult:
    """Assemble and write HTML and/or PDF (plus optional PNG previews) with page-count verification."""
    target = Path(output_path).expanduser()
    if not target.is_absolute():
        target = Path.cwd() / target
    target.parent.mkdir(parents=True, exist_ok=True)

    output_paths: dict[str, str] = {}
    warnings: list[str] = []
    verified_pages: int | None = None
    fit_verified: bool | None = None

    if output_format in {"html", "both"}:
        html_path = target.with_suffix(".html")
        html_content = assemble_html_document(pages, page_spec, theme, doc_title, extra_css)
        html_path.write_text(html_content, encoding="utf-8")
        output_paths["html"] = str(html_path.resolve())

    if output_format in {"pdf", "both"}:
        pdf_path = target.with_suffix(".pdf")
        # Use physical paper geometry for the browser probe as well as the PDF.
        print_html = assemble_html_document(pages, page_spec, theme, doc_title, extra_css, print_layout=True)
        try:
            clipped = _render_html_to_pdf(print_html, pdf_path, len(pages))
        except PdfExportError as exc:
            if "html" in output_paths:
                recovery = output_paths["html"]
            else:
                # A PDF-only request must not overwrite a sibling HTML file.
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=pdf_path.parent,
                                                 prefix=f"{pdf_path.stem}-", suffix=".html", delete=False) as f:
                    f.write(print_html)
                    recovery = f.name
            raise PdfExportError(
                f"PDF export failed. Print-ready HTML is available at {recovery}. "
                f"Open it in a browser and choose Print → Save as PDF.\n{exc}"
            ) from exc
        output_paths["pdf"] = str(pdf_path.resolve())
        verified_pages = _inspect_pdf_pages(pdf_path)
        count_mismatch = verified_pages is not None and verified_pages != len(pages)
        if count_mismatch:
            warnings.append(
                f"Expected {len(pages)} PDF page(s) but rendered {verified_pages}. "
                "Consider reducing content density or using a larger page size."
            )
        if extra_css and re.search(r"@(?:media|import|page)\b", extra_css, re.IGNORECASE):
            # External media rules can change the layout after the physical-sheet probe.
            clipped = None
        if clipped is None:
            warnings.append("Chrome could not verify content fit.")
        elif clipped:
            warnings.append("Content is clipped on page(s) " + ", ".join(map(str, clipped)) + ".")
        if count_mismatch or clipped:
            fit_verified = False
        elif verified_pages is not None and clipped is not None:
            fit_verified = True
        if render_preview_png:
            pngs = _render_pdf_previews(pdf_path)
            if pngs:
                output_paths["preview_pngs"] = ", ".join(pngs)
            else:
                warnings.append("pdftoppm not available or failed; PNG previews skipped.")

    return ExportResult(
        output_paths=output_paths,
        expected_pages=len(pages),
        verified_pdf_pages=verified_pages,
        page_size_label=f"{page_spec.label} ({page_spec.orientation})",
        page_dimensions_mm=(page_spec.width_mm, page_spec.height_mm),
        warnings=warnings,
        fit_verified=fit_verified,
    )
