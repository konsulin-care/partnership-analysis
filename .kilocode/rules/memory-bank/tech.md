# Technologies and Frameworks

- Python 3.11 with Conda environment management
- Pandas and NumPy for financial calculations and tabular data handling
- Carbone SDK (Python) for JSON to PDF rendering using Google Docs templates
- JSON Schema for structured context validation and normalization
- BibTeX for reference and citation management in generated reports
- Google Gemini AI (Gemini-2.0-Flash for research, Gemini-2.5-Flash for synthesis)

# Development Setup

- Project structured under `src/python` with separate packages for research, extraction, calculations, schema, formatters, renderers, orchestration, and config
- Orchestration layer provides complete 11-step pipeline coordination with error recovery and state management
- Environment defined via `environment.yml` and `.env` files, loaded by a dedicated `ConfigLoader` module
- Local JSON files used for research caching, configuration defaults, and schema definitions
- Tests organized into `tests/unit` and `tests/integration` with fixtures under `tests/fixtures`
- Extensive tests marked with `@pytest.mark.extensive` and skipped by default (run with `-m extensive`)
- Custom pytest configuration in `tests/conftest.py` for marker registration and skipping logic

# Technical Constraints

- Minimize LLM usage by preferring deterministic extraction and caching of web research results
- No Markdown or LaTeX based PDF generation; all final rendering goes through Carbone SDK from JSON payloads
- Web search limited to a small number of targeted queries per data gap, with TTL-based cache to avoid repeated calls
- Schema strict mode can be enabled to enforce JSON schema conformance during normalization

# Dependencies and Tool Configuration

- Core Python dependencies: `pandas`, `numpy`, `requests`, `python-dotenv`, `jsonschema`, `marshmallow`, `structlog`, `python-json-logger`
- Pip-only dependencies: `carbone-sdk`, `bibtexparser`, `jinja2`, `markdown`, `httpx`, `tenacity`, `slugify`, `click`, `pydantic`
- `.env` parameters configure research limits, discount rates, CAPEX amortization, file paths, logging, and Carbone credentials
- Carbone configuration stored in `templates/carbone_config.json` and referenced by the renderer module

# Tool Usage Patterns

- Research orchestrator generates queries, checks cache, then calls web search when needed; extracted benchmarks feed financial calculators
- Deep research engine performs iterative LLM-driven research with up to 3 iterations, using Gemini models for query refinement, synthesis, and question generation
- Output formatter converts normalized data and metrics into CSV, JSON, BibTeX, and Carbone JSON payloads for rendering
- Carbone renderer wrapper initializes the SDK client, sends JSON payloads, and writes PDF binaries to the `outputs` directory
- Error handler applies exponential backoff retries for web search and Carbone calls, with graceful degradation and default fallbacks on failure
- Workflow coordinator orchestrates the complete 11-step pipeline with stage execution, error recovery, and state management
- Performance benchmarks use extensive testing markers to skip time-consuming tests by default
