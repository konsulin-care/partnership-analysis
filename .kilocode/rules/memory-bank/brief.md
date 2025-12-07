This architecture enables reproducible, modular analysis of strategic partnership models by combining web research with deterministic financial modeling and direct PDF generation via Carbone SDK. The system is designed for replication across different partners, locations, and scenarios with configuration-driven flexibility and comprehensive error handling.

**Key Features:**
- **Complete End-to-End Pipeline**: 11-step orchestration from user input to final PDF report generation
- **Deep Research Engine**: Iterative LLM-driven research with up to 3 iterations for comprehensive brand analysis
- 70% reduction in LLM calls through caching and structured extraction from web results
- Brand-specific research queries generated from BRAND_NAME, BRAND_ABOUT, BRAND_INDUSTRY parameters
- Modular component design for ease of extension and modification
- Deterministic, auditable calculations based on market research
- Multi-format output CSV, JSON, PDF via Carbone SDK
- Configuration-driven execution for non-technical users
- Production-ready error handling and logging with retry logic and graceful degradation
- Web-research-first approach eliminates need for comprehensive input documents
- Direct JSON to PDF conversion using Carbone SDK
- Partnership-focused final synthesis for collaboration opportunities
- Comprehensive test coverage with 115+ unit and integration tests
