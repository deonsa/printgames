"""Command-line interface for PrintGames (MCP server, JSON spec renderer, and showcase builder)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .games import produce_booklet, produce_game_from_dict
from .models import BookletSpec
from .server import main as run_mcp_server


def _cmd_render(args: argparse.Namespace) -> int:
    spec_path = Path(args.spec)
    data = json.loads(spec_path.read_text(encoding="utf-8"))
    if args.output:
        data["output_path"] = args.output
    if args.format:
        data["output_format"] = args.format
    if args.preview:
        data["render_preview_png"] = True
    res = produce_game_from_dict(data)
    print(json.dumps({
        "files": res.output_paths,
        "page_size": res.page_size_label,
        "expected_pages": res.expected_pages,
        "verified_pdf_pages": res.verified_pdf_pages,
        "fit_verified": res.fit_verified,
        "warnings": res.warnings,
    }, indent=2))
    return 0


def _cmd_booklet(args: argparse.Namespace) -> int:
    spec_path = Path(args.spec)
    data = json.loads(spec_path.read_text(encoding="utf-8"))
    if args.output:
        data["output_path"] = args.output
    if args.format:
        data["output_format"] = args.format
    if args.preview:
        data["render_preview_png"] = True
    spec = BookletSpec.model_validate(data)
    res = produce_booklet(spec)
    print(json.dumps({
        "files": res.output_paths,
        "page_size": res.page_size_label,
        "expected_pages": res.expected_pages,
        "verified_pdf_pages": res.verified_pdf_pages,
        "fit_verified": res.fit_verified,
        "warnings": res.warnings,
    }, indent=2))
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="printgames",
        description="PrintGames — Beautiful print-ready games via MCP or CLI.",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("serve", help="Run the PrintGames MCP server over stdio.")

    p_render = sub.add_parser("render", help="Render a single game from a JSON specification file.")
    p_render.add_argument("spec", help="Path to JSON game spec file.")
    p_render.add_argument("-o", "--output", help="Override output file path.")
    p_render.add_argument("-f", "--format", choices=["pdf", "html", "both"], help="Output format.")
    p_render.add_argument("--preview", action="store_true", help="Also export PNG previews.")

    p_book = sub.add_parser("booklet", help="Render a multi-game booklet from a JSON specification file.")
    p_book.add_argument("spec", help="Path to JSON booklet spec file.")
    p_book.add_argument("-o", "--output", help="Override output file path.")
    p_book.add_argument("-f", "--format", choices=["pdf", "html", "both"], help="Output format.")
    p_book.add_argument("--preview", action="store_true", help="Also export PNG previews.")

    args = parser.parse_args(argv)
    if args.command in (None, "serve"):
        run_mcp_server()
        return
    if args.command == "render":
        sys.exit(_cmd_render(args))
    if args.command == "booklet":
        sys.exit(_cmd_booklet(args))


if __name__ == "__main__":
    main()
