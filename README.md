# Sketch2Code AI — Phase 1

**From Hand Drawn Logic to Production Code.**

This is Phase 1 of the FlowForge/Sketch2Code AI build: the landing page, full
authentication, dashboard, and the infinite-canvas flowchart editor with
tablet support, undo/redo, and autosave. It's built so Phase 2 (AI
recognition, code generation, execution simulator, collaboration) plugs in
without rewriting this code.

## Stack

- **Frontend**: React + TypeScript + Vite, Tailwind CSS, Zustand, React
  Query, react-konva (canvas), Framer Motion, React Router
- **Backend**: FastAPI (Python), SQLAlchemy, PostgreSQL, JWT auth (access +
  refresh tokens)
- **Auth**: email/password with bcrypt hashing, email verification,
  forgot/reset password, Google Sign-In endpoint (frontend button ships
  disabled until you add a client ID)

## Project structure

```
sketch2code-ai/
├── backend/
│   ├── app/
│   │   ├── core/        # config, security (JWT/bcrypt), email sending
│   │   ├── db/           # SQLAlchemy engine/session
│   │   ├── models/        # User, Project ORM models
│   │   ├── schemas/      # Pydantic request/response shapes
│   │   └── api/routes/    # auth, users, projects endpoints
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── pages/          # LandingPage, LoginPage, DashboardPage, EditorPage...
    │   ├── components/    # landing/, auth/, dashboard/
    │   ├── canvas/         # CanvasEditor, Toolbar, MiniMap, shapes/
    │   ├── store/          # useAuthStore, useCanvasStore (zustand)
    │   ├── hooks/           # useAutosave, useKeyboardShortcuts
    │   ├── api/              # axios client with auto token refresh
    │   └── types/
    ├── tailwind.config.ts   # design tokens (colors, type, motion)
    └── package.json
```

## Running it locally

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:
- Set `DATABASE_URL` to a real PostgreSQL connection string. Easiest local
  option: `docker run --name s2c-db -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=sketch2code -p 5432:5432 -d postgres:16`
- Generate a real `JWT_SECRET_KEY` (e.g. `python3 -c "import secrets; print(secrets.token_hex(32))"`)

Then:

```bash
uvicorn app.main:app --reload --port 8000
```

Tables are created automatically on first run. API docs at
`http://localhost:8000/docs`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Opens at `http://localhost:5173`. The Vite dev server proxies `/api/*` to
`http://localhost:8000`, so no CORS config needed locally.

## Notable design decisions

- **Autosave**: canvas state debounces to a `PUT /projects/{id}/autosave`
  call 1.5s after the last edit, plus a best-effort `sendBeacon` on tab
  close. `canvas_data` is stored as JSON so Phase 2's AI recognizer, code
  generator, and execution simulator can all read/write the same shape
  without a database migration.
- **Undo/redo**: snapshot-based history in `useCanvasStore`, capped at 60
  steps. Viewport pan/zoom is intentionally excluded from history.
- **Tablet pressure**: the freehand/highlighter tools read `event.pressure`
  from the native Pointer Event on every point and vary stroke width per
  segment in `StrokeShape.tsx`. This works with Huion/XP-Pen/Wacom drivers
  that expose Windows Ink / native pointer pressure in Chrome and Edge.
  Firefox pointer-pressure support varies by OS driver.
- **Google login**: the backend endpoint (`POST /api/auth/google`) is fully
  implemented and verifies real Google ID tokens. The frontend button is
  disabled until you add a Google OAuth client ID and wire up Google
  Identity Services — that requires a credential only you can provision.
- **Email sending**: defaults to a "console" backend that prints
  verification/reset links to the backend terminal, so you can test the
  full flow with zero setup. Set `EMAIL_BACKEND=smtp` and fill in the SMTP
  fields in `.env` to send real emails.

## What's intentionally not in Phase 1

Per the phased plan: AI flowchart recognition, code generation, code→
flowchart, execution simulator, AI explainer/complexity analysis, bug
detector, voice mode, realtime collaboration, and the admin panel. The
dashboard sidebar links to these already, landing on a clearly-labeled
"Phase 2" screen instead of a fake feature — so the app never lies about
what it can currently do.

---

## Phase 2 — Feature 1: AI Flowchart Recognition

Draw a rough flowchart with the freehand pen tool, then hit **Recognize
Sketch** in the editor. The sketch is replaced in place with clean,
editable shapes and connectors.

### How it works

`backend/app/recognition/` — fully deterministic geometry pipeline, no
external calls except for the optional label-OCR step:

1. **`grouping.py`** — clusters raw strokes into spatial components by
   bounding-box proximity (union-find).
2. **`outline_chaining.py`** — finds closed-loop outlines within a
   component, chaining multiple pen-lift strokes (e.g. a rectangle drawn
   as 4 separate sides) into one boundary via endpoint-cluster graph +
   cycle search. Independently self-closed strokes are pulled out *before*
   grouping so a connecting arrow can't bridge two separate shapes into
   one bogus component.
3. **`shape_classifier.py`** — resamples the outline to a fixed point
   count, normalizes it into its own bounding box, and compares it against
   ideal rectangle/diamond/parallelogram/ellipse templates via nearest-
   point distance. Below a rejection threshold, the sketch stays
   unrecognized rather than being forced into a guess.
4. **`arrow_detector.py`** — validates elongated, mostly-straight open
   strokes as arrows, detects which end has the arrowhead (turning-angle
   analysis near each endpoint, falling back to draw order), and snaps
   both ends to the nearest recognized node.
5. **`label_ocr.py` + `vision_providers.py`** — crops the region of a
   canvas snapshot inside each recognized shape and sends it to a real
   vision model (Gemini or OpenAI, your choice) to transcribe handwritten
   labels. Requires your own API key in `.env` (`AI_PROVIDER` +
   `GEMINI_API_KEY` or `OPENAI_API_KEY`) — same pattern as the Google OAuth
   client ID in Phase 1. Shape recognition still works with zero
   configuration; only handwritten label transcription needs a key.

Connector vs. start/end ellipses, and start vs. end, are disambiguated
using real context (relative size vs. other shapes, and in/out-degree
after arrow detection) rather than a fixed rule.

### Tested

`backend/tests/test_recognition_pipeline.py` runs the full pipeline
against synthetic (intentionally jittered, multi-stroke) hand-drawn-style
input — rectangle, diamond, parallelogram, oval, a small circle next to
larger shapes (connector), a 4-stroke rectangle, an arrow between two
recognized shapes, an unrecognizable scribble, and label OCR both with a
fake vision provider and with no provider configured (graceful
degradation). Run with:

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

### Trying it end-to-end

1. Set `AI_PROVIDER=gemini` and `GEMINI_API_KEY=...` in `backend/.env`
   (get a free key at https://aistudio.google.com/apikey), or use
   `AI_PROVIDER=openai` with `OPENAI_API_KEY`.
2. In the editor, select the **Freehand** tool (F) and draw a rough
   rectangle, a diamond, and an arrow between them. Write a word or two
   inside one of the shapes.
3. Click **Recognize Sketch**. The rough ink is replaced with clean,
   editable nodes and a connecting arrow; the handwritten label appears as
   the node's text once transcription returns.
4. Without an API key configured, shapes and arrows still recognize
   correctly — you'll just see a note that labels weren't transcribed.

---

## Phase 2 — Feature 2: Code Generation

Click **Generate Code** in the editor toolbar, pick a language, and get
real, runnable source generated from the flowchart's shapes and
connectors — Python, Java, C, C++, JavaScript, TypeScript, C#, Go, Rust,
and PHP.

### How it works

`backend/app/codegen/` — a small compiler pipeline, not a template
lookup:

1. **`expression_parser.py`** — a real operator-precedence (Pratt) parser
   for the arithmetic/boolean expressions people write inside shapes
   (`n > 0 and total < 100`), handling precedence and parentheses
   correctly.
2. **`pseudocode_parser.py`** — recognizes the vocabulary flowchart
   pseudocode actually uses (`Read x`, `Print total`, `x = x + 1`) and
   falls back to an honest comment rather than guessing when it can't.
3. **`graph_structurer.py`** — the hard part. Turns the raw node/edge
   graph into nested `if`/`while` control flow using two real graph
   algorithms: forward-reachability BFS to detect loop back-edges
   (including multi-hop ones like `decision -> body -> decision`, not
   just an immediate self-loop), and simultaneous BFS from both branches
   of a decision to find their common merge point for `if`/`else`.
   Decision connectors labeled "Yes"/"No" pick the branch precisely;
   unlabeled ones fall back to connector order, surfaced as a warning.
4. **`type_inference.py`** — a forward pass inferring each variable's
   type (int/float/string/bool) from literals and arithmetic, so
   statically-typed languages get real declared types instead of `var`
   everywhere. Inconsistent usage is marked "unknown" honestly rather than
   silently picked.
5. **`emitters/`** — one class per language, sharing a common base for
   C-style block/if/while emission, each overriding what's genuinely
   different (Python's indentation and `input()`, Go's `for`-as-while and
   no-paren conditions, Rust's `let mut` and real `stdin` parsing, PHP's
   `$` sigils, C/C++'s `return 0;` requirement in `main()`).

### Tested — including actually compiling and running the output

`backend/tests/test_codegen_ir.py` covers the parser and graph structurer
in isolation (precedence, back-edge loop detection, if/else merging, type
widening).

`backend/tests/test_codegen_emitters.py` builds two canonical flowcharts
(an if/else sign-checker and a while-loop sum-1-to-n) and, for every
language where a toolchain exists in the dev environment, **actually
compiles and runs the generated code and checks its real output** —
Python and Node.js directly, C via `gcc`, C++ via `g++ -std=c++17`. Two
real bugs were caught this way and fixed: loop detection missing
multi-hop back edges, and C/C++'s `main()` requiring `return 0;` instead
of a bare `return;` (gcc silently accepted it with a garbage exit code;
g++ correctly refused to compile it). Languages without an available
compiler in this sandbox (Java, C#, Go, Rust, PHP) are checked
structurally (balanced braces, required syntax markers) — the shared
graph/type logic behind all ten emitters is the same code already
verified end-to-end by the languages above.

```bash
cd backend
pytest tests/ -v
```

### Trying it end-to-end

1. Draw or recognize a flowchart with a Start, at least one Decision, and
   an End.
2. Inside each shape, write pseudocode: `Read n`, `n > 0`, `Print "yes"`,
   etc. Label decision connectors "Yes"/"No" for precise branching
   (optional — otherwise the first connector is assumed true).
3. Click **Generate Code**, pick a language, and copy or download it.

---

## Phase 2 — Feature 3: Code → Flowchart

Click **Code → Flowchart** in the editor, paste Python, and a real
flowchart is added to the canvas below whatever's already there (never
destructive).

### How it works

`backend/app/codetoflow/` — the reverse direction of Feature 2, reusing
the same shared IR from `app/codegen/ir.py`:

1. **`python_ast_adapter.py`** — parses real Python using Python's own
   built-in `ast` module (not string matching), converting assignments,
   augmented assignments, if/elif/else, while loops, range()-based for
   loops (desugared into an equivalent while), input()/print() calls, and
   expressions (including chained comparisons and boolean operators) into
   the shared IR. Anything genuinely unsupported (function defs beyond an
   optional `main()`, non-range for-loops, arbitrary calls) is preserved
   verbatim as a comment via `ast.unparse` rather than silently dropped.
2. **`ir_to_text.py`** — the reverse of `pseudocode_parser.py`: turns IR
   expressions/statements back into short human-readable text for shape
   labels (`n = n + 1`, `Read age`, `Print total`).
3. **`flowchart_layout.py`** — a real automatic graph-layout algorithm
   (a single-pass layered layout specialized for flowcharts): the main
   sequence runs down a center line, if/else branches offset right/left
   and reconverge into whatever comes next, while-loop bodies offset right
   and loop back into the condition. Every statement sequence is laid out
   from a real list of incoming connection points from its actual
   predecessor — an earlier version of this used a placeholder "virtual
   entry point" for the first node of every branch, which silently
   dropped the connecting edge into that node; caught by the test suite
   and fixed.

### Tested — including a round-trip against Feature 2

`backend/tests/test_codetoflow.py` covers the AST adapter (assignments,
if/else, while, range-for desugaring, main() extraction, unsupported
constructs surviving as comments) and the layout algorithm (start/end
nodes present, if/else branches provably reconverging into the same next
node, while loops provably having a back-edge, no two nodes at the same
vertical position). It also round-trips: build a flowchart, run it through
Feature 2 to generate Python, then run that Python through Feature 3 and
check the regenerated diagram still has exactly one decision and the
loop's back-edge survived.

```bash
cd backend
pytest tests/ -v
```

### Trying it end-to-end

1. Click **Code → Flowchart** in the editor.
2. Paste Python — the placeholder text shows a working example.
3. Click **Generate Flowchart**. It's added below your existing canvas
   content, fully editable like any other shape.
4. Currently Python-only; other languages need their own AST adapter
   (the layout algorithm and IR are already language-agnostic — it's the
   same shared IR Feature 2 uses).

---

## Phase 2 — Feature 4: Execution Simulator

Click **Run** in the editor. The flowchart actually executes — real
variable state, real branching, real loop iteration — and you step or
play through the trace while the currently-executing shape glows on the
canvas.

### How it works

`backend/app/execution/` — a real interpreter, not a scripted animation:

1. **`evaluator.py`** — evaluates IR expressions with genuine runtime
   semantics: division by zero raises, using a variable before it's ever
   been assigned raises (the whole point of a simulator is to catch these
   bugs for the student, not hide them behind a silent default of 0), and
   `and`/`or` short-circuit like a real language.
2. **`interpreter.py`** — walks the flowchart's actual node/edge graph
   starting at Start, reusing `pseudocode_parser` from Feature 2 (so
   simulation and code generation never disagree about what a shape
   means) and `resolve_branch` from Feature 2's graph structurer (so a
   decision's Yes/No branch is resolved identically whether you're
   generating code or running it — this shared helper was extracted from
   Feature 2's code specifically so the two could never drift apart).
   Loops aren't statically detected here — the interpreter just follows
   whichever edge the *live* condition value selects, so a loop genuinely
   repeats based on runtime state, the same way a real debugger would
   step through it. A step counter (2000 steps) catches infinite loops
   instead of hanging.
3. Every step of execution is recorded as a full snapshot (which shape
   executed, the complete variable table at that point, any console
   output produced) and returned as a trace; the frontend just plays back
   or steps through real recorded state — nothing is re-simulated or
   guessed on the frontend.

**Scope, stated honestly:** this flowchart tool's symbol set (per Feature
1) is Start/End/Process/Decision/Input/Output/Connector — there's no
subroutine/function-call shape. So the simulator executes sequences,
decisions, and loops (via decision back-edges) for real, but doesn't
claim to support functions or recursion, since there's no way to draw a
function call yet. Adding that would mean adding a new node type first.

### Tested

`backend/tests/test_execution.py` covers the evaluator (arithmetic,
comparisons, short-circuit and/or, string concatenation, division by
zero, undefined-variable errors) and the interpreter end-to-end: a
sum-1-to-5 loop that must produce exactly 15, an if/else that must take
the runtime-correct branch, an infinite loop that must be caught by the
step limit, input values consumed in the order the flowchart actually
reads them (not just node order), and errors that must halt at the
correct node with a message a student could act on.

```bash
cd backend
pytest tests/ -v
```

### Trying it end-to-end

1. Click **Run**. If your flowchart has Input shapes, list values
   (comma or newline separated) in the order they're read.
2. Press the play button or step forward one shape at a time. Watch the
   currently-executing shape glow green on the canvas, the variable table
   update, and console output appear exactly as the flowchart produces it.
3. Errors (division by zero, an unassigned variable, an infinite loop)
   stop the simulation at the exact shape that caused them, with a plain
   message — this is meant to help you find real bugs in your flowchart.

---

## Phase 2 — Feature 5: AI Explainer

Click **Explain** in the editor and pick a style — Simple (beginner),
Line by Line, or Interview — to get a real AI-written explanation of what
the flowchart actually does.

### How it works

`backend/app/explainer/` — the one feature so far that genuinely needs an
LLM, and it's scoped to exactly the part that does:

1. **`pseudocode_renderer.py`** — reuses the same `GraphStructurer` from
   Feature 2 to turn the flowchart into accurate, correctly-nested
   pseudocode (real if/else, real while loops — the same structuring
   logic already tested end-to-end in Feature 2). This is deterministic
   and never touches the AI.
2. **`prompts.py`** — builds a mode-specific system prompt (beginner
   plain-English, step-by-step walkthrough, or interview-style summary)
   with the pseudocode embedded as context.
3. **`providers.py`** — the only part that calls an LLM, via the same
   pluggable Gemini/OpenAI pattern as Feature 1's handwriting OCR (reusing
   the same `AI_PROVIDER` / API key config — no new setup needed if you
   already configured Feature 1).

The model is asked to *explain* already-correct structure, never to
*infer* it — control flow correctness comes entirely from tested,
deterministic code; the LLM only writes the prose.

### Tested

`backend/tests/test_explainer.py` covers the pseudocode renderer (correct
if/else and while nesting), prompt construction (each mode selects the
right system prompt and embeds the pseudocode), and the pipeline's logic
using a fake text provider that records exactly what it was asked —
verifying correct behavior without making a real network call in
automated tests. An empty flowchart is handled without even calling the
provider (saving an API call for a diagram with nothing to explain).

```bash
cd backend
pytest tests/ -v
```

### Trying it end-to-end

1. Make sure `AI_PROVIDER` and an API key are set in `backend/.env` (see
   Feature 1's setup — same configuration).
2. Draw or generate a flowchart with at least a Start, one Decision, and
   an End.
3. Click **Explain**, pick a style, and read the real AI-generated
   explanation of your specific flowchart's logic.

---

## Phase 2 — Feature 6: Time & Space Complexity Analysis

Click **Complexity**. Unlike the Explainer, this is deliberately **not**
an AI guess for the Big-O itself — a hallucinated complexity claim would
actively mislead a student, so the actual analysis is real static
analysis, with AI only optionally phrasing a summary on top of facts it
didn't get to invent.

### How it works

`backend/app/complexity/`:

1. **`analyzer.py`** — walks the same structured IR Feature 2 and
   Feature 5 use. Nested loops add polynomial degree (one loop → O(n),
   nested → O(n²), etc.); a loop whose control variable changes
   multiplicatively each iteration (`i = i / 2`) contributes a log-n
   factor instead; sequential blocks and if/else branches combine by
   taking the dominant (worst-case) term — the same reasoning a person
   uses to read Big-O by eye. When a loop's growth pattern isn't
   recognizable, the result is honestly labeled "estimated" rather than
   stated with false confidence.
2. Also flags real optimization opportunities: loop-invariant
   computations (an assignment inside a loop that doesn't depend on
   anything the loop changes) get flagged for hoisting, and O(n²)-or-worse
   nested loops get a note about hash-based alternatives.
3. Space complexity is stated as a fact about this tool's scope: since
   Feature 1's symbol set has no array/list/recursion shapes, every
   diagram this tool can represent only ever uses a fixed number of
   scalar variables — O(1) auxiliary space, always.
4. **`providers.py`** is reused directly from Feature 5 — an optional AI
   narrative is generated *from* the already-computed complexity and
   reasoning (the prompt explicitly tells the model to treat the stated
   complexity as fact and explain it, not second-guess it). If no AI key
   is configured, the deterministic analysis still returns in full —
   only the narrative is skipped.

### Tested

`backend/tests/test_complexity.py` verifies actual Big-O determination
against known shapes: O(1) for no loops, O(n) for a single counted loop,
O(n²) for nested counted loops, O(log n) for a halving loop, worst-case
branch selection in if/else, loop-invariant hoisting detection, and
confidence correctly downgrading to "estimated" for an unrecognizable
loop pattern — plus the AI-narrative wiring using a fake provider.

```bash
cd backend
pytest tests/ -v
```

### Trying it end-to-end

1. Click **Complexity** on a flowchart with at least one loop.
2. See the real Big-O time and space complexity, the reasoning behind
   it, and any optimization suggestions.
3. If `AI_PROVIDER` is configured, an AI-written summary appears too —
   built strictly from the facts already computed above it.

---

## Phase 2 — Feature 7: Bug Detector

Click **Bug Detector** to scan for missing arrows, disconnected shapes,
invalid decisions, and infinite loops/dead ends — via real graph
analysis, not a canned checklist.

### How it works

`backend/app/bugdetector/detector.py` — the key technique is a single
two-directional reachability check that catches most of the interesting
bugs at once: compute every shape reachable *forward* from Start, and
every shape that can reach *any* End *backward*. A shape that's reachable
from Start but can never reach an End represents a guaranteed
non-terminating path — whether that's a literal infinite loop (a cycle
with no exit) or a dead-end branch that trails off — same symptom, one
check, no separate cycle-detection algorithm needed.

Alongside that: missing Start/End, Start with multiple or zero outgoing
connectors, End with an outgoing connector, any non-End shape with no
outgoing connector ("missing arrow"), any non-Start shape with nothing
connecting into it ("disconnected"), decisions with the wrong number of
outgoing connectors or both branches pointing at the same shape, and
(reusing Feature 2/4's `resolve_branch`) decisions without Yes/No labels.

### Tested

`backend/tests/test_bug_detector.py` — 13 tests against known-broken
graphs for every category (missing Start, missing End, dead-end shapes,
disconnected shapes, 1-output and 3-output decisions, both-branches-
same-target, unlabeled branches, a while-loop whose "exit" branch
actually loops back into the cycle instead of reaching End, and a direct
self-loop) plus one known-good flowchart producing zero errors.

```bash
cd backend
pytest tests/ -v
```

### Trying it end-to-end

Click **Bug Detector**, then **Scan Flowchart**. Click any finding to
select the shape(s) it's about on the canvas.

---

## Phase 2 — Feature 8: Export

Click **Export** in the editor toolbar for PNG, SVG, PDF, or Project
JSON — plus a shortcut straight into Feature 2's code generator for
source code. This is entirely frontend work; none of it needs the
backend.

### How it works

`frontend/src/lib/export/`:

1. **`boundingBox.ts`** — computes the real bounding box of every node
   and stroke on the canvas (with padding), so exports are cropped to
   actual content instead of dumping the whole infinite canvas.
2. **PNG** — Konva's native `stage.toDataURL()`, cropped to that
   bounding box (converted from world to screen coordinates via the
   current pan/zoom) at 2x pixel ratio.
3. **`svgExport.ts`** — a genuine hand-written vector SVG serializer, not
   a wrapped screenshot: each shape type (rectangle, diamond, ellipse,
   parallelogram) is reconstructed as real SVG markup matching exactly
   how `NodeShape.tsx` renders it on the Konva canvas, with a real
   arrowhead `<marker>` for edges and word-wrapped `<text>` for labels.
   Freehand strokes render at constant width rather than reproducing
   per-point pressure variation in vector form — a documented
   simplification (building a pressure-varying filled outline path is
   substantially more complex for little visual gain in an exported
   diagram).
4. **PDF** — the same cropped PNG snapshot embedded in a real PDF via
   `jsPDF`, sized to match the diagram's aspect ratio.
5. **Project JSON** — the full `canvas_data` (nodes, edges, strokes,
   viewport) as a downloadable, re-importable project file.
6. **Source Code** — not a separate implementation; it just opens
   Feature 2's existing code generation panel, since that already does
   exactly this job.

### Tested

Set up `vitest` as the frontend's test runner (the first frontend-only
feature so far) and wrote real unit tests: `src/lib/export/__tests__/
export.test.ts` covers the bounding-box math, and — critically — actually
parses the generated SVG string to verify a decision node produces a
real 4-point diamond polygon, start/end nodes produce ellipses, XML
special characters in labels are correctly escaped, edges include a
real arrowhead marker reference, edge labels render as text, eraser
strokes are correctly excluded, and the JSON export round-trips through
`JSON.parse` with the expected shape.

```bash
cd frontend
npm install
npm test
```

### Trying it end-to-end

Draw a flowchart, click **Export**, and try each format. SVG opens
correctly in a browser or vector editor since it's real markup, not an
embedded raster image.

---

## Phase 2 — Feature 9: Flowchart Beautifier

Click **Beautify** to auto-align and re-space any flowchart into a clean
layout — with almost no new code, because two already-tested engines
already do the actual work.

### How it works

`backend/app/beautifier/pipeline.py` doesn't implement its own layout
logic at all: "beautify" is just running the existing flowchart's graph
through **Feature 2's `GraphStructurer`** (to understand the actual
if/else/while logic) and then **Feature 3's `FlowchartLayout`** (to
generate clean positions from that structure) — the exact same pipeline
Code-to-Flowchart uses, just fed a flowchart's own graph instead of
freshly parsed code. A hand-arranged diagram with every shape dropped in
roughly the same spot comes out the other side auto-aligned, evenly
spaced, and provably non-overlapping.

This composition does have two honest, documented side effects: text
round-trips through the parser/formatter (so `n>0` becomes `n > 0` —
arguably an improvement), and connector/free-text shapes get folded into
ordinary process boxes, since the layout engine optimizes positions for
the standard control-flow symbols.

### Tested

`backend/tests/test_beautifier.py` — the most satisfying test here
actually deliberately drops every node at nearly the same (x, y)
coordinate (about as messy as a real hand-arranged flowchart gets) and
verifies **zero pairwise bounding-box overlaps** in the output — a real
geometric property, not just "it ran without crashing." Also verifies
decision/shape counts are preserved, text gets normalized, running
beautify on its own output is stable, and unlabeled-branch warnings still
surface.

```bash
cd backend
pytest tests/ -v
```

### Trying it end-to-end

Draw a messy flowchart (or manually drag shapes onto each other) and
click **Beautify**. Ctrl+Z undoes it if you don't like the result.

---

## Phase 2 — Feature 10: Templates Library

Click **Templates** in the dashboard sidebar for ready-made flowcharts
across DSA Basics, Sorting, Searching, Operating Systems, Networking,
Compiler Design, and Database — grouped by category, one click to start
a new project from any of them.

### How it works

`backend/app/templates/definitions.py` — every template is built
directly as IR (the same `Program`/`Stmt`/`Expr` classes from
`app.codegen.ir`), not a JSON blob of hand-placed shapes with manually
computed coordinates:

- Positions are never hand-tuned — every template runs through
  **Feature 3's `FlowchartLayout`**, the same tested auto-layout engine
  used for Code → Flowchart, so a template is laid out exactly as
  cleanly as any generated diagram.
- The **DSA Basics** templates (Factorial, Fibonacci, GCD, Prime Check,
  Sum of Digits, Armstrong Number) are real, runnable algorithms — not
  just correct-looking diagrams. They're built from real arithmetic IR,
  so Execution Simulator, Code Generation, and Complexity Analysis all
  work on them exactly like a diagram you'd drawn yourself.
- Sorting/Searching/OS/Networking/Compiler/Database templates use array
  indexing or purely conceptual steps this tool's scalar-only expression
  model can't execute — those are honestly marked `executable: false`
  (shown as a "Diagram only" badge). Their flowchart *structure* (loops,
  branches) is still real and correct; only step-by-step numeric
  simulation is out of scope for them, and that's surfaced rather than
  hidden.

### A bug this caught

Writing these templates as real IR and then actually running them
through the Feature 4 interpreter surfaced two genuine round-trip bugs
that manual QA likely wouldn't have caught:

1. The expression tokenizer didn't recognize `//` (floor division) as a
   single operator — it silently split into two separate `/` tokens and
   fell back to an unparseable raw expression. Fixed in
   `expression_parser.py`, with the C-style and Python emitters updated
   to map it correctly per language.
2. `ir_to_text.py`'s own display format for an Input with a prompt —
   `Read n ("Enter a number")` — couldn't be parsed back correctly by
   `pseudocode_parser.py`; it grabbed the wrong token as the variable
   name. Since the execution simulator re-parses node text on every run,
   this silently renamed the variable. Fixed with a dedicated pattern
   for this tool's own round-trip format.

Both are exactly the kind of bug that only surfaces when a feature is
tested by actually running real programs through the pipeline, rather
than checking that output merely looks plausible.

### Tested

`backend/tests/test_templates.py` — every template lays out with a
Start and End and no crash; for the six executable templates, **actually
runs them through the real `FlowchartInterpreter`** and checks the
computed answer: factorial(5) = 120, the first 5 Fibonacci numbers,
gcd(48, 18) = 6, prime checks for 1/2/7/8, sum of digits of 1234 = 10,
and both the true and false Armstrong-number cases (153 and 154).

```bash
cd backend
pytest tests/ -v
```

### Trying it end-to-end

Sidebar → **Templates** → pick any card. A new project is created,
pre-loaded with that template, and you're dropped straight into the
editor.

---

## Phase 2 — Feature 11: AI Chat Assistant

Click **Ask AI** in the editor for a conversational interface — but it's
a router in front of the real pipelines already built, not a new AI
system reimplementing all of them from scratch inside a chat reply.

### How it works

`backend/app/chatassistant/`:

1. **`intent_router.py`** — real, deterministic regex/keyword matching
   (no AI call needed just to route a message) decides whether you're
   asking to check for bugs, analyze complexity, generate code, beautify
   the layout, get an explanation, or something open-ended.
2. **`language_detector.py`** — picks the target language out of the
   message text ("write this in Java", "convert to C++") for the
   generate-code intent.
3. **`pipeline.py`** routes to the actual existing pipeline for each
   intent: **Bug Detector**, **Complexity Analysis**, **Code
   Generation**, and the **Beautifier** are fully deterministic and work
   here with zero AI dependency — only "explain this" and genuinely
   open-ended questions call an LLM (reusing Feature 5's provider), and
   those degrade to a clear, honest fallback message rather than silence
   or a fake answer when no `AI_PROVIDER` key is configured.
4. When the assistant's reply includes real data (a beautified layout, a
   generated code block), the chat UI surfaces an actual action button —
   **Apply to canvas** re-lays out your flowchart for real via the same
   store action the Beautify button uses; **Copy code** copies the real
   generated source.

### A couple of real regex bugs this caught

Writing the intent-classification tests against realistic phrasing
surfaced two genuine bugs before they shipped: `\bbug\b` doesn't match
the word "bugs" (the trailing 's' breaks the right-side word boundary),
so "any bugs in here?" was falling through to the general/AI-chat path
instead of the bug detector. And the code-generation pattern required
the literal word "code" to appear, so "write this in Java" (a completely
natural way to ask) wasn't recognized — fixed by also matching
write/generate + in/using + a known language name.

### Tested

`backend/tests/test_chatassistant.py` — 32 tests: intent classification
across realistic phrasings for all six intents, language detection for
all 10 supported languages plus the "c" vs "c++"/"c#" disambiguation,
and full routing tests that call the real pipelines underneath (a
structurally-broken flowchart really does come back with bug-detector
findings; the sign-checker really does come back O(1); "write this in
java" really does produce `public class Main`), plus explain/general
intents tested both with and without an AI provider to confirm the
honest fallback path never goes silent.

```bash
cd backend
pytest tests/ -v
```

### Trying it end-to-end

Click **Ask AI**, try one of the suggested prompts or ask your own
question. Bug/complexity/codegen/beautify work immediately; explanations
and free-form questions need `AI_PROVIDER` configured in `backend/.env`.

---

## Phase 2 — Feature 12: Settings

Sidebar → **Settings** for preferences that actually change editor
behavior — no decorative toggles that don't do anything.

### What's real here

- **Autosave interval** — 1s/2s/5s/10s, or **Manual only**, which
  disables the debounced background save entirely and adds a **Save
  now** button to the editor's header in its place. This isn't a display
  preference; it changes which code path `useAutosave` actually takes.
- **Snap to grid** — dragged or newly-drawn shapes round to the nearest
  20px, wired directly into the canvas's drag and shape-creation
  handlers.
- **Show grid background** — toggles the dotted grid pattern class on
  the canvas container.
- **Reduce motion** — an explicit, app-level version of
  `prefers-reduced-motion` that doesn't depend on OS settings; toggling
  it adds a `reduce-motion` class to the document root, governed by the
  same CSS rule already used for the system-level media query.
- **Keyboard shortcuts reference** — a static list, but an accurate one:
  every entry matches a real binding in `useKeyboardShortcuts.ts`, not a
  wish-list.
- **Interface language** — deliberately has no dropdown. A language
  switcher that doesn't actually translate the UI would be worse than
  no control at all, so this section says so plainly instead of faking
  one.

All preferences persist to `localStorage` per device (via a small
Zustand store, `useSettingsStore`, following the same `persist` pattern
already used for auth state) — these are editor/device preferences, not
account data that needs to sync across machines.

### Also cleaned up while here

The dashboard sidebar had two stale links — "AI Assistant" and
"Execution Simulator" — still pointing at "coming soon" placeholders
from before those features were built. Both now live inside the editor
itself (the **Ask AI** and **Run** buttons, since they need an open
flowchart to operate on), so the misleading standalone links were
removed rather than left pointing at a lie.

### Trying it end-to-end

Sidebar → **Settings**. Switch autosave to "Manual only" and watch the
editor's save indicator turn into a **Save now** button; toggle **Snap
to grid** and drag a shape to see it land on 20px increments.

---

## Phase 2 — Feature 13: Voice Mode

Click **Voice Mode**, speak a description like "create a flowchart that
checks if a number is even or odd," and a real flowchart is added to
your canvas.

### How it works

This isn't a separate flowchart-generation system — it's **Feature 3
(Code → Flowchart) with an LLM standing in for "paste some Python."**

1. **Speech-to-text** is the browser's native Web Speech API
   (`frontend/src/hooks/useSpeechRecognition.ts`) — no backend
   involvement, works in Chrome/Edge, and honestly reports when a
   browser doesn't support it (Firefox/Safari) rather than pretending to
   listen.
2. **`backend/app/voicemode/prompts.py`** asks the LLM to draft a short,
   real Python script implementing the spoken request — constrained to
   exactly the subset Feature 3's parser already supports (no functions,
   no imports, just assignments/input/print/if-else/while).
3. **`backend/app/voicemode/pipeline.py`** feeds that code straight into
   Feature 3's real, `ast`-based `parse_python_source` and
   `FlowchartLayout` — the exact same tested pipeline, not a
   reimplementation. If the model's code doesn't parse, **one retry is
   attempted with the actual Python syntax error fed back** to the
   model; if that still fails, it returns a clear error rather than
   fabricating a flowchart from nothing.
4. The generated flowchart is added to the canvas the same
   non-destructive way as Code → Flowchart (below existing content), and
   the actual generated Python is shown in a collapsible "show the code"
   section for transparency.

### Tested

`backend/tests/test_voicemode.py` — prompt construction (the spoken
description and, on retry, the actual prior error, are both embedded),
markdown code-fence stripping (models often wrap output in ` ```python `
even when told not to), a successful generation producing a real
start/decision/end layout, **a genuine retry test**: a fake provider
returns invalid Python on the first call and valid Python on the second,
verifying the pipeline actually retries with the real error message and
succeeds — and the failure path when both attempts produce unparseable
code, confirming it returns a clean error instead of crashing or
inventing a fake diagram.

```bash
cd backend
pytest tests/ -v
```

### Trying it end-to-end

Click **Voice Mode**, tap the mic (or type into the text box — voice
isn't required), describe an algorithm, and click **Generate
Flowchart**. Needs `AI_PROVIDER` configured in `backend/.env`, same as
the Explainer.

---

## Phase 2 — Feature 14: Realtime Collaboration

Click **Share** to turn on collaborative access, then **History** and
**Comments** for version checkpoints and pinned discussion — plus live
cursors and presence while collaborators are in the same project.

### A real gap this surfaced

Every prior feature assumed a project has exactly one owner. Building
collaboration surfaced that **there was no way for a second user account
to access the same project at all** — `get_owned_project` rejected
anyone but the owner. That had to be fixed first: `Project` gained an
`is_shared` flag (`backend/app/models/project.py`), and a new
`get_accessible_project` helper (`backend/app/api/access.py`) checks
"owner OR shared" instead of strict ownership for viewing, autosaving,
commenting, and joining the live session — while rename/duplicate/delete
and the share toggle itself stay owner-only. This is deliberately simple
"anyone with the link can edit" sharing, not a full per-user role system
— stated as a real scope choice, not a missing feature hidden from view.

### How it works

1. **`backend/app/collaboration/connection_manager.py`** — an in-memory
   room manager (project id → connected clients) that's a plain,
   dependency-free class rather than something requiring a live
   websocket server to test: it only needs an object with an async
   `send_json`, so its actual room/broadcast/presence logic is fully
   unit-tested with lightweight fakes. **Stated honestly**: this is a
   single-process in-memory manager, correct for one server instance;
   scaling collaboration across multiple backend processes would need a
   shared pub/sub layer (e.g. Redis) to broadcast across instances —
   real infrastructure this project doesn't have and doesn't need to run
   as built.
2. **`backend/app/api/routes/collaboration_ws.py`** — the WebSocket
   endpoint itself (JWT passed as a query param, since browsers can't set
   custom WebSocket headers). Relays cursor positions and canvas
   snapshots between everyone in a project's room.
3. **Canvas sync is deliberately last-write-wins** broadcast — whoever's
   edit arrives last is what every client ends up seeing — the same
   concurrency model this app's autosave already uses, just propagated
   live instead of only on reload, rather than a full operational-
   transform/CRDT merge (a substantially larger undertaking that isn't
   proportionate here).
4. **Comments** (`backend/app/collaboration/comments_service.py`) and
   **Version History** (`versions_service.py`) are real, persisted DB
   models — not just live broadcast state. A comment pins to either a
   specific shape or a free canvas point; only its author can delete it.
   Version snapshots are explicit checkpoints (not one per autosave, which
   would create too much noise) with automatic pruning past 50 per
   project, and restoring one first saves the current state as its own
   checkpoint so a restore is itself reversible.

### Tested

Two different testing approaches for two different kinds of logic:

- `backend/tests/test_connection_manager.py` — the live-collaboration
  logic (rooms, broadcast-excludes-sender, presence updates, room
  cleanup on last participant leaving) tested with fake WebSocket-like
  objects, no real server needed. This also caught a real bug: the
  read-only `room_size()`/`participants()` accessors were calling the
  same internal helper used for *creating* rooms, so checking the size of
  a room right after everyone left silently recreated it — fixed by
  giving read-only lookups a genuinely read-only path.
- `backend/tests/test_collaboration_db.py` — comments and version
  history against a real in-memory SQLite database (this project's first
  tests to touch actual persistence rather than pure in-memory
  dataclasses, since that's the whole point of these two features):
  author-only delete permission, chronological comment ordering, version
  snapshot/restore round-tripping actual canvas data, and version
  pruning past the retention limit.

```bash
cd backend
pip install -r requirements.txt   # now includes pytest-asyncio
pytest tests/ -v
```

### Trying it end-to-end

Open a project, click **Share** → **Enable sharing** → **Copy link**.
Open that link in another browser session (or ask a collaborator to),
and you'll see each other's cursors and edits live, plus a presence bar
of who's connected. **History** lets either of you save a checkpoint and
roll back to it later; **Comments** lets you pin notes to specific
shapes.

---

## Phase 2 — Feature 15: Admin Panel

Sidebar → **Admin Panel** (only visible to admin accounts) for real
users/projects/analytics — every number comes from an actual database
query, not sample data.

### Bootstrapping the first admin

There's deliberately no separate CLI tool or migration for this: set
`ADMIN_EMAILS=you@example.com` (comma-separated for more than one) in
`backend/.env`. Any account with a matching email is granted admin
access on signup, and status stays in sync on every login in case the
list changes later — so promoting someone is editing one env var and
having them log in again, not a special onboarding flow.

### A real gap this surfaced

Same story as Collaboration: giving the admin panel something meaningful
to show required data across *all* users, and every project route so far
was owner-scoped. `backend/app/api/access.py`'s split (owner-only vs.
owner-or-shared) already solved cross-user access for collaboration;
Admin adds a third tier — `get_current_admin_user`
(`backend/app/admin/deps.py`) — that bypasses per-project ownership
entirely for a small, explicit set of moderation endpoints, rather than
threading admin bypasses through every existing route.

### How it works

`backend/app/admin/service.py` — real aggregate SQL queries, not
computed-then-faked numbers: user list with an actual `COUNT(project_id)
GROUP BY user`, project list with a real join to fetch owner name/email,
and analytics (total users/projects/comments/versions, shared-vs-private
ratio, signups and project creation grouped by day over the last 30
days, average projects per user) all computed directly against the
`User`/`Project`/`Comment`/`ProjectVersion` tables. Moderation actions —
suspend/reactivate a user, delete any project — are real writes with one
explicit safety rule: an admin can't deactivate their own account (so
you can't accidentally lock yourself out).

The frontend's daily-activity charts are a small, dependency-free bar
chart component rather than pulling in a charting library for two simple
bar charts.

### Tested

`backend/tests/test_admin.py` — 11 tests against a real in-memory
SQLite database: project counts per user are correct even for users with
zero projects, the admin-can't-deactivate-themself guard, moderating an
unknown user/project raises a clear error instead of silently doing
nothing, analytics reflects exactly the rows inserted (including the
shared-vs-private ratio and the average-projects-per-user division),
avoiding a division-by-zero when there are no users yet, and the
authorization dependency itself — a non-admin user is rejected with 403,
an admin passes through.

```bash
cd backend
pytest tests/ -v
```

### Trying it end-to-end

Set `ADMIN_EMAILS` in `backend/.env` to your account's email, log out
and back in, and **Admin Panel** appears in the sidebar. Overview shows
real totals and 30-day activity charts; Users lets you suspend/reactivate
accounts; Projects lets you moderate/delete any project across every
user.

---

## That's the full original spec

Every feature from the original mega-prompt is now built: the Phase 1
platform plus all 15 Phase 2 features — AI Recognition, Code Generation,
Code → Flowchart, Execution Simulator, AI Explainer, Complexity
Analysis, Bug Detector, Export, Beautifier, Templates, AI Chat
Assistant, Settings, Voice Mode, Realtime Collaboration, and the Admin
Panel. Every one of them is backed by real logic and a real test suite
— run `pytest tests/ -v` in `backend/` (199 tests) and `npm test` in
`frontend/` (12 tests) to see all of it pass.
