# AI Operating Manual — PrintGames MCP

This guide instructs AI assistants on how to communicate with the **PrintGames MCP Server** to produce gorgeous, mathematically accurate, strictly page-fitted printable games (PDF and HTML).

---

## 1. Core Principle: The AI Owns the Creative Content & Context

The PrintGames server is a **precision typesetting, vector-illustration, and print-layout engine**. It does **not** invent filler text or generic trivia. As the calling AI, you MUST provide complete, thoughtful, audience-appropriate context on every tool call:

1. **Clear Editorial Framing**:
   - `title`: Memorable, thematic title.
   - `subtitle`: Optional flavor line (e.g., *"A cozy autumn brain-teaser"*).
   - `instructions`: Tailored, crystal-clear how-to-play rules written for the target audience (e.g., 7-year-olds vs. adult dinner-party guests).
   - `difficulty`: `easy`, `medium`, `hard`, `expert`, or `all_ages`.
   - `author_credit`: Optional footer attribution (e.g., *"Sunday Puzzle Club"*, *"Ms. Rivera's 4th Grade"*).
2. **Explicit Page Geometry & Aesthetic Styling**:
   - `page_size`:
     - `letter` (8.5 × 11 in) — Standard US home printing
     - `a4` (210 × 297 mm) — Standard international printing
     - `a5` (148 × 210 mm) or `half_letter` (5.5 × 8.5 in) — Travel booklets / half-sheets
     - `kdp_6x9` (6 × 9 in) or `kdp_8x10` (8 × 10 in) — Paperback & activity books
     - `square_8x8` (8 × 8 in) — Square visual puzzles & mazes
     - `legal` (8.5 × 14 in) or `a3` (297 × 420 mm) — Extra-large / poster sheets
     - `custom` — Requires `custom_width_mm` and `custom_height_mm` (80–600 mm)
   - `orientation`: `portrait` or `landscape`
   - `theme`:
     - `editorial_classic` — Warm magazine press (charcoal + terracotta crimson)
     - `botanical_ink` — Serene forest green + sage + warm cream
     - `playful_studio` — Friendly kids/family navy + coral + sky tint
     - `vintage_press` — Broadsheet espresso + antique ochre
     - `clean_minimal` — Crisp Swiss monochrome slate
     - `ocean_breeze` — Maritime harbor teal + seafoam
   - `ink_saver`: Set `true` when the user wants black-and-white / toner-saving home printing.
3. **Always Discover Capabilities First**:
   - Call `list_capabilities` (or read `printgames://icons`, `printgames://page-sizes`, `printgames://themes`) before composing vector scenes so every `icon_name` and `scene_element_type` is valid.
4. **Always Verify Output Fit**:
   - If PDF export fails and the error includes a print-ready HTML path, use an available browser printing tool to finish the requested PDF at the intended destination. Honor the CSS page size, enable background graphics, and disable browser headers and footers. Check the resulting page count and inspect the layout before reporting fit.
   - Inspect the returned JSON: confirm `fit_verified == true` (content fit and PDF page count) and `warnings == []`.
   - When designing complex custom artwork (Spot the Difference, Hidden Pictures, Dot-to-Dot, Color-by-Number, Rebus), set `render_preview_png: true` to visually inspect the rendered pages if your client supports viewing images.

---

## 2. Game-by-Game Requirements & Quality Rules (All 16 Games)

### Category 1: Word & Letter Puzzles

#### 1. Cryptograms (`generate_cryptogram`)
- Provide 1–3 rich, witty, or thematic `puzzles` per page (1–2 for compact pages like `a5`/`kdp_6x9`; up to 3 on `letter`/`a4`).
- Each puzzle requires `plaintext` (12–280 chars), optional `attribution`, `hint_letters` (give 1–3 hints for `easy`, 0 for `hard`), and a `seed` (or explicit 26-letter `custom_cipher_map`).
- Each quote has its own cipher and decoder. A–Z letters are encrypted and other characters are printed as supplied. Set `show_alphabet_tracker: true` for player convenience; enable `show_letter_frequency: true` for harder quotes.

#### 2. Word Ladders (`generate_word_ladder`)
- Provide 1–4 `ladders` per page.
- **Strict validation**: Every word in `solution_steps` MUST be a real English word of the exact same length, starting with `start_word` and ending with `end_word`, changing **exactly 1 letter** per step.
- Verify every single adjacent pair letter-by-letter before calling the tool!
- Provide `step_clues` (length = `len(solution_steps) - 2`) to make themed or kid-friendly ladders much more enjoyable.

#### 3. Anagrams & Word Scrambles (`generate_anagram_scramble`)
- Provide 4–20 `items` (8–12 is ideal for `letter`/`a4`; 6–10 for `a5`).
- For classic Jumble-style puzzles, supply `circled_indices` (0-based indices ignoring spaces) on items AND a `bonus_phrase` (`{prompt, answer}`).
- **Strict validation**: The collected circled letters across all items MUST be an exact anagram of `bonus_phrase.answer`. Verify letter counts carefully!

#### 4. Acrostics (`generate_acrostic`)
- Provide `quote` (recommended 45–125 letters for crisp single-page sizing), `author_and_source`, and 6–20 `clues` (`{label, clue, answer}`).
- **Strict validation**: The exact multiset of letters across all `clues[].answer` MUST equal the exact multiset of letters in `quote`!
- **How to construct a valid Acrostic reliably**:
  1. Count every A–Z letter in `quote` (e.g., 5 A's, 8 E's, 4 T's...).
  2. Partition those exact letters into real clue answer words, crossing off each letter as you use it until ZERO letters remain.
  3. Optionally make the first letters of `clues[].answer` spell `author_and_source` and set `require_first_letters_spell_author: true`.

#### 5. Boggle-Style Grids & Word Wheels (`generate_boggle_word_wheel`)
- Choose `mode: "boggle_grid"` (provide a 4×4 or 5×5 `grid`; `"Qu"` is supported!) OR `mode: "word_wheel"` (provide `center_letter` + 6–10 `outer_letters` + optional `pangram_word`).
- Ensure rich vowel/consonant balance (at least 30–40% vowels).
- Provide 10–40 verified `sample_words` for the Answer Key. For `word_wheel`, EVERY sample word MUST contain `center_letter` and only use letters present in the wheel (respecting duplicates).

#### 6. Rebus Puzzles (`generate_rebus`)
- Provide 2–12 cards (6 or 9 cards look stunning on `letter`/`a4`).
- Each card uses a **`240 × 150` logical canvas** (`x` in `0..240`, `y` in `0..150`, center at `(120, 75)`).
- Combine `type: "text"` (with `font_size`, `weight`, `color`, `rotate`, `vertical`, `letter_spacing`, `strikethrough`, `underline`, `italic`), `type: "icon"` (from `built_in_icons`), and geometric primitives (`line`, `rect`, `circle`, `polygon`, `path`) to craft clever spatial idioms!
  - Example — *"Head over heels"*: `HEAD` at `(120, 52)`, horizontal divider `line` from `(55, 75)` to `(185, 75)`, `HEELS` at `(120, 98)`.
  - Example — *"Reading between the lines"*: two parallel lines at `y=52` and `y=98`, `READING` tucked cleanly at `(120, 75)`.
  - Example — *"Once in a blue moon"*: `ONCE` inside a blue `moon` icon or `IN A BLUE` + `moon` icon.
- Always supply clear `answer` and `explanation` for the Answer Key.

---

### Category 2: Visual & Spatial Activities

#### 7. Mazes (`generate_maze`)
- Choose `shape`: `"rectangular"`, `"circular"`, or `"hexagonal"`.
- Pick dimensions to suit audience & page size:
  - Kids / Easy: `cols=10, rows=12` (or `rings=5`)
  - Medium: `cols=16, rows=20` (or `rings=8`)
  - Challenging: `cols=24, rows=30` (or `rings=12`, or `algorithm="braid"` for loops!)
- Add narrative immersion with `story_prompt`, thematic `start_label`/`end_label`, and matching `start_icon`/`end_icon` (e.g., `rocket` → `moon`, `boat` → `treasure`, `bee` → `flower`).

#### 8. Spot the Difference (`generate_spot_the_difference`)
- Default canvas: `480 × 300`. Use `layout: "stacked"` in `portrait` or `layout: "side_by_side"` in `landscape` (or `"auto"`).
- Compose a layered, lively vector scene in `base_elements` (12–45 elements):
  - Back layer: `scenic_mountain`, `scenic_cloud`, `scenic_tree`, `scenic_pine`, `scenic_house`, `scenic_fence`, `scenic_bush`, `scenic_wave`.
  - Foreground details: `icon` elements (`sun`, `bird`, `cat`, `flower`, `butterfly`, `boat`, `apple`, `lantern`, `hat`, `star`, etc.) and custom shapes.
  - Give every element that could mutate a clear, unique `id` (e.g., `"roof_bird"`, `"left_cloud"`, `"cottage_door"`).
- Define 5–10 varied `differences` using `remove`, `add`, `recolor`, `move`, `resize`, `rotate`, `flip_x`, `replace_icon`, and `change_text`.
- **Tip**: Avoid overlapping differences at the same `(x, y)` so Answer Key circles remain clean and distinct!

#### 9. Hidden Pictures / I Spy (`generate_hidden_pictures`)
- Default canvas: `620 × 420`.
- Build a rich, dense line-art or lightly tinted scene in `background_elements` (20–60 elements: trees, shelves, hills, waves, clouds, bushes, fences, houses, geometric texture lines) so hidden objects have genuine visual camouflage.
- Hide 6–12 `hidden_objects` across all four quadrants of the scene. Vary `rotate` (e.g., `-35`, `70`, `145`), `size` (`18`–`34`), `flip_x`, and `stroke` so each object blends naturally into background silhouettes without being microscopic or clipped off-edge (keep `x` in `30..canvas_width-30`, `y` in `30..canvas_height-30`).

#### 10. Dot-to-Dot (`generate_dot_to_dot`)
- Default canvas: `500 × 520`.
- Plot recognizable silhouette coordinates in `paths` (12–50 dots total). Keep adjacent dots spaced at least 22–30 canvas units apart so numbers are spacious and effortless to connect.
- Keep all coordinates safely inside `[35, canvas_width-35] × [35, canvas_height-35]` so labels never clip at the border.
- Add charming `background_elements` (e.g., an eye circle, water waves, ground horizon, smile curve) that bring the silhouette to life once connected!
- Support educational variants with `sequence_type`: `"numbers"`, `"uppercase_letters"` (≤26 dots), `"lowercase_letters"`, or `"skip_count"` (e.g., count by 2s, 5s, or 10s).

#### 11. Color-by-Number (`generate_color_by_number`)
- Default canvas: `500 × 480`.
- Define a harmonious 4–10 color `palette` with crisp, distinct hex colors and friendly color names.
- Build a full-bleed or framed geometric/mosaic/stained-glass/illustrated composition in `regions` (10–60 closed polygons, circles, ellipses, rects, or SVG paths). For path regions, supply both `label_x` and `label_y` at a point inside the region.
- Ensure every region is large enough (at least ~28×28 canvas units) for its printed number to sit legibly inside. If a concave polygon's centroid falls outside the shape, provide explicit `label_x` and `label_y`.

---

### Category 3: Multi-Player Pen & Paper Games

#### 12. Dots and Boxes (`generate_dots_and_boxes`)
- Classic quick game: `rows=6, cols=6` with `boards_per_page=2` or `4`.
- Epic single-sheet game: `rows=10, cols=10` (or `12×12`) with `boards_per_page=1`.
- Enable `show_guide_lines: true` for younger players. Customize `player_labels` when the user gives player names!

#### 13. Battleship (`generate_battleship`)
- Use `sheets_per_page=1` in `portrait` for spacious full-page command sheets, OR `sheets_per_page=2` in `landscape` for two cuttable player sheets on a single printed page!
- Customize `theme_flavor`, `defense_grid_label`, `target_grid_label`, and `fleet` to match any theme (e.g., Space Armada, Pirate Ships, Deep Sea Explorers, Classic Navy).

#### 14. Categories / Scattergories (`generate_categories`)
- Write 10–16 creative, non-overlapping, fun `categories` tailored to the theme (e.g., Holiday Party, Road Trip, Sci-Fi Fans, Kids Classroom).
- Choose `rounds` (4–5 in single-sheet portrait; 3–4 if `sheets_per_page=2` in landscape).
- Leave `round_letters` omitted for open letter-die rolling, OR pre-fill tricky/fun letters!

#### 15. Hangman (`generate_hangman`)
- Choose `visual_style`: `"classic_gallows"` OR family/classroom-friendly `"snowman"`, `"flower"`, or `"rocket"`.
- For open tabletop play, omit `pre_filled_puzzles` and choose `games_per_page` (`2` or `4`).
- For host-led quizzes or themed parties, supply `pre_filled_puzzles` matching `games_per_page` — the server automatically creates exact word blanks on Page 1 and a hidden **Host Secret Key** on Page 2!

#### 16. Mad Libs (`generate_mad_libs`)
- Write a genuinely hilarious, vivid 2–4 paragraph `story_template` containing **10–18 blanks** (avoid >20 blanks on compact page sizes so generous handwriting line spacing stays airy).
- Use `{{PART OF SPEECH}}` or `{{PART OF SPEECH|helpful hint}}` (e.g., `{{ADJECTIVE}}`, `{{PLURAL NOUN|something sticky}}`, `{{PAST-TENSE VERB}}`, `{{CELEBRITY OR FICTIONAL CHARACTER}}`).
- Keep `include_word_collector_sheet: true` so the host can ask for words spoiler-free on Page 1 before transferring them to Page 2!

---

## 3. Multi-Game Booklets (`create_game_booklet`)

When the user asks for an activity pack, party bundle, road-trip booklet, or KDP puzzle book:
- Use `create_game_booklet` with 2–40 mixed game objects inside `games` (each object includes `"game_type"` plus its full required fields).
- Set `include_cover: true`, `include_toc: true`, and `collate_answer_keys_at_end: true` for a genuine published-book experience.
- Every game automatically inherits the booklet's `page_size`, `orientation`, `theme`, and `ink_saver` settings.
