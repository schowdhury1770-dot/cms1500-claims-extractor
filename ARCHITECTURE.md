```
╔════════════════════════════════════════════════════════════════════════════════╗
║          CMS-1500 CLAIMS DATA EXTRACTION ARCHITECTURE & DATA FLOW              ║
╚════════════════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────────────┐
│ LAYER 1: INPUT SOURCES                                                       │
└──────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
    │  TIFF IMAGE     │         │  JSON FILE      │         │  DIRECT API     │
    │  (Scanned Form) │         │  (Structured)   │         │  (Database)     │
    │                 │         │                 │         │                 │
    │ • sample_1.tif  │         │ • sample_1.json │         │ • Healthcare    │
    │ • sample_2.tif  │         │ • sample_2.json │         │   System API    │
    └────────┬────────┘         └────────┬────────┘         └────────┬────────┘
             │                           │                           │
             └───────────────┬───────────┴───────────────┬───────────┘
                             │                           │
                    ┌────────▼───────────┐      ┌────────▼──────────┐
                    │   FILE VALIDATION  │      │  API VALIDATION   │
                    │   • File size      │      │  • Auth tokens    │
                    │   • Format check   │      │  • Rate limits    │
                    └────────┬───────────┘      └────────┬──────────┘
                             │                          │
                             └───────────────┬──────────┘
                                             │

┌──────────────────────────────────────────────────────────────────────────────┐
│ LAYER 2: DATA PREPROCESSING                                                  │
└──────────────────────────────────────────────────────────────────────────────┘

    ┌────────────────────��────────────────────────────────────────────────────┐
    │                    PREPROCESSING PIPELINE                               │
    │                                                                          │
    │  ┌──────────────────┐         ┌──────────────────┐                     │
    │  │  IMAGE PROCESS   │         │  JSON PARSE      │                     │
    │  │                  │         │                  │                     │
    │  │ 1. Load TIFF     │         │ 1. Load & Parse  │                     │
    │  │ 2. Convert Gray  │         │ 2. Validate      │                     │
    │  │ 3. Denoise       │    │    │ 3. Extract keys  │                     │
    │  │ 4. Enhance       │    │    │ 4. Type check    │                     │
    │  │ 5. Binarize      │    │    │ 5. Normalize     │                     │
    │  └────────┬─────────┘    │    └────────┬─────────┘                     │
    │           │              │             │                               │
    │           └──────────────┼─────────────┘                               │
    │                          │                                              │
    │                   ┌──────▼──────────┐                                   │
    │                   │  OCR EXTRACTION │                                   │
    │                   │  (Tesseract)    │                                   │
    │                   │                 │                                   │
    │                   │ • Extract text  │                                   │
    │                   │ • Structure     │                                   │
    │                   │ • Confidence    │                                   │
    │                   └────────┬────────┘                                   │
    │                            │                                            │
    │                   ┌────────▼──────────────┐                             │
    │                   │  STANDARDIZED TEXT    │                             │
    │                   │  REPRESENTATION       │                             │
    │                   └────────┬───────────────┘                            │
    │                            │                                            │
    └────────────────────────────┼────────────────────────────────────────────┘
                                 │

┌──────────────────────────────────────────────────────────────────────────────┐
│ LAYER 3: MODEL INFERENCE (QWEN 3B)                                          │
└──────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────────────┐
    │                        QWEN 3B MODEL                                     │
    │                                                                          │
    │  Input: Preprocessed Text + Prompt Engineering                          │
    │  ┌────────────────────────────────────────────────────────────────────┐ │
    │  │ PROMPT TEMPLATE:                                                   │ │
    │  │                                                                    │ │
    │  │ "Extract structured information from CMS-1500 claim:               │ │
    │  │  [TEXT_CONTENT]                                                   │ │
    │  │                                                                    │ │
    │  │  Return as Key-Value pairs:                                       │ │
    │  │  PATIENT_NAME, PATIENT_DOB, PROVIDER_NAME, PROVIDER_ID,           │ │
    │  │  PRIMARY_DIAGNOSIS, SERVICE_DATE, TOTAL_CHARGE, ..."              │ │
    │  └────────────────────────────────────────────────────────────────────┘ │
    │                            │                                             │
    │                   ┌────────▼──────────┐                                  │
    │                   │  TOKENIZATION     │                                  │
    │                   │  max_length: 512  │                                  │
    │                   └────────┬──────────┘                                  │
    │                            │                                             │
    │                   ┌────────▼──────────┐                                  │
    │                   │  MODEL INFERENCE  │                                  │
    │                   │ (Forward Pass)    │                                  │
    │                   │ Device: GPU/CPU   │                                  │
    │                   │ dtype: float16    │                                  │
    │                   └────────┬──────────┘                                  │
    │                            │                                             │
    │                   ┌────────▼──────────┐                                  │
    │                   │ DECODING OUTPUT   │                                  │
    │                   │ • Temperature: 0.7│                                  │
    │                   │ • top_p: 0.9      │                                  │
    │                   │ • max_tokens: 256 │                                  │
    │                   └────────┬──────────┘                                  │
    │                            │                                             │
    │            Output: Structured Key-Value Pairs                            │
    │                            │                                             │
    └────────────────────────────┼──────────────────────────────────────────────┘
                                 │

┌──────────────────────────────────────────────────────────────────────────────┐
│ LAYER 4: POST-PROCESSING & STANDARDIZATION (SFT)                            │
└──────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────────┐
    │              EXTRACTION FIELD STRUCTURING                               │
    │                                                                          │
    │  Model Output                                                            │
    │        │                                                                 │
    │        ▼                                                                 │
    │  ┌──────────────────────────────────────────┐                           │
    │  │  Parse Response into Pydantic Models     │                           │
    │  │                                          │                           │
    │  │  ExtractionField:                        │                           │
    │  │  ├─ field_name (str)                     │                           │
    │  │  ├─ field_value (Any)                    │                           │
    │  │  ├─ confidence (float: 0-1)              │                           │
    │  │  └─ source (str: json/model/api)         │                           │
    │  └──────────────────────────────────────────┘                           │
    │        │                                                                 │
    │        ▼                                                                 │
    │  ┌──────────────────────────────────────────┐                           │
    │  │  FIELD VALIDATION & CLEANING             │                           │
    │  │                                          │                           │
    │  │  • Remove null/empty values              │                           │
    │  │  • Validate data types                   │                           │
    │  │  • Date format normalization             │                           │
    │  │  • Standardize phone numbers             │                           │
    │  │  • Normalize diagnosis codes (ICD-10)    │                           │
    │  │  • Validate CPT procedure codes          │                           │
    │  └──────────────────────────────────────────┘                           │
    │        │                                                                 │
    │        ▼                                                                 │
    │  ┌──────────────────────────────────────────┐                           │
    │  │  FIELD MAPPING TO STANDARD SCHEMA        │                           │
    │  │                                          │                           │
    │  │  Custom Fields  →  Standard CMS-1500     │                           │
    │  │  ─────────────────────────────────────   │                           │
    │  │  MODEL_OUTPUT → STANDARDIZED_KEY         │                           │
    │  │                                          │                           │
    │  │  PATIENT_NAME → PATIENT_NAME             │                           │
    │  │  PT_DOB → PATIENT_DATE_OF_BIRTH          │                           │
    │  │  PROV_ID → PROVIDER_NPI                  │                           │
    │  │  DIAG_PRIMARY → PRIMARY_DIAGNOSIS_CODE   │                           │
    │  │  SERVICE_DATE_START → SERVICE_DATE_FROM  │                           │
    │  │  CHARGE_TOTAL → TOTAL_CHARGE_AMOUNT      │                           │
    │  │  PAID → TOTAL_PAID_AMOUNT                │                           │
    │  │  INSURANCE → PRIMARY_INSURANCE_CARRIER   │                           │
    │  └──────────────────────────────────────────┘                           │
    │        │                                                                 │
    │        ▼                                                                 │
    │  ┌──────────────────────────────────────────┐                           │
    │  │  CONFIDENCE AGGREGATION                  │                           │
    │  │                                          │                           │
    │  │  For each field:                         │                           │
    │  │  ├─ Individual confidence score          │                           │
    │  │  ├─ Cross-field validation               │                           │
    │  │  └─ Anomaly detection                    │                           │
    │  │                                          │                           │
    │  │  Overall metrics:                        │                           │
    │  │  ├─ Field completeness                   │                           │
    │  │  ├─ Data consistency                     │                           │
    │  │  └─ Average confidence                   │                           │
    │  └──────────────────────────────────────────┘                           │
    │        │                                                                 │
    │        ▼                                                                 │
    └─────────────────────────────────────────────────────────────────────────┘
                                 │

┌──────────────────────────────────────────────────────────────────────────────┐
│ LAYER 5: OUTPUT & STANDARDIZATION                                            │
└──────────────────────────────────────────────────────────────────────────────┘

    Standardized Key-Value Pairs Output:
    
    ┌─────────────────────────────────────────────────────────────────────────┐
    │ STANDARDIZED_OUTPUT {                                                   │
    │   "CLAIM_ID": "CMS-2024-001",                                           │
    │   "EXTRACTION_TIMESTAMP": "2026-09-04T18:06:00",                        │
    │                                                                          │
    │   "PATIENT_INFORMATION": {                                              │
    │     "PATIENT_NAME": {                                                   │
    │       "value": "John Michael Thompson",                                 │
    │       "confidence": 0.98,                                               │
    │       "source": "json"                                                  │
    │     },                                                                  │
    │     "PATIENT_DATE_OF_BIRTH": {                                          │
    │       "value": "1965-03-15",                                            │
    │       "confidence": 0.99,                                               │
    │       "source": "json"                                                  │
    │     },                                                                  │
    │     "PATIENT_GENDER": {                                                 │
    │       "value": "M",                                                     │
    │       "confidence": 1.0,                                                │
    │       "source": "json"                                                  │
    │     },                                                                  │
    │     ...                                                                 │
    │   },                                                                    │
    │                                                                          │
    │   "PROVIDER_INFORMATION": {                                             │
    │     "PROVIDER_NAME": { ... },                                           │
    │     "PROVIDER_NPI": { ... },                                            │
    │     "PROVIDER_ADDRESS": { ... },                                        │
    │     ...                                                                 │
    │   },                                                                    │
    │                                                                          │
    │   "CLINICAL_INFORMATION": {                                             │
    │     "PRIMARY_DIAGNOSIS_CODE": { ... },                                  │
    │     "PRIMARY_DIAGNOSIS_DESCRIPTION": { ... },                           │
    │     "SECONDARY_DIAGNOSES": { ... },                                     │
    │     ...                                                                 │
    │   },                                                                    │
    │                                                                          │
    │   "FINANCIAL_INFORMATION": {                                            │
    │     "TOTAL_CHARGE_AMOUNT": { ... },                                     │
    │     "TOTAL_PAID_AMOUNT": { ... },                                       │
    │     "PATIENT_RESPONSIBILITY": { ... },                                  │
    │     ...                                                                 │
    │   },                                                                    │
    │                                                                          │
    │   "QUALITY_METRICS": {                                                  │
    │     "FIELD_COMPLETENESS": 0.96,                                         │
    │     "DATA_CONSISTENCY": 0.99,                                           │
    │     "EXTRACTION_STATUS": "SUCCESS",                                     │
    │     "AVERAGE_CONFIDENCE": 0.975                                         │
    │   }                                                                     │
    │ }                                                                       │
    └─────────────────────────────────────────────────────────────────────────┘
                                 │

┌──────────────────────────────────────────────────────────────────────────────┐
│ LAYER 6: STORAGE & OUTPUT                                                    │
└──────────────────────────────────────────────────────────────────────────────┘

    ┌────────────────────┐   ┌────────────────────┐   ┌────────────────────┐
    │  JSON OUTPUT FILE  │   │  RESULTS DATABASE  │   │  API RESPONSE      │
    │                    │   │                    │   │                    │
    │ extraction_        │   │ • PostgreSQL       │   │ • REST API         │
    │ results.json       │   │ • MongoDB          │   │ • GraphQL API      │
    │                    │   │ • DynamoDB         │   │ • Kafka Topic      │
    │ Structure:         │   │ • Elasticsearch    │   │                    │
    │ {                  │   │                    │   │ Real-time stream   │
    │   "claims": [...], │   │ Indexing:          │   │ processing         │
    │   "summary": {...},│   │ • Full-text search │   │                    │
    │   "metrics": {...} │   │ • Faceted search   │   │ Integration with   │
    │ }                  │   │                    │   │ Healthcare systems │
    └────────────────────┘   └────────────────────┘   └────────────────────┘
             │                        │                        │
             └────────────────────────┼────────────────────────┘
                                      │

┌──────────────────────────────────────────────────────────────────────────────┐
│ LAYER 7: QUALITY ASSURANCE & MONITORING                                      │
└──────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────────┐
    │  VALIDATION PIPELINE                                                    │
    │                                                                          │
    │  ├─ Schema Validation (Pydantic)                                        │
    │  │  ├─ Field types validation                                           │
    │  │  ├─ Required fields check                                            │
    │  │  └─ Value range validation                                           │
    │  │                                                                      │
    │  ├─ Business Logic Validation                                           │
    │  │  ├─ Diagnosis code format (ICD-10)                                   │
    │  │  ├─ Procedure code format (CPT)                                      │
    │  │  ├─ Date consistency                                                 │
    │  │  └─ Financial amount validation                                      │
    │  │                                                                      │
    │  ├─ Confidence Thresholds                                               │
    │  │  ├─ Critical fields: > 0.95 confidence                               │
    │  │  ├─ Important fields: > 0.85 confidence                              │
    │  │  └─ Optional fields: > 0.70 confidence                               │
    │  │                                                                      │
    │  └─ Error Reporting                                                     │
    │     ├─ Failed validations log                                           │
    │     ├─ Low confidence alerts                                            │
    │     └─ Processing errors tracking                                       │
    │                                                                          │
    └─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ LAYER 8: FEEDBACK LOOP & CONTINUOUS IMPROVEMENT                             │
└──────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────���───────────────────────────────────────────────────────────┐
    │  SFT (Supervised Fine-Tuning) Training Data Collection                  │
    │                                                                          │
    │  1. Collect extraction results with user feedback                       │
    │  2. Identify misclassifications & low confidence extractions            │
    │  3. Prepare training dataset:                                           │
    │     {                                                                   │
    │       "input": "[OCR_TEXT or JSON_CONTENT]",                            │
    │       "output": "[CORRECT_STANDARDIZED_KV_PAIRS]",                      │
    │       "confidence_feedback": "HIGH/MEDIUM/LOW"                          │
    │     }                                                                   │
    │  4. Fine-tune Qwen model on CMS-1500 specific data                      │
    │  5. Evaluate on test set                                                │
    │  6. Deploy improved model version                                       │
    │                                                                          │
    │  Metrics to track:                                                      │
    │  • F1-score for field extraction                                        │
    │  • Extraction accuracy improvement                                      │
    │  • Confidence score calibration                                         │
    │  • Error reduction rate                                                 │
    └─────────────────────────────────────────────────────────────────────────┘

╔════════════════════════════════════════════════════════════════════════════════╗
║                           END-TO-END FLOW SUMMARY                              ║
╚════════════════════════════════════════════════════════════════════════════════╝

TIFF/JSON Input
       │
       ▼
   Validation
       │
       ▼
Preprocessing (OCR for TIFF, Parse for JSON)
       │
       ▼
Standardized Text Input
       │
       ▼
Qwen 3B Model Inference with Prompt Engineering
       │
       ▼
Raw Key-Value Pairs Output
       │
       ▼
Field Parsing & Validation (Pydantic)
       │
       ▼
Data Normalization & Standardization
       │
       ▼
Confidence Scoring & Aggregation
       │
       ▼
Final Standardized Output (Key-Value Pairs)
       │
       ├──► JSON File (extraction_results.json)
       ├──► Database Storage (PostgreSQL/MongoDB)
       ├──► API Response (REST/GraphQL)
       └──► Monitoring & QA Pipeline

═══════════════════════════════════════════════════════════════════════════════

TECHNOLOGIES USED:

┌─────────────────────────────────────────────────────────────────────────────┐
│ Component              │ Technology            │ Version                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ Language               │ Python                │ 3.8+                        │
│ Deep Learning          │ PyTorch               │ 2.0.1                       │
│ Model Library          │ Transformers (HF)     │ 4.35.2                      │
│ LLM Model              │ Qwen 1.8B-Chat        │ Latest                      │
│ Image Processing       │ OpenCV                │ 4.8.1.78                    │
│ OCR Engine             │ Tesseract             │ 3.10+                       │
│ Data Validation        │ Pydantic              │ 2.4.2                       │
│ Data Handling          │ NumPy                 │ 1.24.3                      │
│ Image Library          │ Pillow                │ 10.1.0                      │
│ HTTP Client            │ Requests              │ 2.31.0                      │
│ Progress Tracking      │ tqdm                  │ 4.66.1                      │
│ Env Management         │ python-dotenv         │ 1.0.0                       │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════

DEVICE CONFIGURATION:

┌─────────────────────────────────────────────────────────────────────────────┐
│ Device Support:                                                             │
│ • GPU (CUDA 11.8+): FP16 inference for faster processing                   │
│ • CPU Fallback: FP32 inference for compatibility                           │
│                                                                             │
│ Memory Requirements:                                                        │
│ • GPU: 6-8 GB VRAM (optimized with FP16)                                   │
│ • CPU: 8-12 GB RAM                                                         │
│                                                                             │
│ Processing Time:                                                           │
│ • Per claim (JSON): ~0.5-1.0 seconds                                       │
│ • Per claim (TIFF): ~2-5 seconds (including OCR)                           │
│ • Batch (100 claims): ~2-5 minutes                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```
