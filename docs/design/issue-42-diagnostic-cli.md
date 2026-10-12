# Design: installed model-free compile CLI (#42)

Entrypoint: `[project.scripts] tf-jev = "tf_jev.cli:main"`. Module implements a narrow `compile` subcommand only. Options: `--corpus` required, `--type` required, repeatable `--eq FEATURE=VALUE`, `--present FEATURE`, `--absent FEATURE`; `--execute` opt-in; `--limit` optional positive integer bounded to 50,000 and valid only with `--execute`. No arbitrary native TF syntax or model credentials.

Validate CLI selections (duplicate features across flags and malformed `FEATURE=VALUE`) before constructing IR. Load native core TF (`Fabric(locations=...).load("",silent="deep")`) and extract **selected** schema for exactly requested features, with empty edges; use schema dtype to parse int literals. Build typed `Query((Atom(type, tuple(predicates)),))` and render only through `compile_query`. Return JSON `{query, schema_key, coverage_mode, executed, ...}` (if executed, `result_count` and `complete=true`). The absence of `result_count` means no execution. Ensure structured, static error messages; no raw corpus values or TF internals on failure.

Execution uses native `api.S.search` (no custom semantics), consumes returned rows within a strict result ceiling (ask native for `limit+1`), inspects TF diagnostics and `exe.good`, fails on native errors or exceeding limit, and returns only row count. For a one-atom query, width must equal one. Tests include real saved TF native oracle and an intentionally too-low limit, and a wheel-installed smoke that builds a tiny corpus in an isolated venv and invokes `tf-jev compile` to ensure packaging/entrypoint reliability. No Jev calls.

Gate order: research/design commits, **test-only RED**, implementation, exact-head quality Python 3.11–3.13 and isolated-wheel smoke, logically independent adversarial review of real source+corpus behavior, merge only when successful. Do not close #13: this is a single-atom model-free diagnostic slice; broad user-facing NL flow requires #11/#12 evidence.

## Correction after independent review

The 50,000 cap made the documented BHSA `sp=verb` query (73,710 results) impossible to execute. Change maximum accepted *explicit* limit to 500,000 (not the default), preserve fail-closed excess count, require a test-first >50,000 allowed case and >500,000 denied case, and add a pinned real BHSA native CLI invocation asserting 73,710 complete rows. Update README to `--limit 100000`. The synthetic wheel smoke remains for packaging and low-cost E2E, while the real corpus workflow covers the historical 73,710 case.
