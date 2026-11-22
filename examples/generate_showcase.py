"""Generate a complete showcase of all 16 print game types + PNG previews + sample booklet."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from printgames.games import produce_booklet, produce_game_from_dict
from printgames.models import BookletSpec
from test_all_games import sample_specs


def main() -> None:
    out_dir = ROOT / "output" / "showcase"
    out_dir.mkdir(parents=True, exist_ok=True)
    specs = sample_specs(out_dir)

    print(f"Generating all {len(specs)} print games into {out_dir} ...")
    for spec in specs:
        spec["render_preview_png"] = True
        res = produce_game_from_dict(spec)
        status = "OK" if not res.warnings else f"WARN: {res.warnings}"
        print(
            f"  - {spec['game_type']:<20} | {res.page_size_label:<32} | "
            f"pages={res.verified_pdf_pages}/{res.expected_pages} | {status}"
        )

    booklet = BookletSpec(
        booklet_title="PrintGames Complete Sampler",
        subtitle="Six Handpicked Classics Across Word, Visual & Tabletop Play",
        author="PrintGames MCP Studio",
        page_size="letter",
        theme="editorial_classic",
        include_cover=True,
        include_toc=True,
        collate_answer_keys_at_end=True,
        games=[specs[0], specs[5], specs[6], specs[7], specs[13], specs[15]],
        output_path=str(out_dir / "00_sampler_booklet.pdf"),
        render_preview_png=True,
    )
    bres = produce_booklet(booklet)
    print(
        f"  - {'booklet':<20} | {bres.page_size_label:<32} | "
        f"pages={bres.verified_pdf_pages}/{bres.expected_pages} | warnings={bres.warnings}"
    )


if __name__ == "__main__":
    main()
