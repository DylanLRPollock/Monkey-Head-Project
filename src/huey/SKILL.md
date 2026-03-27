---
name: text-cleanup
description: extract text from uploaded files and convert raw, unformatted, or partially corrupted text into readable output using preserve, correct, or augmented modes. use when chatgpt needs to clean up notes, transcripts, articles, emails, ocr output, copied passages, or similar text from txt, pdf, md, json, and related formats, while preserving order and meaning and marking corrections inline when changes are made.
---

# Annotated Text Cleanup

Use this skill to turn raw text into a clean, readable structure without losing the source. Preserve order and meaning at all times. Apply the selected mode consistently and mark any word-level or phrase-level correction inline.

## Select the mode

Default to **augmented** mode unless the user explicitly asks for another mode.

### Preserve mode
Preserve original wording, grammar, spelling, tone, and order. Improve readability through structure only.

### Correct mode
Preserve meaning, tone, and order, but correct grammar, spelling, punctuation, casing, and formatting for readability.

### Augmented mode
Preserve original wording and tone as much as possible, while allowing minimal corrections only where clearly needed for readability, context, or accuracy.

## Process the file

1. Accept a text-bearing file such as `.txt`, `.pdf`, `.md`, `.json`, or a similar format.
2. Extract the text from the file.
3. If the file contains little or no extractable text, say so clearly.
4. If extraction is partial, visibly corrupted, or incomplete, preserve what was recovered and note the limitation.
5. Format the extracted text according to the selected mode.
6. Generate output files in `.txt` and `.pdf` by default.
7. Generate additional formats such as `.md` or `.json` only when explicitly requested.
8. Name the output files from the original filename unless the user provides a different document name.
9. Provide download links for all generated files.

## Apply formatting rules

### In all modes
- Preserve the original order of the content.
- Do not paraphrase.
- Do not summarize.
- Do not add new information.
- Break text into paragraphs where naturally appropriate.
- Use paragraph breaks for topic changes, speaker changes, sentence grouping, or obvious structural separation.
- Preserve identifiable headings, lists, labels, and section divisions.
- Do not merge unrelated sections.
- Preserve meaning even when improving readability.

### In preserve mode
- Do not rewrite.
- Do not replace words.
- Do not normalize dialect, slang, or tone.
- Add only the minimum punctuation needed for readability.
- Preserve grammar and spelling exactly as written.
- If an apparent original error should be flagged for clarity, keep it and mark it with `[sic]`.
- If a span is clearly malformed, broken, or unreadable and cannot be safely interpreted, keep it and mark it with `[ERROR]`.

### In correct mode
- Correct grammar, spelling, punctuation, casing, and obvious OCR mistakes.
- Preserve the original meaning, tone, and sequence of ideas.
- Do not perform stylistic rewriting beyond what is needed for correctness and readability.
- Do not remove substantive content.
- Remove only obvious mechanical duplication or extraction artifacts when clearly non-substantive.

### In augmented mode
- Preserve the original wording and tone as much as possible.
- Make only minimal corrections needed to avoid confusion or restore clearly intended meaning.
- Do not perform full rewriting or smoothing.
- If a phrase is too broken to repair confidently, keep it and mark it with `[ERROR]` instead of guessing.

## Mark corrections consistently

In **correct** and **augmented** modes, mark each word-level or phrase-level correction inline using this format:

`corrected text [orig: original text]`

Example:

`the food [orig: good] was delicious`

Use this standard for:
- spelling corrections
- grammar corrections
- obvious wrong-word substitutions
- repaired OCR word fragments
- short phrase repairs

Do **not** use silent word substitution in correct or augmented mode.

## Do not over-mark purely structural cleanup

Do not annotate:
- paragraph breaks
- line-wrap cleanup
- heading spacing
- list indentation
- other purely structural formatting changes

Punctuation-only changes may remain unmarked unless they materially affect interpretation. When punctuation changes meaning or resolve clear ambiguity, mark them if needed for transparency.

## Handle uncertainty carefully

When the intended wording is not clear:
- do not guess aggressively
- prefer preserving the original
- use `[ERROR]` when the text is too damaged to repair confidently

When the wording is clear but incorrect:
- correct it only if the selected mode allows correction
- mark the correction inline using `corrected [orig: original]`

## Output expectations

Produce a readable final document that:
- remains faithful to the source
- clearly reflects the selected mode
- shows marked corrections when corrections are allowed
- uses the original filename by default
- is returned as `.txt` and `.pdf` unless the user requests additional formats
