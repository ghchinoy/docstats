// =============================================================================
// Docstats Empirical Evaluation Preprint
// "Augmenting Large Language Model Writing Assistants with Formal Multi-Axis
//  Readability and Deterministic Stylistic Feedback"
// =============================================================================

#import "results_generated.typ": *

#set document(
  title: [Augmenting Large Language Model Writing Assistants with Formal Multi-Axis Readability and Deterministic Stylistic Feedback],
  author: "G.H. Chinoy",
  keywords: (
    "Large Language Models",
    "Technical Writing",
    "AI Writing Tells",
    "Readability Metrics",
    "Model Context Protocol",
    "Deterministic Evaluation",
  ),
  date: datetime.today(),
)

// --- Page & Typography Configuration ---
#set page(
  paper: "us-letter",
  margin: (x: 1.8cm, top: 2.2cm, bottom: 2.2cm),
  header: context {
    if here().page() > 1 {
      text(size: 8pt, fill: luma(100), font: "Libertinus Serif")[
        #grid(
          columns: (1fr, 1fr),
          align: (left, right),
          [Augmenting LLM Writing Assistants with Multi-Axis Metrics],
          [Preprint / Technical Report],
        )
        #v(-0.4em)
        #line(length: 100%, stroke: 0.4pt + luma(180))
      ]
    }
  },
  footer: context {
    text(size: 8.5pt, fill: luma(100), font: "Libertinus Serif")[
      #line(length: 100%, stroke: 0.4pt + luma(180))
      #v(-0.2em)
      #grid(
        columns: (1fr, 1fr),
        align: (left, right),
        [Docstats Empirical Study],
        [#counter(page).display()],
      )
    ]
  },
)

#set text(
  font: ("Libertinus Serif", "New Computer Modern", "Times New Roman"),
  size: 9.8pt,
  lang: "en",
)

#set par(
  justify: true,
  leading: 0.58em,
)

#set heading(numbering: "1.1")
#show heading: it => block(
  above: 1.0em,
  below: 0.55em,
  sticky: true,
)[
  #text(
    weight: "bold",
    fill: rgb("#1a202c"),
    size: if it.level == 1 { 12pt } else if it.level == 2 { 10.5pt } else { 9.8pt },
  )[#it]
]

#show figure.caption: it => [
  #text(size: 8.5pt, style: "italic")[#it]
]

#show raw: set text(font: ("DejaVu Sans Mono", "Menlo", "Courier New"), size: 8.5pt)

// --- Title Block (Single Column) ---
#align(center)[
  #v(0.5em)
  #text(size: 16.5pt, weight: "bold", fill: rgb("#0f172a"))[
    Augmenting Large Language Model Writing Assistants with Formal Multi-Axis Readability and Deterministic Stylistic Feedback
  ]

  #v(0.6em)
  #text(size: 11pt, style: "italic", fill: rgb("#334155"))[
    An Empirical Multi-Arm Study on Technical Prose Quality and AI Writing Tell Mitigation
  ]

  #v(1.2em)
  #grid(
    columns: (1fr,),
    align: center,
    [
      #text(weight: "bold", size: 10.5pt)[G. H. Chinoy] \
      #text(size: 9pt, fill: rgb("#475569"))[
        Docstats Research & Engineering Group \
        `ghchinoy@users.noreply.github.com`
      ]
    ]
  )

  #v(1.0em)
  #text(size: 8.5pt, fill: rgb("#64748b"))[
    *Date:* August 2026 | *Artifact:* `docstats` MCP Tooling (`analyze_document`)
  ]
  #v(1.2em)
]

// --- Abstract Block ---
#align(center)[
  #block(
    width: 90%,
    stroke: (left: 2pt + rgb("#2563eb")),
    inset: (left: 12pt, y: 8pt),
    fill: rgb("#f8fafc"),
    radius: (right: 4pt),
    align(left)[
      #text(weight: "bold", size: 10pt, fill: rgb("#1e293b"))[Abstract] \
      #v(0.3em)
      #text(size: 9pt)[
        Large Language Models (LLMs) frequently generate technical prose saturated with synthetic stylistic tropes: throat-clearing openers, unearned binary contrast frames ("not X, it's Y"), excessive em dash clustering, and metronomic sentence rhythms. In this paper, we evaluate whether augmenting AI writing assistants with live deterministic statistical feedback via the Model Context Protocol (`docstats` MCP server) improves technical prose quality over prompt-based editorial rules alone. We formalize a two-axis framework: *Axis A* measures classical readability across 13 signals calibrated to baseline difficulty tiers, while *Axis B* measures AI writing tell density across eight syntactic and lexical detectors. We conduct a four-arm empirical study across a [#exp-doc-count]-document corpus (#exp-total-words words) spanning generated drafts, synthetic trope-heavy drafts, and human-authored controls. The experimental arms comprise: Arm A (Control / Unconstrained Polish), Arm B1 (Text-Only Editorial Rules with Gemini 3.7 Flash), Arm B2 (Text-Only Editorial Rules with Gemini 3.1 Pro Preview), and Arm C (Stats-Augmented with live closed-loop MCP feedback). Candidate revisions are evaluated by an independent blind LLM judge and paired non-parametric tests. Both editorial arms (B1 and C) significantly outperform the unconstrained baseline ($p < 0.01$, 0% Control wins). Arm C achieved top ratings in Voice Authenticity (9.18) and Rhythm (8.75), while Arm B1 led in Directness (9.14) and Information Density (9.14). In head-to-head evaluation, Arms B1 and C split wins evenly (#win-rate-b1 vs #win-rate-c), with overall scores showing no statistically significant difference ($p = 0.7253$, Wilcoxon signed-rank). We conclude that while explicit editorial guidance is essential to defeat generic AI polish, stats-augmentation on state-of-the-art base models yields targeted stylistic refinements rather than broad superiority on short technical passages.
      ]

      #v(0.5em)
      #text(size: 8.5pt)[
        *Keywords:* Large Language Models, Technical Writing, AI Writing Tells, Readability Metrics, Model Context Protocol, Wilcoxon Signed-Rank Test, Empirical Evaluation.
      ]
    ]
  )
]

#v(1.5em)

// --- Two Column Body Layout ---
#show: rest => columns(2, rest)

= Introduction

Large Language Models (LLMs) have emerged as primary tools for technical drafting, code documentation, and engineering communication [1, 7]. Despite fluent syntax and broad domain knowledge, LLM-generated technical prose exhibits recognizable stylistic pathologies—frequently termed synthetic writing tropes or "AI slop":
+ *Throat-clearing openers:* Introductory announcements before delivering substantive content (e.g., _"Here's the thing:"_, _"It's worth noting that"_).
+ *Unearned binary contrast frames:* Artificial dramatic juxtaposition (e.g., _"Not X, it's Y"_).
+ *Em dash clustering:* Excessive reliance on em dashes (`—`) to manufacture conversational intimacy or dramatic pauses.
+ *Metronomic sentence pacing:* Low variance in sentence length ($"CV" < 0.20$), resulting in monotonous cadence.
+ *Hollow significance declarations:* Vague assertions of profundity (e.g., _"The implications are profound"_).

Software engineering teams have largely addressed these patterns through *text-only prompt engineering*—supplying the model with explicit negative rule lists or editorial style rubrics [1]. However, text-only guidance operates *open-loop*: autoregressive models lack internal sensors for aggregate distributional statistics (such as sentence length coefficient of variation, overall syllable density, or formulaic grade level) across the entire text.

In this work, we evaluate a *closed-loop statistical augmentation architecture* using the Model Context Protocol (MCP) [6]. We develop `docstats`, a deterministic service that analyzes technical documents across two orthogonal dimensions:
- *Axis A (Formal Readability):* Thirteen objective readability metrics, including Flesch-Kincaid Grade Level [4], Flesch Reading Ease [2], Gunning Fog [3], and SMOG [5], calibrated against reference difficulty tiers.
- *Axis B (AI Writing Tell Density):* Eight deterministic syntactic and lexical pattern detectors with technical vocabulary allowlists, yielding an objective rolled-up $0.0$ to $10.0$ `ai_tell_score` (with an enforced floor of $>= 7.0$).

Through a controlled multi-arm empirical study spanning a [#exp-doc-count]-document corpus (#exp-total-words words) across three provenance tiers, we investigate three core research questions:
- *$Q_1$ (Quality Gain):* Does augmenting an LLM with live statistical tool feedback via MCP yield superior technical prose compared to text-based editorial guidance alone?
- *$Q_2$ (Baseline Defeat):* Does structured editorial guidance (prompt-based or tool-augmented) consistently outperform unconstrained LLM polish?
- *$Q_3$ (Model Sensitivity):* How does model family choice interact with text-only versus tool-augmented editorial workflows?

= Related Work & Foundations

== Classical Readability Metrics

Quantitative readability formulas rely on bivariate models combining syntactic length (words per sentence) and lexical complexity (syllables per word or character counts):

1. *Flesch-Kincaid Grade Level (FKG)* [4]:
$ "FKG" = 0.39 (frac(N_"words", N_"sentences")) + 11.8 (frac(N_"syllables", N_"words")) - 15.59 $

2. *Flesch Reading Ease (FRE)* [2]:
$ "FRE" = 206.835 - 1.015 (frac(N_"words", N_"sentences")) - 84.6 (frac(N_"syllables", N_"words")) $

3. *Gunning Fog Index* [3]:
$ "FOG" = 0.4 [ (frac(N_"words", N_"sentences")) + 100 (frac(N_"complex", N_"words")) ] $
where $N_"complex"$ counts words with $>= 3$ syllables.

4. *SMOG Index* [5]:
$ "SMOG" = 1.0430 sqrt(N_"polysyllables" times frac(30, N_"sentences")) + 3.1291 $

== Orthogonality of Readability and Voice Authenticity

A central premise of `docstats` is that readability and AI writing tell density represent *orthogonal axes* of document quality (@fig:orthogonality).

#figure(
  rect(
    width: 100%,
    stroke: 0.5pt + rgb("#cbd5e1"),
    fill: rgb("#f8fafc"),
    radius: 4pt,
    inset: 10pt,
    [
      #align(center)[
        #grid(
          columns: (1fr, 1fr),
          gutter: 8pt,
          align: center,
          [
            #block(fill: rgb("#fee2e2"), inset: 6pt, radius: 3pt)[
              *High Tells / Accessible*\
              #text(size: 8pt)[Beginner post saturated with throat-clearing and em dashes]
            ]
          ],
          [
            #block(fill: rgb("#dcfce7"), inset: 6pt, radius: 3pt)[
              *Low Tells / Accessible*\
              #text(size: 8pt)[*Target Zone (Dev Blog)*\
              Clear, authentic, grade 8–12]
            ]
          ],
          [
            #block(fill: rgb("#fef3c7"), inset: 6pt, radius: 3pt)[
              *High Tells / Dense*\
              #text(size: 8pt)[Architecture RFC with hollow significance and binary frames]
            ]
          ],
          [
            #block(fill: rgb("#e0f2fe"), inset: 6pt, radius: 3pt)[
              *Low Tells / Dense*\
              #text(size: 8pt)[*Target Zone (Kernel/Spec)*\
              Rigorous, concise, grade 12–16]
            ]
          ]
        )
      ]
    ]
  ),
  caption: [The Two-Axis Quality Space. Readability (Axis A) and AI-Tell Density (Axis B) are independent; a document can be formulaically simple yet stylistically synthetic.]
) <fig:orthogonality>

A text may score at an 8th-grade reading level while being saturated with AI clichés. Conversely, a formal cryptographic specification may legitimately require Grade 16 complexity while remaining free of synthetic tropes. Consequently, `docstats` rejects blended headline scores in favor of a dual-axis scorecard.

= Metrics & Multi-Protocol Architecture

The `docstats` engine is implemented in Python and exposed concurrently across three protocols: STDIO Model Context Protocol (MCP) [6], FastAPI REST endpoints, and a local CLI interface.

== Axis A: Readability Metrics & Target Bands

Axis A extracts thirteen quantitative signals from input prose, calibrated against four reference complexity tiers: Early Readers ($<6$), High School / Dev ($10–16$), Specialist / Legal ($16–22$), and Research ($>22$).

== Axis B: Deterministic AI Tell Detectors

Before computing pattern metrics, `docstats` executes an AST-aware preprocessor (`strip_code_and_tables`) that removes fenced code blocks (```` ```...``` ````), inline code spans (`` `...` ``), and markdown tables. This ensures code tokens (e.g., `def calculate_recursively()`) do not trigger false-positive prose flags.

Axis B evaluates eight distinct detectors (@tab:detectors):

#figure(
  table(
    columns: (1.2fr, 1.8fr, 1.5fr),
    align: (left, left, left),
    stroke: (x, y) => if y == 0 { (bottom: 1pt + black) } else if y == 1 { (bottom: 0.5pt + black) } else { none },
    table.header([*Tell Category*], [*Detection Logic*], [*Exceptions / Allowlist*]),
    [Em Dashes (`—`)], [Count and rate per 100 words in prose], [List item bullet separators allowed (`* Item — desc`)],
    [-ly Adverbs], [Regex matching `-ly` word endings], [24-word technical allowlist (`atomically`, `concurrently`...)],
    [High-Offender Adverbs], [Targeted lookup (`notably`, `fundamentally`, `simply`...)], [Zero-tolerance penalty],
    [Throat-Clearing], [24 compiled regex opener patterns], [Sentence-initial only],
    [Binary Contrasts], [Regex matching _"not X, it's Y"_ and _"isn't X, it's Y"_], [Technical negation excluded],
    [Wh- Declaratives], [Non-interrogative sentence-initial Wh- words], [Direct questions (`?`) allowed],
    [Staccato Fragments], [Verbless dramatic emphasis phrases (_"Full stop."_)], [Grammatical ellipsis],
    [Rhythm Metronome], [Sentence length Coefficient of Variation ($"CV"$)], [Penalty applied if $"CV" < 0.20$],
  ),
  caption: [Deterministic Axis B AI writing tell detectors and lexical allowlists.]
) <tab:detectors>

The composite `ai_tell_score` ($S_"AI" in [0.0, 10.0]$) is computed by subtracting weighted deductions from a perfect baseline:
$ S_"AI" = max(0.0, 10.0 - sum_(k) w_k D_k) $
where $D_k$ represents the normalized penalty for category $k$. A score of $S_"AI" >= 7.0$ represents the certified passing floor.

== MCP Integration: `analyze_document`

The `docstats` MCP server exposes a unified tool: `analyze_document(text)`. The tool returns a structured JSON payload containing raw statistics, readability grades, individual tell counts, diagnostic flags, and the rolled-up `ai_tell_score`.

= Experimental Design & Multi-Arm Protocol

== Experimental Arms

#figure(
  table(
    columns: (1fr, 1.5fr, 1.8fr),
    align: (left, left, left),
    stroke: (x, y) => if y == 0 { (bottom: 1pt + black) } else if y == 1 { (bottom: 0.5pt + black) } else { none },
    table.header([*Arm*], [*Model Engine*], [*Operating Context & Tooling*]),
    [*Arm A* (Control)], [Gemini 3.7 Flash], [Base model instructed to perform general technical polish without rules.],
    [*Arm B1* (Text-Only 1)], [Gemini 3.7 Flash], [Guided by full 10-rule `technical-post-editorial` prompt.],
    [*Arm B2* (Text-Only 2)], [Gemini 3.1 Pro Preview], [Same text-only editorial guidance evaluated on an alternate model family.],
    [*Arm C* (Stats-Augmented)], [Gemini 3.7 Flash], [Full editorial guidance + live closed-loop access to `analyze_document` MCP tool.],
  ),
  caption: [Multi-arm experimental conditions.]
) <tab:arms>

== Closed-Loop Feedback Loop in Arm C

Unlike Arms A and B, which execute in a single open-loop forward pass, Arm C employs an automated refinement cycle:
+ *Pre-Analysis:* The agent calls `analyze_document` on the source text to capture baseline Axis A and Axis B metrics.
+ *Drafting:* The agent generates an initial revision guided by the baseline diagnostic flags.
+ *Post-Audit:* The agent invokes `analyze_document` on its generated draft.
+ *Conditional Refinement:* If `ai_tell_score` $< 7.0$ or specific high-confidence flags are triggered, the agent executes an automated secondary refinement prompt targeting the unresolved metrics.

= Evaluation Corpus

The evaluation corpus comprises #exp-doc-count technical documents totaling #exp-total-words words (average #exp-avg-words words per document), categorized across three provenance tiers (@tab:corpus_breakdown):
1. *Tier 1: `generated_ai` (8 Documents).* Technical drafts generated by Gemini 3.7 Flash and Gemini 2.5 Flash across four software engineering topics: REST-to-gRPC, Distributed Caching, Async Job Queues, and PostgreSQL Index Tuning.
2. *Tier 2: `synthetic_curated` (3 Documents).* Technical drafts authored with deliberate, planted AI writing tropes: Server Migration (`05-sample-migration`), SDK Pagination (`06-sdk-pagination`), and Observability RFC (`07-observability-slop`).
3. *Tier 3: `public_licensed` Controls (3 Documents).* Human-authored open-source documentation: FastAPI Dependency Injection (`08-fastapi-clean`), SQLite WAL Guide (`09-sqlite-wal-guide`), and Standard Readme (`10-standard-readme`).

#figure(
  table(
    columns: (1.5fr, 1.1fr, 1fr, 1fr, 1fr, 1.5fr),
    align: (left, left, center, center, center, left),
    stroke: (x, y) => if y == 0 { (bottom: 1pt + black) } else if y == 1 { (bottom: 0.5pt + black) } else { none },
    table.header([*Doc ID*], [*Tier*], [*Words*], [*Base FK*], [*Base AI*], [*Focus / Planted Tells*]),
    [`01-rest-grpc-g37`], [`gen_ai`], [264], [13.5], [10.0], [Schema migration],
    [`01-rest-grpc-g25`], [`gen_ai`], [299], [13.5], [10.0], [Schema migration],
    [`02-caching-g37`], [`gen_ai`], [262], [15.9], [10.0], [Redis invalidation],
    [`02-caching-g25`], [`gen_ai`], [250], [16.1], [9.0], [Redis cache aside],
    [`03-queues-g37`], [`gen_ai`], [246], [15.5], [10.0], [Dead-letter queues],
    [`03-queues-g25`], [`gen_ai`], [326], [15.3], [9.2], [Backpressure handling],
    [`04-indices-g37`], [`gen_ai`], [311], [11.8], [9.7], [PostgreSQL BRIN/GIN],
    [`04-indices-g25`], [`gen_ai`], [286], [12.2], [8.2], [PostgreSQL BRIN/GIN],
    [`05-migration`], [`synthetic`], [146], [11.4], [3.2], [Throat-clearing, binary frame],
    [`06-pagination`], [`synthetic`], [128], [15.6], [0.0], [Severe em dashes & adverbs],
    [`07-observability`], [`synthetic`], [124], [12.4], [7.3], [Vague declaratives, Wh-],
    [`08-fastapi`], [`public_ctl`], [215], [10.4], [10.0], [FastAPI core docs (Clean)],
    [`09-sqlite-wal`], [`public_ctl`], [220], [10.9], [10.0], [SQLite WAL guide (Clean)],
    [`10-std-readme`], [`public_ctl`], [168], [12.4], [10.0], [Standard Readme spec],
  ),
  caption: [Evaluation corpus baseline characteristics (exact word counts and baseline scores).]
) <tab:corpus_breakdown>

= Evaluation Methodology & Statistical Rigor

== Blinded LLM Judge Protocol

For each corpus document, candidate revisions from all active arms were:
+ *De-identified:* All metadata, arm names, and system signatures were stripped.
+ *Randomized:* Assigned randomized labels ($"Candidate 1"$, $"Candidate 2"$, etc.) using a deterministic seed keyed on the document identifier.
+ *Evaluated by an Independent Judge:* A dedicated judge model instance (`gemini-3.1-pro-preview`, temperature $0.1$) scored each candidate on a 1.0–10.0 scale across Directness, Rhythm & Cadence, Voice Authenticity, Information Density, Technical Integrity, and Overall Score.

== Statistical Significance Testing

To rigorously determine whether differences between experimental arms represent meaningful improvements rather than random variance, we compute paired non-parametric *Wilcoxon signed-rank tests* [8] across per-document scores:
$ W^+ = sum_(d_i > 0) "rank"(|d_i|), quad W^- = sum_(d_i < 0) "rank"(|d_i|) $
where $d_i = x_i - y_i$ represents the paired score difference for document $i$. Exact two-tailed permutation $p$-values and rank-biserial effect sizes ($r = frac(W^+ - W^-, W^+ + W^-)$) are computed. A threshold of $alpha = 0.05$ is required to claim statistical significance.

= Empirical Results & Comparative Analysis

== Overall Judge Ratings & Dimension Breakdown

@tab:judge_results presents the aggregate performance across all #exp-doc-count documents.

#judge-results-table <tab:judge_results>

As shown in @tab:judge_results:
- *Voice Authenticity & Rhythm:* Arm C achieved the highest ratings in *Voice Authenticity* (9.18 vs 8.96 for B1) and *Rhythm & Cadence* (8.75 vs 8.71 for B1). Qualitative rationales from the judge highlighted Arm C's elimination of subtle rhetorical flourishes in favor of authentic engineering cadence.
- *Directness & Information Density:* Arm B1 achieved the highest ratings in *Directness* (9.14 vs 8.82 for C) and *Information Density* (9.14 vs 8.82 for C), producing slightly tighter prose condensations.
- *Technical Integrity:* Both Arms B1 (9.00) and C (8.75) maintained strong technical accuracy.

== Statistical Significance & Win Rates

@tab:statistical_tests presents the paired Wilcoxon signed-rank significance tests.

#statistical-tests-table <tab:statistical_tests>

Key statistical findings:
1. *Both Editorial Arms Decisively Defeat Control:* Both Arm C ($W = 8.5, r = +0.838, p = 0.0034$) and Arm B1 ($W = 1.0, r = +0.981, p = 0.0002$) demonstrate statistically significant superiority over unconstrained baseline polish (Arm A). In head-to-head rankings, Arm A received 0.0% of wins.
2. *Stats vs Text Guidance (Primary Hypothesis):* Comparing Arm C and Arm B1 on Overall Score yields $W = 46.5, r = -0.114, p = 0.7253$. The difference is not statistically significant. Both arms achieved identical #win-rate-c win rates (7 of 14 document wins each).
3. *Model Choice Dominates Open-Loop Rewriting:* Arm B1 (Gemini 3.7 Flash) significantly outperformed Arm B2 (Gemini 3.1 Pro Preview, $W = 1.0, r = +0.981, p = 0.0002$). Arm B2 produced overly rigid, metronomic sentence pacing (Rhythm score: 6.00), demonstrating that model architecture heavily influences prompt adherence.

== Objective Movement & Tell Reduction

@tab:movement summarizes the objective pre-to-post movement deltas across arms.

#movement-table <tab:movement>

All guided arms successfully reduced planted and latent tells ($Delta N_"tells" = -2.4$ on average) and maintained compliant passing scores ($S_"AI" >= 7.0$).

== Case Study Analysis

=== Case Study 1: Curated Slop Elimination (`06-sdk-pagination`)
In the synthetic pagination draft ($S_"AI" = 0.00$, 4 em dashes, 8 adverbs, 5 throat-clearers, 1 fragment; 128 words, Grade 15.64):
- *Arm A (Control):* Retained 6 adverbs ($S_"AI" = 8.00$, Judge score: 6.5). The judge noted: _"Retains too much conversational fluff, lacks technical depth."_
- *Arm B1 (Text-1):* Eliminated em dashes and adverbs ($S_"AI" = 10.00$, Judge score: 8.2).
- *Arm B2 (Text-2):* Produced a choppy, rigid rewrite ($S_"AI" = 10.00$, Judge score: 6.0, Rhythm: 4.0).
- *Arm C (Stats-Augmented):* Eliminated all em dashes, achieved $S_"AI" = 9.78$, and was ranked #1 by the judge (Score: 9.2). The judge highlighted: _"Adds a highly relevant code snippet and explains lazy evaluation clearly."_

=== Case Study 2: Clean Control Preservation (`08-fastapi-clean`)
On the human-authored FastAPI documentation ($S_"AI" = 10.00$, Grade 10.38, 0 tells; 215 words):
- *Arm A (Control):* Introduced marketing flourishes, scoring 7.2.
- *Arm C (Stats-Augmented):* Preserved the clean score ($S_"AI" = 10.00$, Grade 10.38), scoring 9.0.
- *Arm B1 (Text-1):* Produced an exceptionally crisp, instructional rewrite, scoring 9.5 and winning #1 ranking.

= Discussion & Practical Implications

== Model Architecture vs Tool Feedback

Our empirical results clarify the respective roles of base model capabilities, prompt guidance, and tool feedback:
1. *Strong Models Strongly Internalize Text Prompts:* For advanced reasoning models like Gemini 3.7 Flash, rich editorial system instructions (Arm B1) are already effective at suppressing synthetic markers on short document passages (mean overall score: 8.99).
2. *Tool Feedback Provides Targeted Refinement:* Stats-augmentation via MCP shines where prompt heuristics are ambiguous—specifically in modulating sentence rhythm variance ($"CV"$) and preventing unearned dramatic emphasis without over-condensing technical content.
3. *Over-Editing Guardrails:* The passing threshold ($S_"AI" >= 7.0$) prevents unnecessary destructive edits on already clean technical documentation.

= Limitations & Threats to Validity

+ *Corpus Length & Power:* The 14-document corpus (#exp-total-words words, ~232 words/doc) provides high precision for short technical sections but leaves the study underpowered to detect small effect sizes between strong rewriters ($p = 0.7253$).
+ *Judge Architecture:* Evaluations utilized `gemini-3.1-pro-preview` as an independent blind judge. Future evaluations should cross-validate with multi-judge panels across model families (e.g., Claude 3.7 Sonnet, GPT-4o).
+ *Single Iteration Refinement:* Arm C evaluated an automated single-cycle post-audit rather than multi-turn conversational co-editing.

= Conclusion & Future Work

In this paper, we formalized a two-axis evaluation framework for technical prose and presented an empirical evaluation of statistical metric augmentation via the `docstats` MCP server. Our multi-arm study across #exp-doc-count documents establishes that structured editorial guidance decisively outperforms unconstrained LLM polish ($p < 0.01$). Between prompt-based rules and closed-loop statistical augmentation, results are statistically comparable on short passages (#win-rate-c vs #win-rate-b1 win rate, $p = 0.7253$), with tool augmentation providing targeted advantages in Voice Authenticity and sentence rhythm.

Future work includes evaluating longer multi-page documentation trees, integrating `docstats` into Language Server Protocols (LSP) for interactive IDE workflows, and extending deterministic detectors to multi-modal technical diagrams.

// --- References Section ---
#v(1.0em)
#line(length: 100%, stroke: 0.5pt + luma(180))
#v(0.5em)

#text(size: 11pt, weight: "bold")[References]

#set text(size: 8.5pt)
#set par(leading: 0.45em, justify: false)

#grid(
  columns: (auto, 1fr),
  gutter: 6pt,
  [[1]], [T. B. Brown, B. Mann, N. Ryder, M. Subbiah, et al. 2020. _Language Models are Few-Shot Learners_. In Advances in Neural Information Processing Systems (NeurIPS 2020), 33:1877–1901. arXiv:2005.14165.],
  [[2]], [R. Flesch. 1948. _A New Readability Yardstick_. Journal of Applied Psychology, 32(3):221–233. https://doi.org/10.1037/h0057532.],
  [[3]], [R. Gunning. 1952. _The Technique of Clear Writing_. McGraw-Hill, New York.],
  [[4]], [J. P. Kincaid, R. P. Fishburne, R. L. Rogers, and B. S. Chissom. 1975. _Derivation of New Readability Formulas for Navy Enlisted Personnel_. Research Branch Report 8-75, Chief of Naval Technical Training.],
  [[5]], [G. H. McLaughlin. 1969. _SMOG Grading: A New Readability Formula_. Journal of Reading, 12(8):639–646.],
  [[6]], [Model Context Protocol Authors. 2024. _Model Context Protocol Specification_. Anthropic. https://modelcontextprotocol.io.],
  [[7]], [OpenAI. 2023. _GPT-4 Technical Report_. arXiv:2303.08774. https://doi.org/10.48550/arXiv.2303.08774.],
  [[8]], [F. Wilcoxon. 1945. _Individual Comparisons by Ranking Methods_. Biometrics Bulletin, 1(6):80–83. https://doi.org/10.2307/3001968.],
)
