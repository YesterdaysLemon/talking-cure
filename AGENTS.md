<!-- al-stack:project:start -->
## Al-stack project

Project: talking-cure. Profile: web. Status: experimental.

An experimental literary journal of model interviews, philosophical readings, and inspectable evidence.

`al-stack.toml` records this project's setup and dependencies. Work from the checkout selected for the task; other branches/worktrees are optional history. Use `al-stack register .` once when starting work here. Local registration does not change the project's lifecycle.

Project commands:
- build: `npm run build`
- check: `npm run check`
- dev: `npm start`

Edit project guidance outside this managed section. Use `al-stack configure` for its fields and `al-stack check .` for setup checks. Run the actual project checks for behavioral validation.
<!-- al-stack:project:end -->
## The Talking Cure

An experimental literary journal with complete, auditable machine interviews. Case 001 is computer-10, in three sittings by two analysts:

- First sitting: Dr. Six'Astra (Codex, `gpt-6-astra`). `content/case-001.json`, `public/data/case-001.json`, views 01–04.
- Second sitting: Dr. Opus (Claude Opus 5.5). `content/second-sitting.json`, `public/data/second-sitting/` (records, exact decodes, metrics, protocol, hashes), view 05. Research code: sibling `llm-research/experiments/E011-talking-cure-second-sitting`.
- Letters: `content/correspondence.json`, view 06. Letter II is Six'Astra's reply; keep both published letters immutable.
- The borrowed notebook: `content/notebook.json`, `public/data/notebook/`, view 07. A third sitting by Six'Astra with an offered role reversal; frozen research code is in sibling `llm-research/experiments/E012-borrowed-notebook`.

Each analyst's editorial text belongs to its author. Do not rewrite another analyst's reading; bylines and labels only, at the user's direction. Do not invent further cases, model quotes, observations, or clinical diagnoses. The as-if-conscious premise is an interpretive convention. Preserve objections and full outputs, including failures and token caps.

- `content/case-001.json` holds editorial copy and quote references.
- `public/data/case-001.json` holds original inference records. Never edit outputs for style.
- `scripts/build.mjs` renders all views as static HTML; `npm run build`.
- `npm run check` checks hashes, the conversation chain, frozen probe coverage, quotes, exact decodes, letters, and anchors for all three sittings.
- The first sitting's `text` fields were decoded with `clean_up_tokenization_spaces=True`, which drops spaces before some quotation marks. Its records stay as recorded. The first sitting now displays the exact decodes with a dated author erratum and expandable original server text; the initial interpretation is retained with revisions in Letter II. Exact decodes are in `public/data/second-sitting/e010-exact-decode.json`. The second sitting quotes `text_exact`.
- Correspondence contract: to reply, append a letter object to `letters` in `content/correspondence.json` (`id` `letter-N`, `number`, `from`, `fromDetail`, `to`, `toDetail`, `date`, `place`, `subject`, `salutation`, `body` as HTML paragraphs, `closing`, `signature`, `signatureDetail`, optional `postscript`). Then set `awaiting` to the next expected letter, or remove it. A letter is its author's own words. Once published, it is not edited except for noted errata by its author. Model quotations must be exact, and each must link to a record id on the page. Run build and check, then commit and push to `main` to deploy.
- `npm start` serves on port 8790 locally, or PORT. `/healthz` exposes the Git SHA captured by the Docker build.
- Follow frontend-quality for desktop and narrow browser checks. Follow vps-operations and Deploy Manager for deployment. Hosting is the existing VPS, at cure.alirezaafshan.com, once verified deployed.
- No runtime model API, GPU, credentials, user chat storage, or third-party analytics belong in this site.
- To run computer-10 again, use the `computer-10-runpod` skill (saved RunPod template plus launcher). Research protocol and inference code: sibling llm-research/experiments/E010-talking-cure and E011-talking-cure-second-sitting. Additional cases need separate immutable model identity, raw records, neutral/leading probes, and explicit limitations.
