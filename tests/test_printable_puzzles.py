"""Regression tests for the six native printable puzzles and MCP contract."""
from __future__ import annotations

from pathlib import Path
import json

import pytest
from pydantic import ValidationError

from printgames.games import GAME_REGISTRY, produce_booklet, produce_game_from_dict, render_game_pages
from printgames.core.pages import resolve_page_spec
from printgames.core.themes import get_theme
from printgames.models import (BookletSpec, WordSearchSpec, CrosswordSpec, SudokuSpec,
                               NonogramSpec)
from printgames.server import (generate_word_search, generate_number_search,
                               generate_crossword, generate_kriss_kross,
                               generate_sudoku, generate_nonogram,
                               list_capabilities)
from printgames.games.printable_engines import (make_search, make_crossword,
                                                make_sudoku, make_nonogram,
                                                _sudoku_count, _nonogram_count)

BASE = {
    'title': 'Printable Practice',
    'instructions': 'Complete the puzzle using the information provided on the worksheet.',
    'page_size': 'a4',
    'theme': 'clean_minimal',
}

SAMPLES = {
    'word_search': {'words': ['TREE', 'BIRD', 'FISH', 'FLOWER'], 'grid_size': 13},
    'number_search': {'numbers': ['1234', '5678', '9087', '2468'], 'grid_size': 13},
    'crossword': {'entries': [
        {'answer': 'APPLE', 'clue': 'A crunchy fruit'},
        {'answer': 'PEAR', 'clue': 'A fruit with a narrow top'},
        {'answer': 'GRAPE', 'clue': 'A fruit that grows in bunches'},
        {'answer': 'PEACH', 'clue': 'A fuzzy fruit'},
    ], 'grid_size': 19},
    'kriss_kross': {'words': ['APPLE', 'PEAR', 'GRAPE', 'PEACH'], 'grid_size': 19},
    'sudoku': {'grid_size': 4, 'difficulty': 'medium'},
    'nonogram': {'grid_size': 5},
}


def spec(kind: str, **extras) -> dict:
    return {**BASE, 'game_type': kind, 'seed': 3, **SAMPLES[kind], **extras}


@pytest.mark.parametrize('kind', sorted(SAMPLES))
def test_registry_and_native_page_contract(kind):
    assert kind in GAME_REGISTRY
    model_cls, renderer, category = GAME_REGISTRY[kind]
    model = model_cls.model_validate(spec(kind))
    page = resolve_page_spec(model.page_size, model.orientation, model.margin_mm)
    pages = renderer(model, page, get_theme(model.theme))
    assert len(pages) == 2
    assert not pages[0].is_answer_key and pages[1].is_answer_key
    assert pages[0].title == model.title
    assert pages[0].instructions == model.instructions
    assert pages[0].body_html and pages[1].body_html
    assert '<table' in pages[0].body_html


@pytest.mark.parametrize('kind', sorted(SAMPLES))
def test_mcp_discovery_and_html_output(kind, tmp_path):
    capabilities = list_capabilities()
    assert capabilities['game_types'][kind]['tool_name'] == 'generate_' + kind
    data = spec(kind, output_format='html', output_path=str(tmp_path / kind),
                include_answer_key=False)
    result = produce_game_from_dict(data)
    assert result.expected_pages == 1
    assert 'html' in result.output_paths
    html = Path(result.output_paths['html']).read_text('utf-8')
    assert 'page-frame' in html
    assert data['title'] in html


def test_direct_mcp_result_shape(tmp_path):
    source = spec('word_search', output_format='html', output_path=str(tmp_path / 'word-search'))
    result = generate_word_search(WordSearchSpec.model_validate(source))
    assert result['status'] == 'ok'
    assert result['game_type'] == 'word_search'
    assert result['expected_pages'] == 2
    assert result['files']['html'].endswith('.html')
    assert 'fit_verified' in result and 'page_dimensions_mm' in result


def test_seeded_word_search_unique_and_reproducible():
    words = ['TREE', 'BIRD', 'FISH', 'FLOWER']
    a = make_search(words, seed=7, size=13)
    b = make_search(words, seed=7, size=13)
    assert a['grid'] == b['grid'] and a['placements'] == b['placements']
    for word, p in a['placements'].items():
        assert ''.join(a['grid'][p['row'] + i*p['dr']][p['col'] + i*p['dc']]
                       for i in range(len(word))) == word


def test_crossword_places_all_clues_without_omissions():
    entries = {'APPLE':'Crunchy fruit','PEAR':'Another fruit','GRAPE':'Small fruit','PEACH':'Fuzzy fruit'}
    result = make_crossword(entries, size=19, seed=3)
    assert set(p['word'] for p in result['entries']) == set(entries)
    assert not result['omitted']
    for p in result['entries']:
        assert ''.join(result['grid'][p['row']+i*p['dr']][p['col']+i*p['dc']]
                       for i in range(len(p['word']))) == p['word']


@pytest.mark.parametrize('size', [4, 6, 9])
def test_sudoku_has_one_solution(size):
    puzzle = make_sudoku(size=size, seed=4)
    assert _sudoku_count([row[:] for row in puzzle['grid']],
                         puzzle['block_rows'], puzzle['block_cols']) == 1


@pytest.mark.parametrize('size', [5, 7])
def test_nonogram_has_one_solution(size):
    p = make_nonogram(size=size, seed=3)
    assert _nonogram_count([tuple(x) for x in p['row_clues']],
                           [tuple(x) for x in p['col_clues']]) == 1


def test_bad_crossword_grid_rejected():
    with pytest.raises(ValidationError):
        CrosswordSpec.model_validate(spec('crossword', grid_size=12))


def test_pdf_output_uses_original_export_pipeline(tmp_path):
    data = spec('sudoku', output_format='pdf', output_path=str(tmp_path / 'sudoku.pdf'))
    result = produce_game_from_dict(data)
    assert result.expected_pages == 2
    assert result.verified_pdf_pages == 2
    assert result.fit_verified is True
    assert not result.warnings


def test_booklet_compiles_new_activities(tmp_path):
    book = BookletSpec(
        booklet_title='Printable Puzzle Pack', page_size='a4', theme='clean_minimal',
        output_format='html', output_path=str(tmp_path / 'booklet.html'),
        games=[spec('word_search'), spec('sudoku')],
    )
    result = produce_booklet(book)
    assert result.expected_pages == 6  # cover + TOC + 2 puzzles + 2 keys
    assert Path(result.output_paths['html']).exists()