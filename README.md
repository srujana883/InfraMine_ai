# InfraMiner AI
**A Multi-Agent Framework for Sustainable Resource Sourcing and Resilience Planning in Large-Scale Infrastructure Projects**

---

## 1. Project Overview & Problem Statement

Mega-infrastructure projects—such as major deep-water ports, coastal highways, and reclamation works—require tens of millions of tonnes of construction materials (rock armour, aggregates, fill murrum, marine sand, and high-performance precast concrete elements). Traditionally, Detailed Project Reports (DPRs) are analyzed manually, leading to:
- Sub-optimal sourcing decisions focused solely on shortest distance or initial quoted price.
- Failure to account for environmental footprints, such as quarry haulage emissions, CRZ sensitivity, and marine dredging restrictions.
- Severe operational disruptions caused by single-source dependencies, seasonal monsoon closures, or transport corridor failures.
- Unintentional fabrication or extrapolation of missing commercial or environmental data.

**InfraMiner AI** addresses this through a multi-agent AI framework with an in-memory sequential architecture. It ingests complex DPR documentation, identifies material requirements, matches verified physical quarries and maritime sources, evaluates multi-criteria trade-offs (cost, logistics, carbon footprint, resilience), and computes mathematically consistent sourcing plans with explicit contingency fallbacks.

---

## 2. Frozen 4-Agent Architecture

The InfraMiner AI architecture consists of four specialized, sequentially coupled agents operating on a shared in-memory state (`InfraMinerState`):

```
                       [ Project DPR Document (PDF) ]
                                      ↓
      ┌──────────────────────────────────────────────────────────────┐
      │         Agent 1: Project & Material Intelligence             │
      │  • DPR Keyword Retrieval & Persistent Indexing              │
      │  • Multi-Tier Structured Extraction (Tool Call / JSON Schema)│
      │  • Zero-Fabrication Preservation of Null / Unstated Values   │
      └──────────────────────────────┬───────────────────────────────┘
                                     ↓
                  [ Project Identity + Material Requirements ]
                                     ↓
      ┌──────────────────────────────────────────────────────────────┐
      │                Agent 2: Source & Logistics                   │
      │  • Dynamic Material-to-Source Mapping                        │
      │  • Multimodal Route Calculation (Road, Rail, Marine)         │
      │  • Haversine & Ministry Verified Distance Lookup             │
      └──────────────────────────────┬───────────────────────────────┘
                                     ↓
                    [ Matched Sources + Logistics Routes ]
                                     ↓
      ┌──────────────────────────────────────────────────────────────┐
      │         Agent 3: Cost, Environment & Resilience              │
      │  • Schedule-of-Rates (SoR) Freight & Extraction Costing      │
      │  • Ecological Footprint & CRZ Constraint Assessment          │
      │  • Supply Disruption Modeling (Monsoon & Capacity Shocks)     │
      └──────────────────────────────┬───────────────────────────────┘
                                     ↓
                  [ Evaluated Source Alternatives & Criteria ]
                                     ↓
      ┌──────────────────────────────────────────────────────────────┐
      │                 Agent 4: Decision (AHP-TOPSIS)               │
      │  • Analytic Hierarchy Process (AHP) Matrix Consistency Check │
      │  • Vector-Normalized TOPSIS Multi-Criteria Ranking           │
      │  • Physical Source Deduplication & Threshold Viability (0.30)│
      │  • Primary Recommendation & Contingency Fallback Plan        │
      └──────────────────────────────┬───────────────────────────────┘
                                     ↓
                    [ Executive Sourcing & Resilience Plan ]
```

---

## 3. The Four Agents in Detail

### Agent 1 — Project & Material Intelligence
- **Role:** Ingests the DPR PDF via page-level persistent indexing (`src/utils/document_index.py`), retrieves relevant sections across 5 categories (Identity, Location, Scope, Timeline, Constraints), and extracts structured material requirements.
- **Reliability & Multi-Tier Fallback:** Employs a three-tier extraction engine:
  1. *Primary:* Standard LangChain tool calling (`with_structured_output`).
  2. *Secondary:* Token-level grammar schema enforcement (`method="json_schema"`), followed by `"json_mode"`.
  3. *Tertiary:* Controlled direct JSON extraction with strict Pydantic validation (`MaterialRequirement`).
- **Integrity Rule:** Strictly preserves `None` for unstated coordinates, quantities, or grades (zero fabrication).

### Agent 2 — Source & Logistics
- **Role:** Maps extracted material requirements to candidate supply sources using verified regional datasets (`data/sources/verified_material_sources.csv`).
- **Logistics Modeling:** Computes distances and transport routes for road, rail, and maritime corridors, generating 1-to-1 route linkages for each source-material pairing.

### Agent 3 — Cost, Environment & Resilience
- **Role:** Evaluates each candidate source across three dimensions:
  1. *Cost:* Computes extraction and freight costs based on official Schedule of Rates (SoR). If commercial purchase prices are unstated, tags them as `calculated` or `unavailable` without inventing market prices.
  2. *Environmental:* Assesses quarry land footprint, marine dredging regulations, and haulage emissions. Applies neutral mathematical baselines where numerical scores are unpublished.
  3. *Resilience:* Evaluates source availability risk, multi-supplier redundancy, and disruption vulnerability against regional scenarios (`data/resilience/verified_disruption_scenarios.csv`).

### Agent 4 — Decision (AHP-TOPSIS)
- **Role:** Synthesizes multi-criteria trade-offs into an operational sourcing decision.
- **AHP Weighting:**
  $$\text{Cost: } 0.2685 \quad|\quad \text{Logistics: } 0.1213 \quad|\quad \text{Environmental: } 0.1899 \quad|\quad \text{Resilience: } 0.4203$$
  - Verifies matrix consistency: $\lambda_{\max} = 4.0709$, $\text{CI} = 0.0236$, $\text{CR} = 0.0262 < 0.10$ (Strictly Consistent).
- **TOPSIS Closeness Coefficient:** Ranks normalized Euclidean distance from positive and negative ideal solutions ($C_i = d_i^- / (d_i^+ + d_i^-)$).
- **Physical Deduplication:** Deduplicates alternatives using the composite identity `(source_id, material_name)`, preventing repeated entries for the same quarry.
- **Viability Threshold Rule:** Alternatives with $C_i < 0.30$ are classified as `NON-VIABLE` and cannot be recommended as primary or fallback sources.

---

## 4. Resilience & Contingency Sourcing Logic

Resilience is a core objective of InfraMiner AI. The system explicitly addresses:
> *"If the selected primary source becomes unavailable or its transport route is disrupted, what feasible alternative source ensures uninterrupted construction?"*

1. **Source Resilience (Level 1):** For each material, identifies the primary source and ranks distinct physical alternative quarries (e.g. Hillock B backed by Hillock D, Hillock E, Hillock F).
2. **Logistics Resilience (Level 2):** Evaluates alternative transport corridors (overland road vs coastal maritime barging).
3. **Resilience Statuses:**
   - `RESILIENT`: Multiple feasible, viable fallback quarries identified.
   - `LIMITED RESILIENCE`: Exactly one alternative supplier identified.
   - `SINGLE-SOURCE DEPENDENCY`: No alternative supplier available; explicit risk warning issued.
   - `NO VIABLE SOURCE`: All candidate sources fail the multi-criteria viability threshold ($< 0.30$).

---

## 5. Verified Data Sources (Vadhavan Port Project)

InfraMiner AI utilizes verified regional infrastructure datasets grounded in Maharashtra State mining surveys, CIDCO/MMRDA regional plans, and the official Vadhavan Port DPR (May 2023):
- **Sources Dataset:** `data/sources/verified_material_sources.csv` (17 verified captive quarries, casting yards, and dredging borrow pits).
- **Cost Dataset:** `data/costs/verified_cost_data.csv` (Documented tariffs and calculated freight rates).
- **Environmental Dataset:** `data/environmental/verified_environmental_factors.csv` (Ecological sensitivity and haulage emission factors).
- **Resilience Scenarios:** `data/resilience/verified_disruption_scenarios.csv` (Monsoon wave height thresholds, coastal road congestion).

---

## 6. How to Run the Application

### Prerequisites
- Python 3.10+ (Recommended: Python 3.12)
- Virtual environment activated (`venv\Scripts\activate` on Windows)

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Launching the Streamlit Web Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.
1. Select the bundled Vadhavan Port DPR or upload a custom project PDF.
2. Click **"🚀 Analyze DPR (Execute 4-Agent Pipeline)"**.
3. View real-time status across all four agents, interactive data tables, decision rankings, and contingency plans.
4. Click **"📥 Download Executive Decision Report (PDF)"** to generate a publication-grade report.

### Running via Backend CLI
```bash
python src/main.py documents/raw/Vadhavan-DPR_May-2023.pdf
```

---

## 7. Testing & Verification Commands

All tests execute in-memory against verified project datasets without requiring intermediate saved JSON files:

```bash
# 1. Agent 1 Unit Validation (LLM Extraction & Schemas)
python test_agent1_validation.py

# 2. Agent 2 Unit Validation (Source Matching & Routes)
python test_agent2_validation.py

# 3. Agent 3 Unit Validation (Cost, Environment & Resilience)
python test_agent3_validation.py

# 4. Agent 4 Unit Validation (AHP-TOPSIS Mathematical Integrity)
python test_agent4_validation.py

# 5. Live Multi-Agent Pipeline Test (In-Memory Sequential Workflow)
python test_live_pipeline.py

# 6. Full Pipeline Integration Test (31 Schema & Integrity Checks)
python test_full_pipeline.py

# 7. UI & Application 24-Criteria Integration Test
python test_ui_application.py
```

---

## 8. Known Limitations & Governance Notice
- **Decision-Support Scope:** InfraMiner AI is an automated decision-support system. Sourcing evaluations tagged as `PROVISIONAL_INDICATIVE` reflect publicly disclosed DPR information.
- **Statutory Approvals:** Formal competitive tender bidding, physical quarry core drill sampling, and statutory environmental clearances (CRZ / MoEFCC / MPCB) remain legally mandatory prior to commercial contract awards.
- **LLM Variance:** The material requirement extraction step utilizes Groq LLM inference; while schemas and outputs are strictly validated by Pydantic models, material counts may vary slightly across runs depending on context retrieval partitioning.

