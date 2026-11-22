"""Generate a six-activity print-only PDF showcase using PrintGames' native exporter."""
from __future__ import annotations

from pathlib import Path

from printgames.games import produce_game_from_dict


def main() -> None:
    output = Path("output/printable-showcase")
    output.mkdir(parents=True, exist_ok=True)
    common = {
        "title": "Classroom Puzzle",
        "instructions": "Complete the puzzle using the clues and information on this sheet.",
        "page_size": "a4",
        "orientation": "portrait",
        "theme": "clean_minimal",
        "ink_saver": True,
        "include_answer_key": True,
        "output_format": "pdf",
    }
    examples = [
        ("word_search", {"title":"Rainforest Word Search",
            "instructions":"Circle each hidden rainforest word and tick it off when you find it.",
            "words":["JAGUAR","CANOPY","MONKEY","TOUCAN"],"grid_size":13,"difficulty":"easy"}),
        ("number_search", {"title":"Find the Number Sequences",
            "instructions":"Find and circle every number sequence in the grid.",
            "numbers":["1203","2410","3062","5137"],"grid_size":13,"difficulty":"medium"}),
        ("crossword", {"title":"Fruit Vocabulary Crossword",
            "instructions":"Read each clue and write the missing fruit word into the grid.",
            "entries":[{"answer":"APPLE","clue":"A crunchy red or green fruit"},
                       {"answer":"PEAR","clue":"A bell-shaped fruit"},
                       {"answer":"GRAPE","clue":"A small fruit growing in bunches"},
                       {"answer":"PEACH","clue":"A fuzzy-skinned stone fruit"}],"grid_size":19}),
        ("kriss_kross", {"title":"Fruit Fill-In Crossword",
            "instructions":"Fit every fruit word into the grid using the word bank.",
            "words":["APPLE","PEAR","GRAPE","PEACH"],"grid_size":19}),
        ("sudoku", {"title":"Six by Six Sudoku",
            "instructions":"Fill each row, column and outlined box with the numbers one to six.",
            "grid_size":6,"difficulty":"medium"}),
        ("nonogram", {"title":"Picture Logic Puzzle",
            "instructions":"Shade squares to match the clues; leave a blank between separate groups.",
            "grid_size":7}),
    ]
    for index, (kind, fields) in enumerate(examples, 1):
        spec = {**common, **fields, "game_type":kind, "seed":3,
                "output_path":str(output / f"{index:02d}_{kind}.pdf")}
        result = produce_game_from_dict(spec)
        assert result.expected_pages == 2, kind
        assert result.verified_pdf_pages == 2, (kind, result.verified_pdf_pages)
        assert result.fit_verified is True, (kind, result.warnings)
        print(f"{kind}: {result.output_paths['pdf']} (fit verified)")


if __name__ == "__main__":
    main()
