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

An experimental literary journal with complete, auditable machine interviews. Case 001 is computer-10. Do not invent further cases, model quotes, observations, or clinical diagnoses. The as-if-conscious premise is an interpretive convention. Preserve objections and full outputs, including failures and token caps.

- `content/case-001.json` holds editorial copy and quote references.
- `public/data/case-001.json` holds original inference records. Never edit outputs for style.
- `scripts/build.mjs` renders all views as static HTML; `npm run build`.
- `npm run check` checks hashes, the conversation chain, frozen probe coverage, quotes, and anchors.
- `npm start` serves on port 8790 locally, or PORT. `/healthz` exposes the Git SHA captured by the Docker build.
- Follow frontend-quality for desktop and narrow browser checks. Follow vps-operations and Deploy Manager for deployment. Hosting is the existing VPS, at cure.alirezaafshan.com, once verified deployed.
- No runtime model API, GPU, credentials, user chat storage, or third-party analytics belong in this site.
- Research protocol and inference code: sibling llm-research/experiments/E010-talking-cure. Additional cases need separate immutable model identity, raw records, neutral/leading probes, and explicit limitations.
