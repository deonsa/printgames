"""End-to-end tests for all 16 PrintGames types, strict validation, page-fit, booklet, and MCP server."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from printgames.games import GAME_REGISTRY, produce_booklet, produce_game_from_dict
from printgames.models import (
    AcrosticSpec,
    AnagramScrambleSpec,
    BoggleWordWheelSpec,
    BookletSpec,
    ColorByNumberSpec,
    MadLibsSpec,
    SpotTheDifferenceSpec,
    WordLadderSpec,
)
from printgames.server import (
    create_game_booklet,
    generate_cryptogram,
    generate_maze,
    list_capabilities,
    mcp,
)


def sample_specs(out_dir: Path) -> list[dict]:
    """Rich, realistic specifications covering all 16 game types across multiple page sizes & themes."""
    return [
        # 1. Cryptogram (US Letter, Editorial Classic)
        {
            "game_type": "cryptogram",
            "title": "Wisdom in Cipher",
            "subtitle": "Classic Literary Quotes",
            "instructions": "Each letter in the quotes below has been replaced by a consistent substitute letter. Use word patterns, punctuation, and the A-Z decoder strip to reveal each quote.",
            "difficulty": "medium",
            "page_size": "letter",
            "theme": "editorial_classic",
            "show_alphabet_tracker": True,
            "show_letter_frequency": True,
            "puzzles": [
                {
                    "plaintext": "Curiosity is the wick in the candle of learning.",
                    "attribution": "William Arthur Ward",
                    "hint_letters": ["E", "T"],
                    "theme_clue": "On staying inquisitive",
                    "seed": 11,
                },
                {
                    "plaintext": "Not all those who wander are lost.",
                    "attribution": "J. R. R. Tolkien",
                    "hint_letters": ["O"],
                    "theme_clue": "From Middle-earth",
                    "seed": 22,
                },
            ],
            "output_path": str(out_dir / "01_cryptogram.pdf"),
        },
        # 2. Word Ladders (A4, Botanical Ink)
        {
            "game_type": "word_ladder",
            "title": "Garden Step Ladders",
            "subtitle": "One Letter at a Time",
            "instructions": "Transform the top word into the bottom word by changing exactly one letter per rung. Every rung must be a valid English word.",
            "difficulty": "easy",
            "page_size": "a4",
            "theme": "botanical_ink",
            "ladders": [
                {
                    "label": "Ladder 1: Warm Up",
                    "start_word": "COLD",
                    "end_word": "WARM",
                    "solution_steps": ["COLD", "CORD", "WORD", "WORM", "WARM"],
                    "step_clues": [
                        "A thick string or cable",
                        "A unit of language",
                        "A wiggly garden creature",
                    ],
                },
                {
                    "label": "Ladder 2: Head to Toe",
                    "start_word": "HEAD",
                    "end_word": "TAIL",
                    "solution_steps": ["HEAD", "HEAL", "TEAL", "TELL", "TALL", "TAIL"],
                    "step_clues": [
                        "Recover from an injury",
                        "Blue-green color",
                        "Share a story",
                        "High in stature",
                    ],
                },
            ],
            "output_path": str(out_dir / "02_word_ladder.pdf"),
        },
        # 3. Anagrams & Word Scrambles (Letter, Playful Studio, with Bonus Phrase!)
        {
            "game_type": "anagram_scramble",
            "title": "Sunday Bakery Jumble",
            "subtitle": "Unscramble the treats & solve the bonus riddle",
            "instructions": "Unscramble each set of letter tiles into a real word. Copy the circled letters into the Bonus Riddle at the bottom and unscramble them for the final punchline!",
            "difficulty": "medium",
            "page_size": "letter",
            "theme": "playful_studio",
            "items": [
                {"answer": "SCONE", "clue": "British tea-time pastry", "circled_indices": [0]},      # S
                {"answer": "FLOUR", "clue": "Milled wheat powder", "circled_indices": [3]},          # U
                {"answer": "GLAZE", "clue": "Shiny sweet topping", "circled_indices": [0]},          # G
                {"answer": "BREAD", "clue": "Baked loaf staple", "circled_indices": [3, 1]},         # A, R
                {"answer": "MAPLE", "clue": "Tree syrup flavor", "circled_indices": [2]},            # P
                {"answer": "ICING", "clue": "Frosted cake coat", "circled_indices": [0]},            # I
                {"answer": "CRUST", "clue": "Golden outer shell", "circled_indices": []},
                {"answer": "YEAST", "clue": "Makes dough rise", "circled_indices": [1]},             # E
            ],
            # Circled letters: S, U, G, A, R, P, I, E -> "SUGAR PIE"
            "bonus_phrase": {
                "prompt": "What did the baker call their favorite sweetheart?",
                "answer": "SUGAR PIE",
            },
            "output_path": str(out_dir / "03_anagram_scramble.pdf"),
        },
        # 4. Acrostic (Letter, Vintage Press)
        # Quote: "TIME FLIES LIKE AN ARROW" -> letters: T I M E F L I E S L I K E A N A R R O W (20 letters)
        # Let's craft a crisp 38-letter quote with exact verified letter multiset!
        # Quote: "READ A GOOD BOOK AND TRAVEL FAR AWAY"
        # Letters: R E A D A G O O D B O O K A N D T R A V E L F A R A W A Y
        # Count: A:7, B:1, D:3, E:2, F:1, G:1, K:1, L:1, N:1, O:4, R:3, T:1, V:1, W:1, Y:1 (29 letters)
        # Clue answers (must sum to exact same 29 letters):
        # A: "ABOARD" (A:2, B:1, D:1, O:1, R:1) -> rem: A:5, D:2, E:2, F:1, G:1, K:1, L:1, N:1, O:3, R:2, T:1, V:1, W:1, Y:1
        # B: "WOODLAND" (W:1, O:2, D:2, L:1, A:1, N:1) -> rem: A:4, E:2, F:1, G:1, K:1, O:1, R:2, T:1, V:1, Y:1
        # C: "GRAVY" (G:1, R:1, A:1, V:1, Y:1) -> rem: A:3, E:2, F:1, K:1, O:1, R:1, T:1
        # D: "FREAK" (F:1, R:1, E:1, A:1, K:1) -> rem: A:2, E:1, O:1, T:1
        # E: "OATAE" -> wait, let's pick a real word! Rem letters: A, A, E, O, T -> let's adjust quote slightly!
        # Quote: "A GOOD BOOK IS A PORTABLE MAGIC"
        # Letters: A G O O D B O O K I S A P O R T A B L E M A G I C (25 letters)
        # Counts: A:4, B:2, C:1, D:1, E:1, G:2, I:2, K:1, L:1, M:1, O:5, P:1, R:1, S:1, T:1
        # Clues:
        # A: "BLOOM" (B:1, L:1, O:2, M:1) -> rem: A:4, B:1, C:1, D:1, E:1, G:2, I:2, K:1, O:3, P:1, R:1, S:1, T:1
        # B: "CARGO" (C:1, A:1, R:1, G:1, O:1) -> rem: A:3, B:1, D:1, E:1, G:1, I:2, K:1, O:2, P:1, S:1, T:1
        # C: "BAKED" (B:1, A:1, K:1, E:1, D:1) -> rem: A:2, G:1, I:2, O:2, P:1, S:1, T:1
        # D: "PATIO" (P:1, A:1, T:1, I:1, O:1) -> rem: A:1, G:1, I:1, O:1, S:1
        # E: "AGIOS" -> tweak! Instead of PATIO + AGIOS, use: rem A:2, G:1, I:2, O:2, P:1, S:1, T:1:
        # D: "PIANO" (no N). What about "IGLOO" (no 2nd L).
        # Let's check rem: A, A, G, I, I, O, O, P, S, T -> "TOGAS" (T,O,G,A,S) + "OPIAI" no.
        # Change D to "GOATS" (G,O,A,T,S) -> rem A, I, I, O, P. Not a clean word.
        # Add "PORTABLE" -> Quote: "BOOKS ARE A UNIQUELY PORTABLE MAGIC" (Stephen King! Famous real quote!)
        # Letters: B O O K S A R E A U N I Q U E L Y P O R T A B L E M A G I C
        # Wait let's keep it super clean and verified programmatically in Python inside the test helper:
        # Quote: "A GOOD BOOK IS A MAGIC PORTAL" -> A G O O D B O O K I S A M A G I C P O R T A L
        # Counts: A:4, B:1, C:1, D:1, G:2, I:2, K:1, L:1, M:1, O:5, P:1, R:1, S:1, T:1 (23 letters)
        # Clues:
        # A: "BLOOM" (B,L,O,O,M)
        # B: "CARGO" (C,A,R,G,O)
        # C: "AUDIO" (no U) -> "RADIO" (no 2nd R)
        # Let's make clues first and build the exact quote!
        # Quote: "BOOKS ARE PORTABLE MAGIC"
        # Letters: B O O K S A R E P O R T A B L E M A G I C (21 letters)
        # Counts: A:3, B:2, C:1, E:2, G:1, I:1, K:1, L:1, M:1, O:3, P:1, R:2, S:1, T:1
        # Clues:
        # A: "BOOK" (B,O,O,K)
        # B: "GRAPE" (G,R,A,P,E)
        # C: "CLIMB" (C,L,I,M,B)
        # D: "ROAST" (R,O,A,S,T)
        # E: "AE" -> make "BOOKS ARE A PORTABLE MAGIC" + "AT SEA"?
        # Wait: B,O,O,K + G,R,A,P,E + C,L,I,M,B + R,O,A,S,T = A:2,B:2,C:1,E:1,G:1,I:1,K:1,L:1,M:1,O:3,P:1,R:2,S:1,T:1 -> missing A,E!
        # So change "BOOK" to "BRAKE" (adds R,A,E removes O,O) or add clue E: "ERA" if quote has extra R!
        # Quote: "BOOKS ARE A TRULY PORTABLE MAGIC" -> let's just check exact words:
        # Words: "BLOOM" + "CARGO" + "BAKED" + "SIGHT" + "PIANO" ->
        # Actually: Quote "BOOKS ARE PORTABLE MAGIC" has 21 letters:
        # A: "BROOM" (B,R,O,O,M)
        # B: "AGILE" (A,G,I,L,E)
        # C: "PACKS" (P,A,C,K,S)
        # D: "BOATER" (B,O,A,T,E,R)
        # Check sum:
        # A: 1+1+1=3 ✓, B: 1+1=2 ✓, C: 1 ✓, E: 1+1=2 ✓, G: 1 ✓, I: 1 ✓, K: 1 ✓, L: 1 ✓, M: 1 ✓, O: 2+1=3 ✓, P: 1 ✓, R: 1+1=2 ✓, S: 1 ✓, T: 1 ✓! EXACT 21/21 MATCH!
        {
            "game_type": "acrostic",
            "title": "Literary Acrostic",
            "subtitle": "Decode the book lover's maxim",
            "instructions": "Answer the clues below and transfer each letter into the matching numbered square in the grid above to reveal a famous quote about reading.",
            "difficulty": "medium",
            "page_size": "letter",
            "theme": "vintage_press",
            "quote": "BOOKS ARE PORTABLE MAGIC.",
            "author_and_source": "Stephen King — On Writing",
            "clues": [
                {"label": "A", "clue": "Long-handled sweeping tool", "answer": "BROOM"},
                {"label": "B", "clue": "Quick and nimble in movement", "answer": "AGILE"},
                {"label": "C", "clue": "Fills a suitcase for travel", "answer": "PACKS"},
                {"label": "D", "clue": "Flat-topped straw hat", "answer": "BOATER"},
            ],
            "output_path": str(out_dir / "04_acrostic.pdf"),
        },
        # 5. Boggle / Word Wheel (Square 8x8, Ocean Breeze)
        {
            "game_type": "boggle_word_wheel",
            "title": "Harbor Word Wheel",
            "subtitle": "Every word must use the center letter",
            "instructions": "Build as many words of 3 or more letters as you can using the letters in the wheel. Every word MUST include the highlighted center letter 'A', and each wheel tile may be used once per word.",
            "difficulty": "medium",
            "page_size": "square_8x8",
            "theme": "ocean_breeze",
            "mode": "word_wheel",
            "center_letter": "A",
            "outer_letters": ["S", "E", "L", "I", "N", "G", "T", "R"],
            "pangram_word": "TRIANGLES",
            "min_word_length": 3,
            "timer_suggestion": "5 Minutes",
            "writing_lines": 30,
            "sample_words": [
                "TRIANGLES", "TRIANGLE", "INTEGRAL", "RELATING", "ALERTING", "ALTERING",
                "SALTING", "STARING", "SEATING", "TEASING", "RANGES", "STRANGE", "GIANTS",
                "TRAINS", "GRAINS", "STAIR", "RAILS", "TRAIL", "GRAIN", "TRAIN", "SLATE",
                "LATER", "STAR", "SAIL", "TALE", "SALE",
            ],
            "output_path": str(out_dir / "05_word_wheel.pdf"),
        },
        # 6. Rebus Puzzles (Letter, Editorial Classic)
        {
            "game_type": "rebus",
            "title": "Visual Wordplay",
            "subtitle": "Decode the 6 hidden idioms",
            "instructions": "Study the placement, size, color, and symbols inside each frame to figure out the familiar English phrase or idiom it represents.",
            "difficulty": "medium",
            "page_size": "letter",
            "theme": "editorial_classic",
            "puzzles": [
                {
                    "answer": "Head over heels",
                    "explanation": "The word HEAD sits directly over the word HEELS.",
                    "elements": [
                        {"type": "text", "text": "HEAD", "x": 120, "y": 50, "font_size": 28, "weight": "900"},
                        {"type": "line", "x1": 55, "y1": 75, "x2": 185, "y2": 75, "stroke_width": 2.5},
                        {"type": "text", "text": "HEELS", "x": 120, "y": 100, "font_size": 28, "weight": "900"},
                    ],
                },
                {
                    "answer": "Reading between the lines",
                    "explanation": "READING is positioned between two horizontal lines.",
                    "elements": [
                        {"type": "line", "x1": 35, "y1": 48, "x2": 205, "y2": 48, "stroke_width": 3},
                        {"type": "text", "text": "READING", "x": 120, "y": 75, "font_size": 24, "weight": "800", "color": "#B54434"},
                        {"type": "line", "x1": 35, "y1": 102, "x2": 205, "y2": 102, "stroke_width": 3},
                    ],
                },
                {
                    "answer": "Once in a blue moon",
                    "explanation": "The phrase ONCE IN A paired with a blue crescent moon.",
                    "elements": [
                        {"type": "text", "text": "ONCE IN A", "x": 92, "y": 75, "font_size": 20, "weight": "800"},
                        {"type": "icon", "icon_name": "moon", "x": 182, "y": 75, "size": 46, "stroke": "#2563EB", "fill": "#93C5FD", "stroke_width": 2.2},
                    ],
                },
                {
                    "answer": "Think outside the box",
                    "explanation": "The word THINK sits outside a drawn square box.",
                    "elements": [
                        {"type": "rect", "x": 45, "y": 40, "width": 84, "height": 70, "rx": 4, "fill": "#FAF7F2", "stroke_width": 2.5},
                        {"type": "text", "text": "THINK", "x": 182, "y": 75, "font_size": 22, "weight": "900", "color": "#B54434"},
                    ],
                },
                {
                    "answer": "Broken heart",
                    "explanation": "A split heart icon with the word HEART.",
                    "elements": [
                        {"type": "icon", "icon_name": "heart", "x": 120, "y": 72, "size": 68, "stroke": "#B54434", "fill": "#FDE8E5", "stroke_width": 2.4},
                        {"type": "polyline", "points": [[120, 44], [112, 62], [128, 76], [116, 98]], "stroke": "#1F2421", "stroke_width": 3},
                    ],
                },
                {
                    "answer": "Standing ovation",
                    "explanation": "STANDING printed vertically (standing up) over OVATION.",
                    "elements": [
                        {"type": "text", "text": "STAND", "x": 68, "y": 75, "font_size": 17, "weight": "900", "vertical": True, "color": "#2B5B6C"},
                        {"type": "text", "text": "OVATION", "x": 152, "y": 75, "font_size": 22, "weight": "900"},
                    ],
                },
            ],
            "output_path": str(out_dir / "06_rebus.pdf"),
        },
        # 7. Maze (A4, Botanical Ink — Circular Polar Maze!)
        {
            "game_type": "maze",
            "title": "The Botanical Labyrinth",
            "subtitle": "Circular Hedge Maze",
            "instructions": "Enter from the top gate and trace a continuous path through the concentric garden hedges to reach the flower pavilion at the center without crossing any walls.",
            "difficulty": "medium",
            "page_size": "a4",
            "theme": "botanical_ink",
            "shape": "circular",
            "rings": 8,
            "algorithm": "recursive_backtracker",
            "seed": 77,
            "start_label": "ENTER",
            "end_label": "BLOOM",
            "end_icon": "flower",
            "story_prompt": "Wind your way inward through the sunlit conservatory hedges to discover the rare golden blossom.",
            "output_path": str(out_dir / "07_maze_circular.pdf"),
        },
        # 8. Spot the Difference (Letter Portrait, Stacked, Playful Studio)
        {
            "game_type": "spot_the_difference",
            "title": "Hilltop Cottage Morning",
            "subtitle": "Compare Picture A and Picture B carefully",
            "instructions": "Circle all 6 subtle differences in Picture B! Check the sky, the cottage roof, the trees, and the garden critters, then check off each number below.",
            "difficulty": "easy",
            "page_size": "letter",
            "theme": "playful_studio",
            "scene_description": "A cheerful cottage on a sunny green hill with pine trees, a picket fence, birds, and flowers.",
            "canvas_width": 480,
            "canvas_height": 270,
            "sky_color": "#E8F4FD",
            "ground_color": "#D7ECD2",
            "horizon_y": 190,
            "base_elements": [
                {"id": "sun", "type": "icon", "icon_name": "sun", "x": 62, "y": 50, "size": 44, "stroke": "#D97706", "fill": "#FDE68A"},
                {"id": "mtn_l", "type": "scenic_mountain", "x": 150, "y": 190, "width": 160, "height": 95, "fill": "#9DB4C0"},
                {"id": "mtn_r", "type": "scenic_mountain", "x": 370, "y": 190, "width": 170, "height": 105, "fill": "#88A2B0"},
                {"id": "cloud_1", "type": "scenic_cloud", "x": 180, "y": 54, "size": 52},
                {"id": "cloud_2", "type": "scenic_cloud", "x": 385, "y": 48, "size": 46},
                {"id": "pine_l", "type": "scenic_pine", "x": 66, "y": 208, "size": 76, "fill": "#2F6F4E"},
                {"id": "tree_r", "type": "scenic_tree", "x": 405, "y": 212, "size": 78, "fill": "#4C956C"},
                {"id": "cottage", "type": "scenic_house", "x": 240, "y": 215, "width": 116, "height": 90, "fill": "#FFF7EB", "roof_fill": "#D45542"},
                {"id": "fence", "type": "scenic_fence", "x": 96, "y": 236, "width": 84, "height": 24, "pickets": 6},
                {"id": "bush_r", "type": "scenic_bush", "x": 342, "y": 230, "size": 36, "fill": "#589D68"},
                {"id": "bird_1", "type": "icon", "icon_name": "bird", "x": 295, "y": 76, "size": 28, "stroke": "#1D2B44", "fill": "#93C5FD"},
                {"id": "flower_1", "type": "icon", "icon_name": "flower", "x": 146, "y": 248, "size": 24, "stroke": "#E05A47", "fill": "#FDE68A"},
                {"id": "cat_1", "type": "icon", "icon_name": "cat", "x": 325, "y": 248, "size": 28, "stroke": "#1D2B44", "fill": "#FDBA74"},
                {"id": "kite_star", "type": "star", "cx": 442, "cy": 96, "r": 12, "fill": "#F59E0B"},
            ],
            "differences": [
                {"number": 1, "target_id": "cottage", "change_type": "recolor", "params": {"roof_fill": "#2D7DD2"}, "description": "Cottage roof changed from red to blue"},
                {"number": 2, "target_id": "bird_1", "change_type": "flip_x", "params": {}, "description": "Flying bird reversed direction"},
                {"number": 3, "target_id": "cloud_2", "change_type": "remove", "params": {}, "description": "Right-side cloud disappeared"},
                {"number": 4, "target_id": "cat_1", "change_type": "replace_icon", "params": {"icon_name": "dog"}, "description": "Garden cat became a dog"},
                {"number": 5, "target_id": "flower_1", "change_type": "move", "params": {"dx": 34, "dy": -6}, "description": "Front flower shifted right"},
                {"number": 6, "target_id": "__add__", "change_type": "add", "params": {"element": {"id": "extra_bfly", "type": "icon", "icon_name": "butterfly", "x": 115, "y": 115, "size": 26, "stroke": "#9333EA", "fill": "#E9D5FF"}}, "description": "A purple butterfly appeared above the pine tree"},
            ],
            "output_path": str(out_dir / "08_spot_the_difference.pdf"),
        },
        # 9. Hidden Pictures (I Spy) (Letter, Botanical Ink)
        {
            "game_type": "hidden_pictures",
            "title": "Enchanted Woodland I Spy",
            "subtitle": "8 disguised curiosities hide in the forest",
            "instructions": "Scan the forest illustration closely to spot all 8 hidden objects listed in the tray below. Circle each one as you find it and tick its box!",
            "difficulty": "medium",
            "page_size": "letter",
            "theme": "botanical_ink",
            "scene_description": "A dense woodland clearing with pines, cottages, hills, clouds, and fences.",
            "canvas_width": 620,
            "canvas_height": 400,
            "background_color": "#FAFDFB",
            "background_elements": [
                {"type": "scenic_mountain", "x": 150, "y": 230, "width": 230, "height": 140, "fill": "#EBF2EE"},
                {"type": "scenic_mountain", "x": 450, "y": 230, "width": 260, "height": 155, "fill": "#E4EFE9"},
                {"type": "scenic_cloud", "x": 115, "y": 62, "size": 68, "fill": "#FFFFFF"},
                {"type": "scenic_cloud", "x": 350, "y": 54, "size": 76, "fill": "#FFFFFF"},
                {"type": "scenic_cloud", "x": 540, "y": 70, "size": 62, "fill": "#FFFFFF"},
                {"type": "rect", "x": 0, "y": 230, "width": 620, "height": 170, "fill": "#EFF6F1", "stroke": "none"},
                {"type": "scenic_pine", "x": 72, "y": 280, "size": 115, "fill": "#D7E8DD"},
                {"type": "scenic_tree", "x": 182, "y": 295, "size": 110, "fill": "#CCE3D4"},
                {"type": "scenic_house", "x": 315, "y": 292, "width": 124, "height": 96, "fill": "#FFFFFF", "roof_fill": "#DCE8E0"},
                {"type": "scenic_pine", "x": 465, "y": 286, "size": 120, "fill": "#D7E8DD"},
                {"type": "scenic_tree", "x": 556, "y": 304, "size": 105, "fill": "#CCE3D4"},
                {"type": "scenic_fence", "x": 42, "y": 360, "width": 160, "height": 30, "pickets": 8, "fill": "#FFFFFF"},
                {"type": "scenic_bush", "x": 248, "y": 358, "size": 52, "fill": "#DCEBE1"},
                {"type": "scenic_bush", "x": 405, "y": 364, "size": 58, "fill": "#DCEBE1"},
                {"type": "scenic_wave", "x": 220, "y": 384, "width": 180, "amplitude": 6, "cycles": 5},
            ],
            "hidden_objects": [
                {"name": "Key", "icon_name": "key", "x": 115, "y": 64, "size": 24, "rotate": -25, "hint": "Inside the left cloud"},
                {"name": "Crown", "icon_name": "crown", "x": 448, "y": 104, "size": 22, "rotate": 12, "hint": "Near the right mountain peak"},
                {"name": "Fish", "icon_name": "fish", "x": 310, "y": 376, "size": 24, "rotate": 0, "hint": "Along the stream waves"},
                {"name": "Teacup", "icon_name": "cup", "x": 184, "y": 242, "size": 22, "rotate": 35, "hint": "Tucked in the leafy tree"},
                {"name": "Crescent Moon", "icon_name": "moon", "x": 546, "y": 70, "size": 22, "rotate": -40, "hint": "Inside the right cloud"},
                {"name": "Bell", "icon_name": "bell", "x": 72, "y": 220, "size": 22, "rotate": 18, "hint": "Hanging in the left pine"},
                {"name": "Apple", "icon_name": "apple", "x": 406, "y": 344, "size": 22, "rotate": -15, "hint": "Nestled in the right bush"},
                {"name": "Envelope", "icon_name": "envelope", "x": 112, "y": 344, "size": 22, "rotate": 8, "hint": "Behind the wooden fence"},
            ],
            "output_path": str(out_dir / "09_hidden_pictures.pdf"),
        },
        # 10. Dot-to-Dot (Letter, Playful Studio — Sailboat!)
        {
            "game_type": "dot_to_dot",
            "title": "Connect the Coastline",
            "subtitle": "Count from 1 to 18 to reveal the picture",
            "instructions": "Start at the highlighted dot #1 and draw straight lines in numerical order to reveal what is sailing across the bay!",
            "difficulty": "easy",
            "page_size": "letter",
            "theme": "playful_studio",
            "subject": "Classic Sailboat",
            "canvas_width": 500,
            "canvas_height": 480,
            "sequence_type": "numbers",
            "solution_fill": "#E8F4FD",
            "paths": [
                {
                    "close_path": True,
                    "points": [
                        {"x": 95, "y": 320},
                        {"x": 130, "y": 385},
                        {"x": 370, "y": 385},
                        {"x": 415, "y": 320},
                        {"x": 270, "y": 320},
                        {"x": 270, "y": 290},
                        {"x": 385, "y": 290},
                        {"x": 345, "y": 215},
                        {"x": 295, "y": 140},
                        {"x": 260, "y": 75},
                        {"x": 260, "y": 48},
                        {"x": 215, "y": 62},
                        {"x": 250, "y": 78},
                        {"x": 245, "y": 145},
                        {"x": 190, "y": 215},
                        {"x": 135, "y": 290},
                        {"x": 245, "y": 290},
                        {"x": 245, "y": 320},
                    ],
                }
            ],
            "background_elements": [
                {"type": "icon", "icon_name": "sun", "x": 85, "y": 82, "size": 46, "stroke": "#D97706", "fill": "#FEF3C7"},
                {"type": "scenic_wave", "x": 40, "y": 412, "width": 420, "amplitude": 9, "cycles": 7, "stroke": "#2D7DD2"},
                {"type": "scenic_wave", "x": 65, "y": 438, "width": 370, "amplitude": 7, "cycles": 6, "stroke": "#60A5FA"},
            ],
            "output_path": str(out_dir / "10_dot_to_dot.pdf"),
        },
        # 11. Color-by-Number (Square 8x8, Clean Minimal — Stained-Glass Sunrise Mountain!)
        {
            "game_type": "color_by_number",
            "title": "Alpine Sunrise Mosaic",
            "subtitle": "Geometric Stained-Glass Coloring",
            "instructions": "Match each numbered section to the Color Palette Key below and fill it in with colored pencils, markers, or watercolors.",
            "difficulty": "all_ages",
            "page_size": "square_8x8",
            "theme": "clean_minimal",
            "subject": "Alpine Sunrise",
            "canvas_width": 500,
            "canvas_height": 420,
            "palette": [
                {"number": 1, "color_name": "Dawn Sky", "hex_color": "#93C5FD"},
                {"number": 2, "color_name": "Warm Peach", "hex_color": "#FDBA74"},
                {"number": 3, "color_name": "Golden Sun", "hex_color": "#FDE047"},
                {"number": 4, "color_name": "Slate Peak", "hex_color": "#64748B"},
                {"number": 5, "color_name": "Snow Cap", "hex_color": "#F8FAFC"},
                {"number": 6, "color_name": "Pine Green", "hex_color": "#34D399"},
                {"number": 7, "color_name": "Lake Teal", "hex_color": "#38BDF8"},
            ],
            "regions": [
                # Sky bands
                {"color_number": 1, "shape_type": "polygon", "points": [[0, 0], [500, 0], [500, 120], [0, 120]], "label_x": 80, "label_y": 55},
                # Extend the peach sky to the foreground. The peaks hide the
                # joins at x=140 and x=365, leaving three separately labeled areas.
                {"color_number": 2, "shape_type": "rect", "x": 0, "y": 120, "width": 140, "height": 160, "label_x": 58, "label_y": 170},
                {"color_number": 2, "shape_type": "rect", "x": 140, "y": 120, "width": 225, "height": 160, "label_x": 245, "label_y": 211},
                {"color_number": 2, "shape_type": "rect", "x": 365, "y": 120, "width": 135, "height": 160, "label_x": 450, "label_y": 170},
                # Rising sun
                {"color_number": 3, "shape_type": "circle", "cx": 250, "cy": 135, "r": 54},
                # Left mountain + snow cap
                {"color_number": 4, "shape_type": "polygon", "points": [[0, 280], [140, 110], [280, 280]], "label_x": 140, "label_y": 235},
                {"color_number": 5, "shape_type": "polygon", "points": [[102, 156], [140, 110], [178, 156], [140, 144]], "label_x": 140, "label_y": 136},
                # Right mountain + snow cap
                {"color_number": 4, "shape_type": "polygon", "points": [[210, 280], [365, 95], [500, 280]], "label_x": 365, "label_y": 230},
                {"color_number": 5, "shape_type": "polygon", "points": [[325, 143], [365, 95], [402, 145], [365, 134]], "label_x": 365, "label_y": 124},
                # Foreground hills & lake
                {"color_number": 6, "shape_type": "polygon", "points": [[0, 280], [180, 280], [140, 420], [0, 420]], "label_x": 72, "label_y": 350},
                {"color_number": 6, "shape_type": "polygon", "points": [[320, 280], [500, 280], [500, 420], [360, 420]], "label_x": 428, "label_y": 350},
                {"color_number": 7, "shape_type": "polygon", "points": [[180, 280], [320, 280], [360, 420], [140, 420]], "label_x": 250, "label_y": 355},
            ],
            "output_path": str(out_dir / "11_color_by_number.pdf"),
        },
        # 12. Dots and Boxes (A5 Compact, Playful Studio, 2 boards)
        {
            "game_type": "dots_and_boxes",
            "title": "Travel Dots & Boxes",
            "subtitle": "Pocket 2-Game Sheet",
            "instructions": "Take turns drawing a single horizontal or vertical line between two adjacent dots. Completing the 4th side of a square claims it with your initial and earns a bonus turn!",
            "difficulty": "all_ages",
            "page_size": "a5",
            "theme": "playful_studio",
            "rows": 7,
            "cols": 9,
            "boards_per_page": 2,
            "player_count": 2,
            "show_guide_lines": True,
            "output_path": str(out_dir / "12_dots_and_boxes.pdf"),
        },
        # 13. Battleship (Letter Landscape, 2 Cuttable Sheets, Ocean Breeze)
        {
            "game_type": "battleship",
            "title": "High Seas Battleship",
            "subtitle": "Cut down the center line for instant 2-player play",
            "instructions": "Secretly draw your 5 ships horizontally or vertically on MY FLEET. Take turns calling coordinates (e.g., B-7) to hunt your opponent's ships on ENEMY WATERS!",
            "difficulty": "all_ages",
            "page_size": "letter",
            "orientation": "landscape",
            "theme": "ocean_breeze",
            "grid_size": 10,
            "sheets_per_page": 2,
            "theme_flavor": "Pacific Fleet Command",
            "output_path": str(out_dir / "13_battleship.pdf"),
        },
        # 14. Categories / Scattergories (Letter Portrait, Editorial Classic)
        {
            "game_type": "categories",
            "title": "Friday Night Categories",
            "subtitle": "Think fast — unique answers win!",
            "instructions": "Roll or pick a letter for the round, set a 3-minute timer, and fill every category with an answer starting with that letter. Unique answers score 1 point; duplicates score 0!",
            "difficulty": "all_ages",
            "page_size": "letter",
            "theme": "editorial_classic",
            "rounds": 4,
            "timer_minutes": 3,
            "categories": [
                "A City or Country",
                "Something in a Kitchen",
                "A Movie Title",
                "An Animal with Four Legs",
                "Something You Pack for Vacation",
                "A Famous Historical Figure",
                "A Breakfast Food",
                "A Musical Instrument",
                "Something Cold",
                "A Fictional Character",
                "A Hobby or Pastime",
                "Something Found at the Beach",
            ],
            "output_path": str(out_dir / "14_categories.pdf"),
        },
        # 15. Hangman (KDP 6x9, Snowman style, 2 pre-filled rounds + Host Key!)
        {
            "game_type": "hangman",
            "title": "Winter Snowman Word Guess",
            "subtitle": "Guess the secret phrase before the snowman is built",
            "instructions": "Guess one letter at a time and cross it off the Letter Bank. Each wrong guess adds one piece to the snowman. Uncover the phrase before 6 wrong guesses!",
            "difficulty": "easy",
            "page_size": "kdp_6x9",
            "theme": "ocean_breeze",
            "games_per_page": 2,
            "visual_style": "snowman",
            "max_wrong_guesses": 6,
            "pre_filled_puzzles": [
                {"category": "Cozy Winter Drink", "secret_word": "HOT CHOCOLATE"},
                {"category": "Outdoor Snow Activity", "secret_word": "SLEDDING HILL"},
            ],
            "output_path": str(out_dir / "15_hangman.pdf"),
        },
        # 16. Mad Libs (Letter, Playful Studio, 2-page Collector + Story!)
        {
            "game_type": "mad_libs",
            "title": "The Great Space Cafeteria Mishap",
            "subtitle": "A Fill-in-the-Blank Comedy",
            "instructions": "Fill in every blank with the matching numbered word from your Word Collector sheet, then read the finished sci-fi disaster out loud!",
            "difficulty": "all_ages",
            "page_size": "letter",
            "theme": "playful_studio",
            "story_title": "Lunch Hour on Station Nebula",
            "illustration_icon": "rocket",
            "include_word_collector_sheet": True,
            "story_template": (
                "Every Tuesday aboard Space Station {{SILLY MADE-UP NAME}}, the crew gathers in the "
                "{{ADJECTIVE}} cafeteria for Captain {{FIRST NAME}}'s famous lunch special. "
                "Today's menu featured steamed {{PLURAL NOUN}} smothered in {{COLOR}} gravy and a side of "
                "crunchy {{FOOD}}.\n\n"
                "Suddenly, the zero-gravity generator began to {{VERB}} {{ADVERB}}! "
                "Within seconds, {{NUMBER}} trays of soup floated past the {{NOUN|something in a room}} "
                "and splashed straight onto our chief robot's {{BODY PART}}.\n\n"
                "\"{{EXCLAMATION}}!\" shouted the pilot, grabbing a giant {{OBJECT}} to scoop up the mess. "
                "In the end, everyone agreed it was the most {{ADJECTIVE}} meal in the entire galaxy."
            ),
            "output_path": str(out_dir / "16_mad_libs.pdf"),
        },
    ]


def test_all_16_games_registered():
    assert len(GAME_REGISTRY) == 16
    caps = list_capabilities()
    assert len(caps["game_types"]) == 16
    assert len(caps["built_in_icons"]) >= 70
    assert len(caps["themes"]) == 6
    assert len(caps["page_sizes"]) == 9


def test_all_16_games_render_pdf_with_exact_page_fit(tmp_path: Path):
    specs = sample_specs(tmp_path)
    assert len(specs) == 16
    seen_types = {s["game_type"] for s in specs}
    assert seen_types == set(GAME_REGISTRY.keys())

    for spec in specs:
        res = produce_game_from_dict(spec)
        pdf_path = Path(res.output_paths["pdf"])
        assert pdf_path.exists() and pdf_path.stat().st_size > 2000
        assert res.warnings == [], f"{spec['game_type']} had warnings: {res.warnings}"
        if res.verified_pdf_pages is not None:
            assert (
                res.verified_pdf_pages == res.expected_pages
            ), f"{spec['game_type']}: expected {res.expected_pages} pages, rendered {res.verified_pdf_pages}"


def test_multi_game_booklet_with_cover_toc_and_collated_keys(tmp_path: Path):
    specs = sample_specs(tmp_path)
    chosen = [specs[0], specs[1], specs[6], specs[13]]  # cryptogram, ladder, maze, categories
    booklet = BookletSpec(
        booklet_title="Weekend Puzzle Companion",
        subtitle="Four Handcrafted Print Games",
        author="PrintGames Press",
        page_size="letter",
        theme="editorial_classic",
        include_cover=True,
        include_toc=True,
        collate_answer_keys_at_end=True,
        games=chosen,
        output_path=str(tmp_path / "weekend_booklet.pdf"),
    )
    res = produce_booklet(booklet)
    assert Path(res.output_paths["pdf"]).exists()
    # Cover (1) + TOC (1) + 4 puzzle pages + 3 answer keys (categories has no answer key) = 9 pages
    assert res.expected_pages == 9
    assert res.verified_pdf_pages == 9
    assert res.warnings == []


def test_ink_saver_and_custom_page_size(tmp_path: Path):
    res = produce_game_from_dict(
        {
            "game_type": "maze",
            "title": "Custom Hex Maze",
            "instructions": "Find your path across the hexagonal honeycomb from start to finish.",
            "page_size": "custom",
            "custom_width_mm": 180,
            "custom_height_mm": 220,
            "theme": "clean_minimal",
            "ink_saver": True,
            "shape": "hexagonal",
            "cols": 11,
            "rows": 13,
            "seed": 55,
            "output_path": str(tmp_path / "hex_custom.pdf"),
        }
    )
    assert res.expected_pages == 2
    assert res.verified_pdf_pages == 2
    assert res.warnings == []


def test_strict_ai_validation_errors():
    # Word ladder changing 2 letters in a single step must fail
    with pytest.raises(ValidationError):
        WordLadderSpec(
            title="Bad Ladder",
            instructions="Change one letter at a time to reach the goal word.",
            ladders=[
                {
                    "start_word": "COLD",
                    "end_word": "WARM",
                    "solution_steps": ["COLD", "WARM", "WARM"],
                }
            ],
        )

    # Acrostic mismatched letter multiset must fail
    with pytest.raises(ValidationError):
        AcrosticSpec(
            title="Bad Acrostic",
            instructions="Fill clues and transfer numbered letters into the quote grid.",
            quote="HELLO WORLD TODAY IS NICE",
            author_and_source="Test Author",
            clues=[
                {"label": "A", "clue": "Wrong letters", "answer": "APPLE"},
                {"label": "B", "clue": "Wrong letters", "answer": "ZEBRA"},
                {"label": "C", "clue": "Wrong letters", "answer": "MANGO"},
                {"label": "D", "clue": "Wrong letters", "answer": "TIGER"},
            ],
        )

    # Anagram bonus phrase mismatch must fail
    with pytest.raises(ValidationError):
        AnagramScrambleSpec(
            title="Bad Jumble",
            instructions="Unscramble each word and use circled letters for the bonus riddle.",
            items=[
                {"answer": "APPLE", "circled_indices": [0]},
                {"answer": "PEACH", "circled_indices": [0]},
                {"answer": "GRAPE", "circled_indices": [0]},
                {"answer": "MANGO", "circled_indices": [0]},
            ],
            bonus_phrase={"prompt": "Bonus", "answer": "ZZZZ"},
        )

    # Word wheel sample word missing center letter must fail
    with pytest.raises(ValidationError):
        BoggleWordWheelSpec(
            title="Bad Wheel",
            instructions="Every word must use the center letter in the hub.",
            mode="word_wheel",
            center_letter="Z",
            outer_letters=["A", "E", "I", "O", "R", "S", "T"],
            sample_words=["STARE", "RATES", "TEARS", "ASTER", "ROAST", "STORE"],
        )

    # Spot the difference targeting missing ID must fail
    with pytest.raises(ValidationError):
        SpotTheDifferenceSpec(
            title="Bad Spot",
            instructions="Spot all the differences between the two drawings.",
            scene_description="A simple scene for validation testing.",
            base_elements=[{"id": f"e{i}", "type": "circle", "cx": 50 + i * 20, "cy": 50, "r": 10} for i in range(8)],
            differences=[
                {"number": 1, "target_id": "nonexistent", "change_type": "remove", "description": "Missing id"},
                {"number": 2, "target_id": "e1", "change_type": "remove", "description": "Remove e1"},
                {"number": 3, "target_id": "e2", "change_type": "remove", "description": "Remove e2"},
                {"number": 4, "target_id": "e3", "change_type": "remove", "description": "Remove e3"},
            ],
        )

    # Color-by-number referencing missing palette color must fail
    with pytest.raises(ValidationError):
        ColorByNumberSpec(
            title="Bad Color",
            instructions="Color every numbered shape using the palette legend below.",
            subject="Test Art",
            palette=[
                {"number": 1, "color_name": "Red", "hex_color": "#FF0000"},
                {"number": 2, "color_name": "Blue", "hex_color": "#0000FF"},
                {"number": 3, "color_name": "Green", "hex_color": "#00FF00"},
            ],
            regions=[
                {"color_number": 9, "shape_type": "circle", "cx": 50, "cy": 50, "r": 20},
                *[{"color_number": 1, "shape_type": "circle", "cx": 80 + i * 20, "cy": 80, "r": 15} for i in range(5)],
            ],
        )

    # Mad Libs with too few blanks must fail
    with pytest.raises(ValidationError):
        MadLibsSpec(
            title="Short Mad Libs",
            instructions="Fill in the blanks and read the story out loud with friends.",
            story_title="Too Few Blanks",
            story_template="Once upon a time there was a {{ADJECTIVE}} {{NOUN}} who walked down the very long cobblestone street every single morning.",
        )


def test_mcp_tool_wrappers_work(tmp_path: Path):
    res = generate_maze(
        spec={
            "title": "MCP Tool Test Maze",
            "instructions": "Guide the rocket from the launchpad to the moon.",
            "shape": "rectangular",
            "cols": 12,
            "rows": 14,
            "start_icon": "rocket",
            "end_icon": "moon",
            "output_path": str(tmp_path / "mcp_maze.pdf"),
        }
        if False
        else __import__("printgames.models", fromlist=["MazeSpec"]).MazeSpec(
            title="MCP Tool Test Maze",
            instructions="Guide the rocket from the launchpad to the moon.",
            shape="rectangular",
            cols=12,
            rows=14,
            start_icon="rocket",
            end_icon="moon",
            output_path=str(tmp_path / "mcp_maze.pdf"),
        )
    )
    assert res["status"] == "ok"
    assert res["fit_verified"] is True
    assert Path(res["files"]["pdf"]).exists()
    assert mcp.name == "printgames"
