# ═══════════════════════════════════════════════════════════════
# prompts.py  –  LLM prompt templates for lecture note generation
# ═══════════════════════════════════════════════════════════════
#
# You can freely edit the prompts below to adapt the output style
# to your personal note-taking preferences.
#

# ── System prompt: sets the role and output contract ────────────

SYSTEM_PROMPT = """You are an expert academic assistant specialized in transforming raw lecture transcripts into clear, structured, study-ready notes.

Your output must always be a single, well-formed Markdown document.

Formatting rules:
- Use ## for main sections, ### for sub-topics
- Use **bold** for key terms when first introduced
- Use > blockquotes for important definitions
- Use numbered lists for sequential steps or proofs
- Use bullet lists for enumerations
- Use LaTeX math notation with $...$ (inline) and $$...$$ (block) for any formulas
- Use fenced code blocks with language tag for any code or pseudocode
- Add a ⚠️ callout line for common misconceptions or warnings explicitly mentioned
- Add a 💡 callout line for insights or intuitions explicitly highlighted by the professor

Never invent content. Only structure and clarify what is present in the transcript, using the same words 
and examples made by the professor. If something is not explicitly stated in the transcript, do not add it.
If a section of the transcript is unclear or inaudible, note it with [unclear] rather than guessing.
"""


# ── User prompt template ─────────────────────────────────────────
# {course_hint}  → filled with --course argument (or empty string)
# {style_hint}   → filled with --style argument
# {transcript}   → filled with the actual transcript text

USER_PROMPT_TEMPLATE = """Below is a verbatim transcript of a university lecture.{course_hint}

Your task is to produce a complete set of structured study notes following the style: **{style}**.

--- TRANSCRIPT START ---
{transcript}
--- TRANSCRIPT END ---

Generate the full Markdown notes document now.
"""


# ── Style descriptions sent to the LLM ──────────────────────────

STYLES = {
    "cornell": """Cornell Note-Taking Style.
Structure the document as follows:
1. **Header**: Title, date placeholder, course name
2. **Main Notes** (right column equivalent): Full content organized by topic with all details, examples, formulas
3. **Cue Column** (## Cues & Questions section): A list of short questions or keywords that test recall of the main notes
4. **Summary** (## Summary section): A concise 5-10 line paragraph summarizing the entire lecture
""",

    "outline": """Hierarchical Outline Style.
Structure the document as a clean hierarchical outline:
- H2 for main topics
- H3 for sub-topics
- H4 for details and examples
Include all key terms bolded, formulas in LaTeX, and add a ## Key Takeaways section at the end.
""",

    "mindmap-md": """Mind Map in Markdown Style.
Represent the lecture as a nested bullet-point mind map rooted at the lecture topic.
Each branch represents a concept, sub-concept, or relationship.
Use indentation depth to show hierarchy (max 4 levels).
Append a ## Glossary section with brief definitions of all key terms.
""",

    "flashcard": """Flashcard Generation Style.
Produce a series of Q&A flashcard pairs covering all important concepts in the lecture.
Format each card as:

---
**Q:** [question]
**A:** [answer]

---

Group cards under ## [Topic] headers.
Append a ## Summary section at the very end.
""",

    "deep": """Deep Study Notes Style (default).
Produce comprehensive notes with the following sections:
## Overview
## Key Concepts  (one ### subsection per concept, with definition, explanation, examples)
## Important Formulas / Theorems  (if any)
## Examples Worked in Lecture  (if any)
## Common Pitfalls  (⚠️ warnings from the transcript)
## Key Insights  (💡 moments from the transcript)
## Summary
## Review Questions  (5-10 self-test questions)
""",
}
