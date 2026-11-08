# Real Agent 3 Data Report: Cost, Environment & Resilience Baseline

**InfraMiner AI Framework**  
*Project:* Vadhavan Port Multi-Agent Resource Sourcing & Resilience Planning  
*Scope:* Agent 3 — Cost Analysis, Environmental Assessment, and Resilience Assessment  
*Status:* Verified Real-World Document-Supported Baseline Established  

---

## Executive Summary

This report establishes the factual, document-supported data foundation for **Agent 3 (Cost, Environment & Resilience)** of the InfraMiner AI system. In strict adherence to project guidelines:
1. **Zero Fabrication:** No arbitrary unit costs, supplier quotes, numerical environmental scores, disruption probabilities, or severity ratings were invented.
2. **Preservation of Demonstration Datasets:** Existing baseline demonstration files (`data/costs/cost_data.csv`, `data/environmental/environmental_factors.csv`, `data/resilience/disruption_scenarios.csv`) remain completely untouched.
3. **Dedicated Real Datasets Created:**
   - [`data/costs/verified_cost_data.csv`](file:///C:/Users/SRUJANA/Desktop/InfraMine_ai/data/costs/verified_cost_data.csv) (32 records)
   - [`data/environmental/verified_environmental_factors.csv`](file:///C:/Users/SRUJANA/Desktop/InfraMine_ai/data/environmental/verified_environmental_factors.csv) (13 records)
   - [`data/resilience/verified_disruption_scenarios.csv`](file:///C:/Users/SRUJANA/Desktop/InfraMine_ai/data/resilience/verified_disruption_scenarios.csv) (9 scenarios)
   - [`data/agent3_provenance.csv`](file:///C:/Users/SRUJANA/Desktop/InfraMine_ai/data/agent3_provenance.csv) (54 traceable provenance records)

---

## 1. Documents Consulted & Page References

All data points originate from official primary and reference documents downloaded in `documents/raw` and `documents/reference`:

| Document Name | File Path | Focus Area & Extracted Sections |
| :--- | :--- | :--- |
| **Vadhavan Detailed Project Report (DPR)** | `documents/raw/Vadhavan-DPR_May-2023.pdf` | Chapter 14 Cost Estimates (p331-334 / PDF p357-360 Table 14-1, 14-2); Chapter 2 Project Description (p68-72); Chapter 13 Oceanography & Sedimentation (p332-340). |
| **Road Connectivity DPR (VPPL)** | `documents/reference/Road-Connectivity-DPR-VPPL.pdf` | Chapter 8 Cost Estimates (p22-23 Table 1-7, p104-106 Table 8-1); Chapter 1 & 7 Material Sourcing (p21 Table 1-5, p94-95 Table 7-1, 7-2, 7-3). |
| **Rail Connectivity DPR (VPPL)** | `documents/reference/Rail-Connectivity-DPR-VPPL.pdf` | Chapter 13 & 14 Detailed Cost Estimates (p21-22 Table 0-2, p83-86 Table 13-1, 13-2, p92-94 Formation & Earthwork Annexure). |
| **Comprehensive EIA Report (VPPL)** | `documents/reference/EIA-VPPL-Jan-2024_043228.pdf` | Chapter 10 Environmental Management Plan & EMP Budget (p570-579 / PDF p616-625 Tables 161, 162, 163, 164, 165); Chapter 4 Environmental Impacts (p187, p284, p420). |
| **Gargaon Quarry EIA Executive Summary** | `documents/reference/Vadhvan_patch_1_Gargaon_17.08_Executive_Summary_(English)_R2_29062026.pdf` | Section 1 & 2 Lease Area, Mineable Reserves, Forest Land Diversion (p7, p10, p13-14). |
| **Khanivade Quarry EIA Executive Summary** | `documents/reference/Vadhvan_patch_5_Khanivade_15.39_Ha_Executive_Summary_(English)_R2_29062026.pdf` | Section 1 & 2 Lease Area, Mineable Reserves, Forest Land Diversion (p7, p11, p14). |
| **Public Hearing Minutes (Gargaon & Khanivade)** | `documents/reference/2_Gargaon_17.08_Ha_English_Minutes.pdf`, `3_Khanivade_15.39_Ha_English_Minutes.pdf` | Public objections, groundwater protection, dust impact on horticulture orchards, blasting vibrations (p2-5). |
| **Ministry of Mines Sand Reservation Gazette** | `documents/reference/Vadhavan-Mines-OAMDR-Act-Reservation-for-JNPA-21.12.23-app.pdf` | Official Gazette S.O. 5411(E) dated 21.12.2023 under Section 17A(1) of OAMDR Act 2002 reserving 102.77 sq.km offshore Daman. |
| **EPC Package 1A Breakwater Tender** | `documents/reference/Package-1A-Breakwater.pdf` | Section 1 & 2 Technical criteria, Accropode II specifications, 100-year cyclone wave design, seasonal shutdown (p7-10, p13-18). |
| **EPC Package 2B Offshore Reclamation Tender** | `documents/reference/Package-2B-Off-Shore-Reclamation-and-Dredging-on-PPP-HAM-.pdf` | HAM model structure, approach channel dredging, beneficial reuse of dredged material (p1-6). |
| **Maharashtra PWD State Schedule of Rates 2022–23** | `documents/reference/state_rates.pdf` | Chapter 49 Coastal Engineering Items 1678 to 1724 (p320-328 / PDF p327-335); General Notes (p7-13); Lead Statement C-1 (p551-567). |

---

## 2. Summary of Verified Datasets Created

| Dataset File | Total Records | Directly Documented Numerical | Calculated Derived Numerical | Qualitative / Descriptive | Missing Numerical (NULL) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`verified_cost_data.csv`** | **32** | **27** | **2** | **0** | **3** |
| **`verified_environmental_factors.csv`** | **13** | **5** | **0** | **8** | **8** |
| **`verified_disruption_scenarios.csv`** | **9** | **0** | **0** | **9** | **9** (prob & sev) |
| **`agent3_provenance.csv`** | **54** | Full cross-dataset audit trail connecting each row to page-level citations |

---

## 3. Cost Data Evidence & Numerical Values Found

### A. Directly Documented Capital Block Costs (DPR Table 14-1)
- **Breakwater Infrastructure (Phase 1):** `INR 5,361 Crores` (53,610,000,000 INR).
- **Offshore Land Platform Reclamation:** `INR 9,321 Crores` (Phase 1), `INR 2,586 Crores` (Phase 2); `Total: INR 11,907 Crores` (119,070,000,000 INR).
- **Shore Protection & Revetment Works:** `INR 2,381 Crores` (Phase 1), `INR 1,111 Crores` (Phase 2); `Total: INR 3,492 Crores` (34,920,000,000 INR).
- **Navigation Channel Capital Dredging:** `INR 936 Crores` (Phase 1), `INR 2,016 Crores` (Phase 2); `Total: INR 2,952 Crores` (29,520,000,000 INR).
- **Common Support Infrastructure Reclamation:** `INR 271 Crores` (2,710,000,000 INR).
- **Road Expressway Civil Works:** `INR 1,944 Crores` civil; `Earthwork: INR 397 Crores`; `Flexible Pavement: INR 214 Crores`; `Total with inflation: INR 2,449 Crores`.
- **Rail Connectivity Infrastructure:** `Phase 1 Civil Works: INR 888.42 Crores`; `Formation & Earthwork: INR 187.57 Crores`; `P-way materials: INR 61.81 Crores`; `Total Phase 1: INR 1,276.53 Crores`.

### B. Directly Documented Operating & Base Utility Rates (DPR Section 14.3.4)
- **Diesel Fuel:** `INR 100.00 per litre`.
- **Industrial / Port Power:** `INR 9.20 per kWh` plus `INR 432 per MVA` monthly demand charge.
- **Water Tariff:** `INR 150.00 per kilolitre` (kL).

### C. Calculated Derived Unit Costs
- **Breakwater Rock Overall Unit Cost:** `INR 1,670.09 per tonne`  
  *Derivation:* Breakwater Phase 1 Capex (`INR 53,610,000,000`) divided by documented breakwater rock requirement (`32,100,000 tonnes`). Represents the true composite EPC cost of sourcing, transporting, sorting, placing core, underlayer, armour stone, and Accropode II units with maritime plant and contractor overheads.
- **Reclamation Sand Fill Unit Rate:** `INR 1,488.38 per m³`  
  *Derivation:* Total Reclamation Capex (`INR 119,070,000,000`) divided by total reclamation sand volume (`80,000,000 m³`). Represents the composite EPC cost of TSHD offshore extraction at Daman, maritime transport, placement, and ground compaction.

### D. Maharashtra PWD State Schedule of Rates (SSR 2022–23) Reference Rates
- **Geotextile Polypropylene Woven Filter Fabric in Tidal Condition (Item 1678 / Coastal 49.01):** `INR 89.00 per m²` (Labour: INR 11.00).
- **Supplying & Laying Trap Stone in Tidal Range:**
  - Up to 20 kg (Core/Filter layer): `INR 894.00 per m³` (Item 1682 / Coastal 49.03).
  - 20 to 50 kg (Core/Sub-armour): `INR 907.00 per m³` (Item 1684 / Coastal 49.05).
  - 50 to 100 kg (Core/Sub-armour/Armour): `INR 974.00 per m³` (Item 1687 / Coastal 49.08).
  - 100 to 200 kg (Sub-armour): `INR 1,206.00 per m³` (Item 1690 / Coastal 49.11).
  - 300 to 500 kg (Armour stone): `INR 1,316.00 per m³` (Item 1694 / Coastal 49.15).
  - Above 1,000 kg (>1 MT Heavy Armour Rock): `INR 1,429.00 per m³` (Item 1698 / Coastal 49.19).
- **Precast Concrete Tetrapods M-30 (Item 1709 / Coastal 49.23):** `INR 9,387.00 per unit`.
- **In-Situ Marine Concrete in Tidal Conditions:**
  - M-20 Concrete with 15% plum (Item 1712 / Coastal 49.26): `INR 6,213.00 per m³`.
  - M-25 Concrete for jetty/retaining wall (Item 1713 / Coastal 49.27): `INR 6,377.00 per m³`.
- **Transport & Lead Charges (Statement C-1, Machine Loading):**
  - Bitumen Bulk Transport Rate: `INR 10.00 per MT per km` (General Note p11).
  - Excavated Rock / Soling Stone Haulage at 20 km lead: `INR 488.73 per m³`.
  - Sand / Crushed Stone Aggregate Haulage at 20 km lead: `INR 515.63 per m³`.
  - Murrum / Earth Haulage at 20 km lead: `INR 468.37 per m³`.

---

## 4. Environmental Evidence Found

### A. Documented Numerical Environmental Footprints & Budgets
1. **Forest Land Diversion Area:**
   - Gargaon Quarry Patch-1 (`VAD-Q01`): `17.08 hectares` of classified government forest land.
   - Khanivade Quarry Patch-5 (`VAD-Q03`): `15.39 hectares` of classified government forest land.
2. **Marine Benthic Disturbance Footprint:**
   - Daman Offshore Sand Borrow Concession (`VAD-M01`): `102.77 sq.km` (10,277.10 Ha) seabed area subject to TSHD extraction.
3. **Offshore Reclamation Marine Footprint:**
   - Land platform: `1,207.0 hectares` of subtidal/intertidal marine habitat transformed into port land.
4. **Beneficial Sediment Reuse:**
   - Channel dredging reuse: `7.0 million m³` of dredged silt/sand reused as reclamation fill.
5. **Committed Environmental Mitigation Budgets:**
   - Port Construction Phase EMP (EIA Table 161): `INR 302.00 Lakhs capital` (Rs. 3.02 Cr) + `INR 197.35 Lakhs/year O&M`.
   - Road Corridor Environmental Mitigation (Road DPR Table 1-7): `INR 20.00 Crores`.
   - Corporate Environmental Responsibility (CER) Budget (EIA Table 165): `INR 190.00 Crores` committed by JNPA.

### B. Qualitative Environmental Factors (No Fabricated Scores)
- **Quarry Blasting:** Ground vibration and air overpressure standards set to DGMS permissible peak particle velocity limits (NONEL detonators).
- **Quarry Fugitive Dust:** PM10/PM2.5 generation mitigated through wet drilling, dry fog dust suppression, and 7.5m peripheral greenbelts.
- **Offshore Turbidity Plumes:** Hopper overflow sediment plume modeled by CWPRS; tidal current dispersion limits sediment deposition on sensitive coastal ecology.
- **Transport Emissions:** High highway diesel emissions along rural corridors vs. ~75% lower carbon footprint via 103 TKM electrified rail link.

---

## 5. Resilience & Disruption Evidence Found

Nine real-world disruption scenarios were extracted from official feasibility and engineering studies:

1. **`VAD-RS01` — Southwest Monsoon Marine Shutdown:**
   - *Impact:* Complete shutdown of offshore sand dredging at Daman, marine barging, and breakwater rock dumping from June 1 to September 30 (4 months annual shutdown; 210-240 working days/year).
   - *Probability:* `NULL` | *Severity:* `NULL`.
2. **`VAD-RS02` — Forest Clearance Dependency for Captive Quarries:**
   - *Impact:* Gargaon (`VAD-Q01`) and Khanivade (`VAD-Q03`) require Stage-I and Stage-II clearances under the Forest Conservation Act 1980. Failure or delay blocks access to `30.97 million tonnes` of proved basalt rock.
   - *Probability:* `NULL` | *Severity:* `NULL`.
3. **`VAD-RS03` — SEIAA Maharashtra Environmental Clearance Constraints:**
   - *Impact:* Community objections raised during public hearings regarding groundwater, orchard dust, and blasting restrictions can lead to legal stays or reduced daily extraction limits.
   - *Probability:* `NULL` | *Severity:* `NULL`.
4. **`VAD-RS04` — Single Concession Dependency for Reclamation Sand:**
   - *Impact:* Total reclamation volume (`80 million m³`) is concentrated in a single 102.77 sq.km offshore borrow polygon in Daman. Dredger failure or interstate regulatory disputes halt reclamation with no onshore land substitute.
   - *Probability:* `NULL` | *Severity:* `NULL`.
5. **`VAD-RS05` — Rural Road Haulage Bottleneck Prior to Expressway Completion:**
   - *Impact:* Hauling 32.1 million tonnes of rock over narrow state highways (SH-40) and rural village roads prior to commissioning the 8-lane expressway causes traffic congestion, bridge damage, and public protests.
   - *Probability:* `NULL` | *Severity:* `NULL`.
6. **`VAD-RS06` — Arabian Sea Extreme Cyclone Event:**
   - *Impact:* Severe cyclonic storm generating 100-year return period waves ($H_s = 6.8$ to $7.2$ m, wave crests $>10$ m) causes damage to partially completed breakwater core and offshore plant.
   - *Probability:* `NULL` | *Severity:* `NULL`.
7. **`VAD-RS07` — Western DFC Rail Link Construction Lag:**
   - *Impact:* 36-month construction duration for 28 km rail link to New Palghar involving major bridges and RFO flyovers. Delays force inbound cement and steel onto congested highways.
   - *Probability:* `NULL` | *Severity:* `NULL`.
8. **`VAD-RS08` — Commercial Quarry Availability and Lease Life Expiry:**
   - *Impact:* Secondary commercial quarries (Borsheti, Kirat, Nagzari, Girnoli) have small surface leases (6.5 to 8 acres) and competing local demand, risking volume shortages.
   - *Probability:* `NULL` | *Severity:* `NULL`.
9. **`VAD-RS09` — Harbour Channel Siltation Surge Post-Monsoon:**
   - *Impact:* CWPRS modeling predicts 0.5 m siltation (`3.1 million m³` in non-monsoon alone), reducing navigation channel depth before maintenance dredging mobilization.
   - *Probability:* `NULL` | *Severity:* `NULL`.

---

## 6. Missing Numerical Values & Impact on Current Agent 3 Logic

The following critical numerical inputs are **NOT provided in official project reports** and are documented as `NULL`:

1. **Gate Purchase Price for Commodity Steel (TMT Fe500D):** `NULL`  
   *DPR reports that steel is available at Mumbai wholesale markets (~100 km) and embeds steel costs inside general civil EPC contracts. It does not publish a vendor purchase invoice price per tonne.*
2. **Gate Purchase Price for Bulk Cement (OPC / PPC):** `NULL`  
   *DPR notes cement is available locally in Vadhavan, but does not state a factory supply invoice rate.*
3. **Commercial Rock Purchase Price at Merchant Quarries (Borsheti/Kirat):** `NULL`  
   *Quarry owners sell at negotiated commercial rates not published in the government DPR.*
4. **Marine Sand Statutory Extraction Royalty:** `NULL`  
   *The Ministry of Mines Gazette reserves the 102.77 sq.km area for JNPA, but royalty per cubic metre payable to the DNH & DD administration is unstated.*
5. **Numerical Environmental Scores (0.0 to 1.0):** `NULL`  
   *The EIA provides detailed baseline concentrations ($\mu g/m^3$, $dB(A)$) and qualitative mitigation matrices, but never assigns an arbitrary scalar score.*
6. **Numerical Disruption Probabilities & Severity Factors:** `NULL`  
   *Official engineering and risk reports state operational risks qualitatively. Converting "monsoon restricts operations" into an arbitrary probability like `0.9` or `0.6` is mathematically unfounded.*

### Formulas in Current Agent 3 That Cannot Yet Be Computed from Verified Data Alone

In the existing `agents/cost_environment_resilience.py`:
1. **Material Cost Formula:** $\text{Cost} = \text{Quantity} \times \text{unit\_cost}$  
   *Cannot be computed for Steel, Cement, or Merchant Stone without assuming a market price or using derived EPC block costs.*
2. **Environmental Score Formula:** Weighted sum of scalar factor scores:
   $$\text{Score} = \sum w_i \times \text{factor}_i$$
   *Cannot be evaluated because genuine environmental impact reports provide physical quantities (hectares of forest, decibels, PM concentrations) rather than scalar 0–1 weights.*
3. **Resilience Score Formula:** Linear risk exposure calculation:
   $$\text{Risk} = \text{Probability} \times \text{Severity}$$
   *Cannot be evaluated because probability and severity are unquantified in official engineering reports.*

> [!IMPORTANT]
> The absence of a numerical value in official engineering documents does **NOT** justify creating an assumed number. The real dataset preserves factual qualitative evidence and explicit `NULL`s. In a future task, Agent 3 should be updated to support qualitative risk evaluation and multi-level cost aggregation.

---

## 7. Data Classification Taxonomy

All records across the verified datasets strictly adhere to this four-tier classification:

1. **`verified_document`:** Directly copied from an official government gazette, tender specification, detailed project report, or statutory executive summary. Every entry includes document name, section, and page number.
2. **`calculated`:** Derived through direct mathematical operations exclusively on documented parameters (e.g., dividing total breakwater capital budget by total required stone tonnage).
3. **`requires_current_verification`:** Documented commercial or prospective assets whose current operational status, lease validity, or market quote cannot be verified from historical DPR text alone (e.g., private quarries at Borsheti, Kirat).
4. **`regulatory_dependency`:** Documented project components whose operational validity is legally conditioned upon pending statutory clearances (e.g., Stage-I Forest Clearance for Gargaon Patch-1 and Khanivade Patch-5).

---

## 8. Applicability Limitations of Maharashtra PWD SSR (2022–23)

1. **Schedule of Rates vs. Commercial Bid:** The Maharashtra PWD SSR is an administrative benchmark published for government engineering departments to prepare administrative approvals and Detailed Tender Proofs (DTP). It is **not** a firm contractor bid, commercial supplier quotation, or legally binding market price.
2. **Local Market Fluctuations:** General Note 1 (p7) explicitly stipulates that if local market rates for sand, metal, murrum, or bricks deviate from SSR base rates, the Superintending Engineer must prepare a separate local rate analysis.
3. **Tidal Surcharges & Coastal Circle Conditions:** Coastal items (Chapter 49) are subject to specific additions:
   - For work carried out in tidal conditions, an additional `10%` surcharge applies to the completed item rate (SSR p17).
   - Foul condition excavation adds `25%` over normal scheduled rates (SSR p9).
4. **Applicability to Large Marine EPC Contracts:** Vadhavan Port breakwater and reclamation are mega-contracts ($>\text{Rs. } 5,000 \text{ Cr}$) executed by international EPC consortiums using specialized heavy marine equipment (e.g., 20,000 m³ TSHDs, split-hopper barges, 100-tonne marine cranes). PWD SSR rates are derived for typical state public works and tend to underestimate large-scale specialized marine mobilisation costs while overestimating basic manual quarrying unit costs.

---

## 9. Document Conflicts & Overlaps Noted

1. **Quarry Lead Distances:**
   - *DPR Table 2-2 & Road DPR Table 1-6:* Gargaon lead distance reported as **17.0 km** via Shigaon road.
   - *Gargaon Quarry EIA Executive Summary (2026):* Distance reported as **17.2 km** north-west of lease centroid.  
   *(Variance of 0.2 km is within normal survey tolerance).*
2. **Nagzari Lead Distance:**
   - *DPR Table 2-3 & Road DPR Table 7-3:* Distance from port to Nagzari Village recorded as **26 km**.
   - *Techno-Economic Feasibility Report (TEFR, Section 7.3.4.1, p68):* States existing quarry sites at Nagzari are **~35 km** away.  
   *(Both citations are catalogued in the provenance log).*
3. **Reclamation Dredging Volumes:**
   - *DPR Section 2.3.2:* Estimated capital dredging yield for Phase 1 fill at **6.9 million m³**.
   - *Package 2B EPC Tender (p4):* References approximately **7.0 million m³** of suitable sand/silt for reclamation bund formation.

---

## 10. Conclusion

The real Agent 3 dataset establishes an authentic, transparent engineering baseline for Vadhavan Port. By rigorously preserving documented values, recording verifiable derivations, and acknowledging missing figures as explicit `NULL`s, InfraMiner AI maintains total scientific and audit integrity.

