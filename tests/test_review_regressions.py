"""Regression coverage for worksheet rendering and answer keys."""

import json
import queue
import re
import subprocess
import sys
import threading
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest
from pydantic import ValidationError

from printgames.core import renderer
from printgames.core.icons import render_icon_svg
from printgames.core.scene_svg import apply_spot_differences, render_scene_element
from printgames.games import produce_booklet, produce_game_from_dict
from printgames.models import BookletSpec, BoggleWordWheelSpec, ColorRegion, CryptogramItem, MazeSpec
from printgames.server import generate_maze


def test_svg_attributes_round_trip():
    family = '"Noto Sans", "Teacher\'s Choice", sans-serif'
    label = 'Read "rain & snow"'
    node = ET.fromstring(render_scene_element(dict(type="text", text=label, font_family=family, weight="bold")))
    assert node.text == label
    assert node.get("font-family") == family
    assert node.get("font-weight") == "bold"
    assert family not in node.get("style", "")

    value = 'a"b & c'
    circle = ET.fromstring(render_scene_element(dict(type="circle", fill=value, dash=value)))
    assert circle.get("fill") == circle.get("stroke-dasharray") == value
    icon = ET.fromstring(render_icon_svg("star", stroke=value))
    assert icon.get("stroke") == value


def test_cryptogram_per_quote_decoders_and_non_ascii(tmp_path):
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    spec = dict(
        game_type="cryptogram", title="Two quotes", instructions="Decode each quote using its own alphabet.",
        show_letter_frequency=True, output_format="html", output_path=str(tmp_path / "quotes"),
        puzzles=[
            dict(plaintext="AAAAAAAAAA café ß", attribution="José", hint_letters=["A"],
                 custom_cipher_map=dict(zip(alphabet, alphabet[1:] + alphabet[:1]))),
            dict(plaintext="AAAA BBBBBB!", custom_cipher_map=dict(zip(alphabet, alphabet[2:] + alphabet[:2]))),
        ],
    )
    path = produce_game_from_dict(spec).output_paths["html"]
    html = Path(path).read_text()
    assert ">é</span>" in html and ">ß</span>" in html
    for n, expected in enumerate([{"B": 11, "K": 1}, {"C": 4, "D": 6}], start=1):
        tracker = html.split(f"Quote #{n} Decoder Scratchpad")[1].split("</div></div></div>")[0]
        values = dict(re.findall(r">([A-Z])</div>\s*<div[^>]*></div>\s*<div[^>]*>(\d+)</div>", tracker))
        for key, count in expected.items():
            assert int(values[key]) == count
    with pytest.raises(ValidationError, match="single A-Z"):
        CryptogramItem(plaintext="A lovely café.", hint_letters=["é"])


def test_boggle_validates_paths_including_qu_tiles():
    grid = [["Qu", "I", "T", "S"], list("ABER"), list("HOLD"), list("FMNP")]
    spec = dict(title="Word grid", instructions="Trace adjacent letters to form words.",
                mode="boggle_grid", grid=grid, sample_words=["QUIT", "QUITE", "TIE", "TIER", "ITS", "HOLD"])
    assert BoggleWordWheelSpec(**spec).grid[0][0] == "QU"
    for word in ["QIT", "QUIP", "TIT", "IS", "ZOO"]:
        with pytest.raises(ValidationError):
            BoggleWordWheelSpec(**(spec | {"sample_words": [word, *spec["sample_words"]]}))
    with pytest.raises(ValidationError, match="tile"):
        BoggleWordWheelSpec(**(spec | {"grid": [["TH", *grid[0][1:]], *grid[1:]]}))


def test_moved_svg_path_and_marker():
    base = [{"id": "road", "type": "path", "d": "m45,30 q10 5 20 0"}]
    change = dict(number=1, target_id="road", change_type="move", params=dict(dx=10, dy=-3))
    moved, markers = apply_spot_differences(base, [change, change | {"number": 2}])
    assert ET.fromstring(render_scene_element(moved[0])).get("transform") == "translate(20.00,-6.00)"
    assert [(m["x"], m["y"]) for m in markers] == [(55, 27), (65, 24)]
    assert render_scene_element(base[0]).startswith("<path")


def test_path_regions_require_a_label_point():
    region = dict(shape_type="path", d="M40 40h20v20z", color_number=1)
    for point in [{}, {"label_x": 50}, {"label_y": 45}]:
        with pytest.raises(ValidationError, match="label_x and label_y"):
            ColorRegion(**region, **point)
    assert ColorRegion(**region, label_x=50, label_y=45).label_x == 50


@pytest.mark.parametrize("collate", [True, False])
def test_paginated_toc_points_to_actual_pages(tmp_path, collate):
    games = [dict(game_type="maze", title=f"Activity {i:02}", instructions="Find the path through the maze.",
                  cols=6, rows=6) for i in range(40)]
    book = BookletSpec(booklet_title="Club booklet", games=games, collate_answer_keys_at_end=collate,
                       output_format="html", output_path=str(tmp_path / "booklet"))
    result = produce_booklet(book)
    sections = Path(result.output_paths["html"]).read_text().split('<section class="page">')[1:]
    contents = [s for s in sections if 'class="game-title" style="margin-top:2mm;">Table of Contents' in s]
    assert len(contents) >= 2
    toc = "".join(contents)
    for i, game in enumerate(games):
        page = 2 + len(contents) + i * (1 if collate else 2)
        assert f'<h1 class="game-title">{game["title"]}</h1>' in sections[page - 1]
        assert re.search(rf'>{i+1:02d}\.</span>\s*<div[^>]*><b>{game["title"]}</b>.*?>p\. {page}</span>', toc)
    if collate:
        assert 'Answer Keys</span>' in contents[-1]
        assert f'>p. {2 + len(contents) + len(games)}</span>' in contents[-1]
    else:
        assert 'Answer Keys</span>' not in toc


@pytest.mark.parametrize(("pages", "clipped", "fit"), [(2, [], True), (2, [1], False), (2, None, None),
                                                        (1, [], False), (None, [], None)])
def test_mcp_fit_requires_both_checks(tmp_path, monkeypatch, pages, clipped, fit):
    monkeypatch.setattr(renderer, "_render_html_to_pdf", lambda *args: clipped)
    monkeypatch.setattr(renderer, "_inspect_pdf_pages", lambda path: pages)
    result = generate_maze(MazeSpec(title="Small maze", instructions="Trace a path to the exit.",
                                    output_path=str(tmp_path / "maze.pdf")))
    assert result["fit_verified"] is fit
    if clipped:
        assert "clipped on page(s) 1" in " ".join(result["warnings"])


def test_previews_only_return_current_render(tmp_path, monkeypatch):
    pdf = tmp_path / "game[one].pdf"
    previous_answer = tmp_path / "game[one]-2.png"
    previous_answer.touch()
    monkeypatch.setattr(renderer.shutil, "which", lambda _: "pdftoppm")

    def convert(args, **kwargs):
        Path(args[-1] + "-1.png").write_bytes(b"current page")
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(renderer.subprocess, "run", convert)
    assert renderer._render_pdf_previews(pdf) == [str(tmp_path / "game[one]-1.png")]


def test_pdf_fit_flags_clipping_with_correct_page_count(tmp_path):
    # Even the mandatory header cannot fit this valid, very small sheet.
    result = generate_maze(MazeSpec(
        title="A long printed maze title " * 3,
        instructions="Read all of these instructions carefully before playing. " * 7,
        page_size="custom", custom_width_mm=80, custom_height_mm=80, margin_mm=16,
        output_path=str(tmp_path / "dense.pdf"),
    ))
    assert result["verified_pdf_pages"] == result["expected_pages"]
    assert result["fit_verified"] is False
    assert any("clipped on page(s) 1" in warning for warning in result["warnings"])


def test_rebus_clue_clipped_by_svg_viewport(tmp_path):
    clue = {"type": "text", "text": "THIS CLUE MUST BE VISIBLE", "x": 238,
            "y": 70, "align": "left", "font_size": 28}
    card = {"answer": "Visible clue", "elements": [clue]}
    result = produce_game_from_dict(dict(
        game_type="rebus", title="Rebus clues", instructions="Read the clues in both pictures.",
        puzzles=[card, card], output_path=str(tmp_path / "rebus.pdf"),
    ))
    assert result.verified_pdf_pages == result.expected_pages == 2
    assert result.fit_verified is False
    assert "Content is clipped on page(s) 1." in result.warnings


def test_pdf_retries_another_browser_after_failed_launch(tmp_path, monkeypatch):
    monkeypatch.setattr(renderer, "_chrome_binaries", lambda: ["first", "second"])
    calls = []

    def launch(args, **kwargs):
        calls.append(args[0])
        if "--dump-dom" in args:
            return subprocess.CompletedProcess(args, 0, '<body data-printgames-fit="1:">', "")
        output = Path(next(arg.split("=", 1)[1] for arg in args if arg.startswith("--print-to-pdf=")))
        if args[0] == "first":
            output.write_bytes(b"partial")
            raise subprocess.TimeoutExpired(args, 60)
        assert not output.exists()
        output.write_bytes(b"complete")
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(renderer.subprocess, "run", launch)
    target = tmp_path / "print.pdf"
    assert renderer._render_html_to_pdf("<body></body>", target, 1) == []
    assert calls == ["first", "second", "second"]
    assert target.read_bytes() == b"complete"


@pytest.mark.parametrize("output_format", ["pdf", "both"])
def test_pdf_failure_preserves_printable_worksheet(tmp_path, monkeypatch, output_format):
    monkeypatch.setenv("PRINTGAMES_CHROME", str(tmp_path / "missing-chrome"))
    target = tmp_path / "garden.pdf"
    target.write_bytes(b"previous PDF")
    sibling = target.with_suffix(".html")
    sibling.write_text("previous HTML")
    with pytest.raises(renderer.PdfExportError, match="Print-ready HTML") as error:
        produce_game_from_dict(dict(
            game_type="maze", title="Garden maze", instructions="Trace a path to the exit.",
            output_format=output_format, output_path=str(target),
        ))
    if output_format == "pdf":
        assert sibling.read_text() == "previous HTML"
        recovery, = tmp_path.glob("garden-*.html")
    else:
        recovery = sibling
    assert str(recovery) in str(error.value)
    assert "Garden maze" in recovery.read_text()
    assert target.read_bytes() == b"previous PDF"


def test_stdio_handshake_with_input_open():
    request = {
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {
            "protocolVersion": "2025-11-25", "capabilities": {},
            "clientInfo": {"name": "printgames-test", "version": "1"},
        },
    }
    with subprocess.Popen(
        [sys.executable, "-c", "from printgames.server import main; main()"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
    ) as server:
        replies = queue.Queue()
        # Keep stdin open until the response arrives, as a real MCP client does.
        reader = threading.Thread(target=lambda: replies.put(server.stdout.readline()), daemon=True)
        reader.start()
        try:
            server.stdin.write(json.dumps(request) + "\n")
            server.stdin.flush()
            response = json.loads(replies.get(timeout=10))
            assert response["id"] == 1
            assert response["result"]["serverInfo"]["name"] == "printgames"
            server.stdin.close()
            assert server.wait(timeout=5) == 0
        finally:
            if server.poll() is None:
                server.kill()
            reader.join(timeout=5)
