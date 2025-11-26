# System Architecture: Nama Kala Wellness Hub Partnership Analysis

## Executive Summary

This document specifies the architecture for a reproducible, generalized system that transforms strategic business collaboration models into modular software artifacts suitable for replication across partners, locations, and scenarios. The system minimizes LLM invocations through structured caching, orchestrates web research and data extraction from external sources, and produces publication-ready outputs using CSV, JSON, and Carbone SDK for final PDF generation.

---

## 1. System Overview

### 1.1 Purpose and Scope

**Primary Objective:**
Generate comprehensive financial analysis and partnership feasibility reports from web research data and user-provided business context using:
- Minimal LLM calls (Gemini 2.5-Flash for synthesis only)
- Structured web research for market data and benchmarks
- Modular Python workflows for data transformation
- Configuration-driven execution via `.env` parameters
- Direct PDF generation via Carbone SDK from structured JSON

**System Scope:**
- Input: User-provided partner information, financial parameters, and configuration
- Processing: Web research orchestration, data extraction, calculations, template assembly
- Output: Integrated report (PDF via Carbone), structured data (JSON), financial tables (CSV), bibliography (BibTeX)

### 1.2 Key Architectural Principles

1. **Reproducibility:** Every execution is deterministic given identical inputs and configuration.
2. **Modularity:** Components operate independently with clearly defined interfaces.
3. **LLM Minimization:** LLM calls cached and reused; structured extraction from web results preferred.
4. **Configuration-Driven:** `.env` parameters control thresholds, paths, API credentials, output preferences.
5. **Multi-Format Output:** Single processed dataset exported to multiple formats for downstream use.
6. **Traceability:** All data transformations logged with source attribution and research provenance.
7. **Direct JSON to PDF:** Carbone SDK receives structured JSON; no Markdown or LaTeX intermediates.
8. **Web-Research-First:** Extraction operates on web search results, not input documents.

---

## 2. Core Components and Responsibilities

### 2.1 Component Architecture

```
graph TB
    Input["INPUT LAYER<br/>User Parameters<br/>Configuration .env"]
    
    Orchestrator["ORCHESTRATION LAYER<br/>Workflow Coordinator<br/>Task Sequencing<br/>State Management"]
    
    Input --> Orchestrator
    
    subgraph Processing["PROCESSING LAYER src/python/"]
        Research["Research Orchestrator<br/>Query Generation<br/>Web Search Integration<br/>Result Extraction"]
        
        Extractor["Data Extraction<br/>Web Result Parser<br/>Entity Labeling<br/>Benchmark Extraction"]
        
        Calculator["Financial Calculator<br/>Cost-Benefit Analysis<br/>Breakeven Scenarios<br/>Sensitivity Analysis"]
        
        Schema["JSON Schema Builder<br/>Entity Mapping<br/>Schema Validation<br/>Normalization"]
        
        Formatter["Output Formatter<br/>CSV Export<br/>JSON Serialization<br/>Carbone JSON Gen"]
    end
    
    Orchestrator --> Research
    Research --> Extractor
    Extractor --> Calculator
    Calculator --> Schema
    Schema --> Formatter
    
    CarboneSDK["CONVERSION LAYER<br/>Carbone SDK<br/>JSON Template Data<br/>PDF Rendering"]
    
    Formatter --> CarboneSDK
    
    Output["OUTPUT LAYER<br/>PDFs | JSON | CSV | BibTeX"]
    
    CarboneSDK --> Output
```

### 2.2 Component Definitions

#### **2.2.1 Research Orchestrator Module** (`src/python/research/`)

**Purpose:** Autonomously identify required market data and orchestrate web research to populate report content.

**Responsibilities:**
- Generate targeted search queries based on user parameters and report context
- Invoke web search tool to find market benchmarks, pricing data, and competitive analysis
- Manage research cache to avoid redundant searches
- Track research sources and citations for attribution
- Synthesize findings from multiple search results

**Key Functions:**
```
def generate_research_queries(partner_type: str, industry: str, location: str) -> List[str]
def execute_web_search(queries: List[str], cache: Dict) -> List[Dict[str, Any]]
def extract_structured_results(search_results: List[Dict]) -> Dict[str, Any]
def cache_research_findings(query_hash: str, findings: Dict, ttl_days: int = 30)
def synthesize_market_data(findings: List[Dict]) -> Dict[str, Any]
```

**Input:** User parameters (industry, location, partner type), configuration thresholds, existing research cache
**Output:** Research findings with sources, confidence scores, and synthesized benchmarks
**Cache:** Store by query hash; reuse identical research results across reports

**Orchestration Logic:**
```
For each research category needed:
  1. Generate 2-3 targeted search queries based on user context
  2. Check cache for identical or similar queries
  3. If cache hit: return cached result (verify freshness)
  4. If cache miss:
     a. Execute web search (up to 3 queries per category)
     b. Extract structured facts from search results
     c. Validate confidence scores for each finding
     d. Cache result with source attribution and timestamp
  5. Synthesize findings into coherent market narrative
  6. Flag low-confidence data for manual review
```

---

#### **2.2.2 Data Extraction Module** (`src/python/extractors/`)

**Purpose:** Parse web search results and extract structured entities for financial modeling.

**Responsibilities:**
- Extract financial benchmarks from search result snippets and summaries
- Identify pricing ranges, market growth rates, and operational metrics
- Detect and label data sources with confidence scores
- Convert unstructured web results into normalized JSON
- Track citation links and source references

**Key Functions:**
```
def extract_financial_data(search_results: List[Dict]) -> List[Dict[str, float]]
def extract_pricing_benchmarks(search_results: List[Dict]) -> Dict[str, tuple]
def extract_market_metrics(search_results: List[Dict]) -> Dict[str, Any]
def extract_source_citations(search_results: List[Dict]) -> List[Dict]
def validate_extracted_values(values: Dict) -> Tuple[bool, List[str]]
```

**Input:** Web search results from Research Orchestrator, validation thresholds
**Output:** Normalized JSON document with extracted benchmarks, confidence scores, and source attribution
**Cache:** Store extracted benchmarks keyed by source hash to detect duplicates

---

#### **2.2.3 Financial Calculator Module** (`src/python/calculations/`)

**Purpose:** Perform all financial computations deterministically using extracted benchmarks.

**Responsibilities:**
- Execute cost-benefit scenarios using extracted market data and user parameters
- Calculate break-even timelines for different business models
- Generate sensitivity analyses showing impact of market assumption variations
- Produce amortization schedules and NPV calculations
- Flag mathematical inconsistencies or unrealistic projections

**Key Functions:**
```
def calculate_operational_costs(revenue: float, config: Dict) -> Dict[str, float]
def calculate_breakeven(capex: float, monthly_profit: float) -> int
def calculate_revenue_share(revenue: float, share_pct: float, minimum: float) -> float
def generate_sensitivity_table(base_revenue: float, variance_range: List[float]) -> pd.DataFrame
def calculate_npv(cashflows: List[float], discount_rate: float) -> float
def validate_calculations(results: Dict) -> Tuple[bool, List[str]]
```

**Input:** Extracted financial amounts from research, operational parameters from config, user-provided business terms
**Output:** Computed metrics (breakeven months, NPV, ROI, scenario tables) as JSON
**LLM Usage:** Zero. All computations are deterministic and formula-based.

---

#### **2.2.4 JSON Schema Builder Module** (`src/python/schema/`)

**Purpose:** Create generalized JSON schema for coded context and downstream systems.

**Responsibilities:**
- Map extracted entities and calculated metrics to normalized schema fields
- Validate data conformance to partnership analysis schema
- Generate schema documentation (JSON Schema format)
- Export normalized data structure for APIs or integrations
- Handle schema evolution and versioning

**Key Functions:**
```
def load_base_schema(schema_version: str) -> Dict
def validate_entity_against_schema(entity: Dict, schema: Dict) -> Tuple[bool, List[str]]
def normalize_entity(entity: Dict, schema: Dict) -> Dict
def generate_schema_docs(schema: Dict) -> str
def export_to_schema_version(data: Dict, target_version: str) -> Dict
```

**Input:** Extracted research data and calculated financials, base schema definition
**Output:** Normalized JSON conforming to schema; schema documentation
**Example Schema Sections:**
- `research_context` (market_benchmarks, sources, confidence_scores)
- `partnership_terms` (revenue_share_pct, capex_investment, minimum_occupancy)
- `financial_scenario` (monthly_revenue, operational_costs, breakeven_months)

---

#### **2.2.5 Output Formatter Module** (`src/python/formatters/`)

**Purpose:** Export processed data to multiple formats and prepare Carbone JSON payload.

**Responsibilities:**
- Generate Carbone SDK compatible JSON from processed data
- Export financial tables to CSV for spreadsheet analysis
- Produce final JSON artifacts for APIs and data integration
- Build BibTeX bibliography from research source citations
- Prepare intermediary TXT output for optional LLM synthesis

**Key Functions:**
```
def generate_carbone_json(data_dict: Dict, schema: Dict) -> Dict
def export_financial_tables_to_csv(tables: Dict[str, pd.DataFrame]) -> List[str]
def serialize_to_json(data_dict: Dict[str, Any], schema: Dict) -> str
def generate_bibtex(references: List[Dict]) -> str
def generate_intermediary_txt(sections: Dict) -> str
```

**Input:** Processed research data, calculated metrics, schema, extracted content
**Output:** 
- Carbone-compatible JSON ready for SDK rendering
- Multiple artifact files in `outputs/` directory

---

#### **2.2.6 Carbone PDF Renderer Module** (`src/python/renderers/`)

**Purpose:** Generate final PDF using Carbone SDK from structured JSON payload.

**Responsibilities:**
- Initialize Carbone SDK client with API credentials
- Prepare JSON payload for Carbone Google Docs template
- Handle rendering requests and manage error recovery
- Validate PDF output integrity and file completeness
- Manage rendering timeouts and automatic retries

**Key Functions:**
```
def initialize_carbone_client(api_key: str, api_version: str = "v3") -> CarboneSDK
def prepare_carbone_payload(data: Dict, template_id: str) -> Dict
def render_to_pdf(payload: Dict, client: CarboneSDK) -> bytes
def save_pdf(pdf_binary: bytes, output_path: str) -> str
def validate_pdf_integrity(pdf_path: str) -> Tuple[bool, str]
```

**Input:** Carbone-formatted JSON data, template identifier, SDK client
**Output:** PDF binary, saved to `outputs/` directory with metadata
**SDK Usage:** `carbone-sdk>=1.0.0`

---

### 2.3 Module Interaction Matrix

| Module A | Module B | Interaction | Data Format | Frequency |
|----------|----------|-------------|-------------|-----------|
| Research Orchestrator | Data Extraction | Web search results to entity extraction | JSON (search results) | Once per category |
| Data Extraction | Financial Calculator | Extracted benchmarks to cost models | JSON | Once per report |
| Financial Calculator | JSON Schema Builder | Metrics to normalized structure | JSON | Once per report |
| JSON Schema Builder | Output Formatter | Normalized schema to formats | Dict | Once per report |
| Output Formatter | Carbone PDF Renderer | Carbone JSON payload | JSON | Once per report |

---

## 3. Directory and Module Structure (`src/python`)

```
src/
├── python/
│   ├── research/
│   │   ├── __init__.py
│   │   ├── query_generator.py       # Generate search queries
│   │   ├── web_search_client.py     # Web search integration
│   │   ├── result_parser.py         # Parse search results
│   │   ├── cache_manager.py         # Research cache local JSON
│   │   └── synthesizer.py           # Synthesize findings
│   │
│   ├── extractors/
│   │   ├── __init__.py
│   │   ├── result_extractor.py      # Extract from web results
│   │   ├── benchmark_extractor.py   # Extract pricing and metrics
│   │   ├── citation_extractor.py    # Extract source citations
│   │   └── validator.py             # Validate extracted data
│   │
│   ├── calculations/
│   │   ├── __init__.py
│   │   ├── financial_models.py      # Cost-benefit calculations
│   │   ├── breakeven_analyzer.py    # Timeline and ROI
│   │   ├── scenario_builder.py      # Sensitivity analysis
│   │   └── validators.py            # Math sanity checks
│   │
│   ├── schema/
│   │   ├── __init__.py
│   │   ├── base_schemas.py          # Define entity schemas
│   │   ├── validator.py             # Schema validation
│   │   ├── normalizer.py            # Normalize entities
│   │   └── schema_docs_generator.py # Generate JSON Schema docs
│   │
│   ├── formatters/
│   │   ├── __init__.py
│   │   ├── csv_exporter.py          # Export tables to CSV
│   │   ├── json_exporter.py         # Serialize to JSON
│   │   ├── carbone_json_builder.py  # Build Carbone payload
│   │   ├── bibtex_exporter.py       # Generate .bib files
│   │   └── txt_intermediary.py      # Generate TXT for LLM
│   │
│   ├── renderers/
│   │   ├── __init__.py
│   │   ├── carbone_renderer.py      # Carbone SDK wrapper
│   │   ├── payload_validator.py     # Validate JSON payload
│   │   └── error_handler.py         # Rendering error recovery
│   │
│   ├── orchestration/
│   │   ├── __init__.py
│   │   ├── workflow_coordinator.py  # Main execution logic
│   │   ├── error_handler.py         # Error recovery
│   │   ├── logger.py                # Structured logging
│   │   └── state_manager.py         # Cache and state
│   │
│   └── config/
│       ├── __init__.py
│       ├── config_loader.py         # Load .env and YAML configs
│       ├── validators.py            # Validate config parameters
│       └── defaults.py              # Default thresholds and paths
│
├── templates/
│   ├── carbone_template.json        # Carbone template structure
│   ├── json_schema_v1.json          # Base entity schema
│   └── carbone_config.json          # Carbone SDK parameters
│
├── tests/
│   ├── unit/
│   │   ├── test_research.py
│   │   ├── test_calculations.py
│   │   └── test_formatters.py
│   ├── integration/
│   │   └── test_end_to_end.py
│   └── fixtures/
│       └── sample_partner_config.json # Test input
│
├── .env.example                      # Configuration template
├── environment.yml                   # Conda environment spec
├── requirements.txt                  # Python dependencies
└── README.md                         # Architecture and usage guide
```

---

## 4. Data Flow and Execution Pipeline

### 4.1 High-Level Execution Sequence

1. INITIALIZATION
   - Load configuration .env
   - Initialize cache managers
   - Validate environment Python, Carbone SDK, web search access
   - Set execution logging

2. RESEARCH QUERY GENERATION
   - Analyze user parameters and report context
   - Generate targeted search queries for market data, benchmarks, pricing
   - Identify research categories needed for financial modeling
   Output: List of research queries

3. WEB SEARCH EXECUTION
   - Execute queries against web search API
   - Check research cache for existing results
   - Retrieve search results with snippets and source links
   - Cache results with timestamp and source attribution
   Output: Raw search results with metadata

4. DATA EXTRACTION FROM SEARCH RESULTS
   - Parse web search results and snippets
   - Extract financial benchmarks (pricing, market growth, costs)
   - Extract operational metrics and assumptions
   - Identify and track source citations
   - Assign confidence scores to extracted values
   Output: Structured benchmark data with sources

5. FINANCIAL CALCULATIONS
   - Load extracted benchmarks and user-provided parameters
   - Calculate cost-benefit scenarios for different business models
   - Generate breakeven analysis, NPV, ROI projections
   - Create sensitivity tables showing variance impacts
   Output: Computed metrics JSON

6. SCHEMA NORMALIZATION
   - Map extracted benchmarks and calculations to base schema
   - Validate data conformance and type consistency
   - Normalize field types and currency units
   Output: Normalized JSON ready for APIs

7. INTERMEDIARY TEXT GENERATION (Optional)
   - Generate TXT sections from normalized data
   - Prepare market findings narrative
   - Format financial summaries for LLM synthesis if needed
   - Maintain structure for Carbone consumption
   Output: Structured TXT content

8. CARBONE JSON PAYLOAD ASSEMBLY
   - Combine normalized research data, financial metrics, and narratives
   - Build Carbone template structure with all required fields
   - Prepare payment QR codes or additional visual elements
   - Validate JSON schema compliance
   Output: Complete Carbone JSON payload

9. PDF RENDERING via CARBONE SDK
   - Initialize Carbone SDK client with API key
   - Send JSON payload to Carbone renderer
   - Retrieve PDF binary from Carbone service
   - Save PDF to outputs directory with metadata

10. MULTI-FORMAT EXPORT
    - Export financial tables to CSV for spreadsheet analysis
    - Serialize normalized data to JSON for API consumption
    - Generate BibTeX bibliography from research citations
    Output: Complete artifact set

11. CLEANUP AND LOGGING
    - Archive generated files with execution metadata
    - Write execution summary and performance metrics
    - Update cache with fresh research data
    - Clean up temporary intermediaries
    Output: Final report metadata and audit trail

### 4.2 Detailed Data Flow Diagram

```
graph TD
    A["User Parameters<br/>Partner Info + Config"] --> B["Generate Research<br/>Queries"]
    
    B --> C["Research Queries<br/>List"]
    
    C --> D["Research Cache<br/>Local JSON DB"]
    
    D -->|Cache Hit| E["Return Cached<br/>Results"]
    D -->|Cache Miss| F["Execute Web<br/>Search API"]
    
    F --> G["Parse Search<br/>Results"]
    
    G --> H["Extract and Cache<br/>Benchmarks"]
    
    E --> I["Merged Research<br/>Data JSON"]
    H --> I
    
    I --> J["Financial<br/>Calcs"]
    I --> K["Schema<br/>Normalize"]
    
    J --> L["Computed<br/>Metrics JSON"]
    K --> M["Normalized<br/>Data JSON"]
    
    L --> N["Intermediary TXT<br/>Optional LLM"]
    M --> N
    
    N --> O["Carbone JSON<br/>Builder"]
    
    O --> P["Carbone Payload<br/>JSON"]
    
    P --> Q["Carbone SDK<br/>Client"]
    
    Q --> R["PDF Renderer"]
    
    R --> S["PDF Output"]
    
    L --> T["CSV Exporter"]
    M --> U["JSON Exporter"]
    I --> V["BibTeX Generator"]
    
    T --> W["Output Files<br/>CSV, JSON,<br/>PDF, BibTeX"]
    U --> W
    V --> W
    S --> W
```

### 4.3 State Management and Caching Strategy

**Cache Structure Local JSON:**

```
{
  "cache_version": "1.0",
  "last_updated": "2025-11-26T20:30:00Z",
  "research_queries": {
    "hash_abc123": {
      "query": "medical aesthetics clinic pricing Indonesia 2025",
      "cached_at": "2025-11-20T10:15:00Z",
      "ttl_days": 30,
      "results": [
        {
          "title": "Indonesia Medical Aesthetics Market Report 2025",
          "url": "https://example.com/report",
          "snippet": "Hair transplant procedures range from IDR 15.8M to 47.4M...",
          "confidence": 0.85,
          "extracted_data": {
            "pricing_min": 15800000,
            "pricing_max": 47400000,
            "currency": "IDR"
          }
        }
      ],
      "synthesis": "Market pricing shows competitive range between IDR 15.8M-47.4M"
    }
  },
  "extracted_benchmarks": {
    "hash_xyz789": {
      "extracted_at": "2025-11-26T20:00:00Z",
      "benchmarks": {
        "hair_transplant_avg_price": 37850000,
        "market_growth_rate": 0.115,
        "source": "Medihair Indonesia 2025"
      }
    }
  }
}
```

**Cache Validation Logic:**
```
def get_cached_result(query_hash: str, ttl_days: int = 30) -> Optional[Dict]:
    if query_hash not in cache["research_queries"]:
        return None
    
    cached_item = cache["research_queries"][query_hash]
    age_days = (now() - cached_item["cached_at"]).days
    
    if age_days > ttl_days:
        # Marked as stale; flag for refresh
        cached_item["stale"] = True
        return cached_item
    
    return cached_item
```

---

## 5. Design Patterns Used and Their Roles

### 5.1 Pipeline Pattern

**Usage:** Orchestrates modular processing stages with clear input and output contracts.

**Implementation:**
```
class ProcessingPipeline:
    def __init__(self, stages: List[ProcessStage]):
        self.stages = stages
    
    def execute(self, input_data: Dict) -> Dict:
        result = input_data
        for stage in self.stages:
            logger.info(f"Executing stage: {stage.name}")
            result = stage.process(result)
            self.cache_stage_output(stage.name, result)
        return result
```

**Benefit:** Modular, extensible processing; easy to insert or remove stages.

---

### 5.2 Strategy Pattern

**Usage:** Encapsulates different financial calculation strategies standalone vs. hub model.

**Implementation:**
```
class FinancialStrategy(ABC):
    @abstractmethod
    def calculate_costs(self, revenue: float) -> Dict:
        pass

class StandaloneClinicStrategy(FinancialStrategy):
    def calculate_costs(self, revenue: float) -> Dict:
        return {"rent": 20_833_333, "staff": 30_500_000, ...}

class WellnessHubStrategy(FinancialStrategy):
    def calculate_costs(self, revenue: float) -> Dict:
        return {"revenue_share": revenue * 0.12, "staff_share": 4_916_750, ...}

scenarios = {
    "standalone": StandaloneClinicStrategy().calculate_costs(285_000_000),
    "hub": WellnessHubStrategy().calculate_costs(285_000_000)
}
```

**Benefit:** Easy to add new scenarios without modifying existing logic.

---

### 5.3 Factory Pattern

**Usage:** Creates appropriate schema validators based on entity type.

**Implementation:**
```
class SchemaFactory:
    _schemas = {
        "organization": OrganizationSchema,
        "partnership_terms": PartnershipTermsSchema,
        "financial_scenario": FinancialScenarioSchema
    }
    
    @staticmethod
    def get_schema(entity_type: str) -> Schema:
        return SchemaFactory._schemas[entity_type]()

schema = SchemaFactory.get_schema("partnership_terms")
is_valid = schema.validate(extracted_entity)
```

**Benefit:** Centralized schema management; easy to extend with new entity types.

---

### 5.4 Observer Pattern

**Usage:** Tracks execution milestones and errors without coupling components.

**Implementation:**
```
class ExecutionObserver(ABC):
    @abstractmethod
    def on_stage_complete(self, stage_name: str, output: Dict):
        pass

class LoggingObserver(ExecutionObserver):
    def on_stage_complete(self, stage_name: str, output: Dict):
        logger.info(f"{stage_name} completed. Records: {len(output)}")

class CacheObserver(ExecutionObserver):
    def on_stage_complete(self, stage_name: str, output: Dict):
        self.cache_stage_output(stage_name, output)

coordinator.attach_observer(LoggingObserver())
coordinator.attach_observer(CacheObserver())
```

**Benefit:** Decoupled event handling; flexible logging and caching strategies.

---

## 6. Key Technical Decisions and Justifications

| Decision | Justification |
|----------|---------------|
| **Carbone SDK for PDF generation** | Handles complex financial tables, multi-page layouts reliably. Supports direct JSON payloads and QR code generation. Minimal overhead compared to external tool spawning. |
| **Web search as primary data source** | Eliminates need for user to provide comprehensive input documents. Current market data automatically retrieved. Reduces manual data gathering burden. |
| **CSV and JSON output formats** | CSV universally compatible for financial auditing and spreadsheet integration. JSON enables API consumption and data interchange. Reduces coupling to specific report format. |
| **Local JSON cache instead of Redis** | Simple deployment with no external dependencies. Sufficient for single-user and batch workflows. Easy to version control and archive. TTL logic handles staleness effectively. |
| **Python for orchestration** | Pandas and NumPy dominate data science workflows. Better support for web scraping and structured data extraction. Native integration with financial modeling libraries. |
| **Configuration via .env** | Simpler for non-technical stakeholders to modify. Integrates directly with environment variables for cloud deployment. Fewer parsing errors than YAML. |
| **Minimize LLM calls via structured extraction** | Deterministic extraction from web results costs approximately USD 0.001 per document versus LLM costs USD 0.01-0.10. Caching research reduces calls by 70 percent. |
| **BibTeX for bibliography** | Supports cross-document citation consistency. Integrates with reference management systems. Reusable across reports and partners. |

---

## 7. Critical Implementation Paths

### 7.1 Minimal LLM Call Path (Preferred)

```
User input parameters
     |
     v
Generate research queries based on context
     |
     v
Lookup research cache hash-based query lookup
     |------ Cache HIT: Return cached findings
     |
     |------ Cache MISS: Execute web search
                |
                v
             Extract benchmarks from results
                |
                v
             Validate confidence scores
                |
                v
             Cache results
     |
     v
Perform calculations formulas, no LLM
     |
     v
Inject into Carbone JSON variable substitution
     |
     v
Render PDF via Carbone SDK
     |
     v
Export to multiple formats

Result: Zero LLM calls for 80% of reports cache hits
        Up to 1 LLM call for narrative synthesis if needed
```

**Cost Impact:** Approximately USD 0.0015 per document versus USD 0.10 or more for full LLM processing

### 7.2 Full Processing Path (Fallback)

```
If extraction confidence less than 0.70 or significant gaps detected:

User input parameters
     |
     v
LLM Call 1: Enhance research queries with context
    Prompt: "Generate targeted web search queries to find market data
    for medical aesthetics clinic in Indonesia"
     |
     v
Execute web search with enhanced queries
     |
     v
Extract benchmarks from results
     |
     v
[Rest of pipeline identical]
     |
     v
LLM Call 2 optional: Synthesize research findings into narrative
    Only if multiple research gaps or conflicting data identified
     |
     v
Render PDF via Carbone SDK

Cost: USD 0.02-0.05 per document still 50% lower than 
naive full LLM approach
```

### 7.3 Error Recovery Path

```
At ANY pipeline stage:

If error occurs:
     |
     v
1. Log error with full context input, parameters, stack trace
2. Check if partial output is usable graceful degradation
     |
     |---- YES: Mark as partial_success, output what's available
     |
     |---- NO: Escalate to manual review queue
     |
     v
3. Update cache with FAILED marker TTL = 1 hour
4. Notify operator via email and logging
5. Continue pipeline with default benchmarks from config if configured

Example: If web search times out on query 2 of 3
    - Mark that research gap as no_data_available
    - Use industry default benchmark from config
    - Flag for manual verification
    - Continue to next pipeline stage
```

---

## 8. Error Handling Strategy

### 8.1 Error Classification and Recovery

| Error Type | Detection | Recovery Action | Fallback |
|-----------|-----------|-----------------|----------|
| **Web Search Timeout** | HTTP timeout after 30 seconds | Retry query once with exponential backoff | Use cached default benchmark |
| **Low Confidence Extraction** | extracted_confidence less than 0.70 | Flag data for manual review | Mark as low_confidence in output |
| **Calculation Math Error** | Division by zero, NaN detection | Log error, use conservative default | Set to zero, flag as error |
| **Carbone SDK Error** | Non-200 response code | Retry up to 3 times with exponential backoff | Save as JSON, notify user |
| **Schema Validation Failure** | JSON schema mismatch | Attempt auto-correction via type coercion | Output with schema_non_compliant flag |
| **File I/O Error** | FileNotFoundError, permission denied | Check path permissions, create directories | Store in temporary directory |

### 8.2 Retry Logic with Exponential Backoff

```
# src/python/orchestration/error_handler.py

from tenacity import retry, stop_after_attempt, wait_exponential

class ErrorHandler:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def execute_with_retry(self, func, *args, **kwargs):
        """Execute function with exponential backoff retry."""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Attempt failed: {e}")
            raise
    
    def graceful_degradation(self, func, *args, default_value=None, **kwargs):
        """Execute function; return default on failure."""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Function failed, returning default: {e}")
            return default_value
```

---
