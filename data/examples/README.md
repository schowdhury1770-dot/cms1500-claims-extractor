# Example Datasets

This directory contains example CMS-1500 claim data for testing and demonstration purposes.

## Files

### JSON Examples
- **sample_cms1500_claim_1.json** - Patient: John Michael Thompson (Diabetes & Hypertension)
  - Represents a typical office visit with lab work
  - Contains complete patient, provider, and billing information
  - Includes multiple diagnosis and procedure codes

- **sample_cms1500_claim_2.json** - Patient: Maria Rosa Garcia (Back Pain)
  - Represents physical medicine services
  - Includes imaging and therapy procedures
  - Shows multi-line claim structure

### Expected Output
- **expected_output.json** - Standardized output format after extraction and SFT processing
  - Shows the structure produced by the Qwen 3B model with SFT
  - Contains key-value pair standardization
  - Includes quality metrics and confidence scores

## TIFF Image Files

### Note on TIFF Files
The TIFF image files contain scanned CMS-1500 forms. These are placeholder references and actual TIFF files would need to be:

1. **Obtained from** healthcare providers or claim systems
2. **De-identified** to remove all PHI (Protected Health Information)
3. **Compressed** using lossless TIFF compression for storage efficiency

### Expected TIFF Structure
```
sample_cms1500_form_1.tiff - Scanned front page of CMS-1500 form
sample_cms1500_form_2.tiff - Scanned front page of CMS-1500 form
```

## Data Schema

### Patient Information
- `name`: Full name of patient
- `date_of_birth`: DOB in YYYY-MM-DD format
- `gender`: M/F designation
- `patient_account_number`: Internal account number
- `group_number`: Insurance group number

### Provider Information
- `provider_name`: Full name with credentials
- `provider_id`: NPI (National Provider Identifier)
- `provider_address`: Complete address
- `provider_phone`: Contact number

### Diagnosis Codes
- `code`: ICD-10-CM diagnosis code
- `description`: Full description of diagnosis
- `primary`: Boolean indicating if primary diagnosis
- `position`: Position in diagnosis list

### Procedure Codes
- `code`: CPT/HCPCS procedure code
- `description`: Procedure description
- `units`: Number of units billed
- `charge`: Amount charged
- `modifier`: Any applicable modifiers

## Standardized Output Format

The SFT-processed output uses consistent key-value pairs:

```json
{
  "PATIENT_ID": "unique_identifier",
  "PATIENT_NAME": "standardized_name",
  "PROVIDER_ID": "npi_number",
  "PRIMARY_DIAGNOSIS_CODE": "icd10_code",
  "TOTAL_CHARGE_AMOUNT": 0.00,
  "CLAIM_STATUS": "status_value"
}
```

## Data Privacy

⚠️ **IMPORTANT**: These are synthetic examples created for demonstration purposes. 

When working with real CMS-1500 claims:
- Ensure HIPAA compliance
- De-identify all PHI before processing
- Use secure, encrypted storage
- Follow your organization's data governance policies

## Usage

Use these files to:
1. Test the Qwen 3B extraction model
2. Validate SFT standardization output
3. Benchmark extraction accuracy
4. Train and fine-tune models

## Adding New Examples

To add new example claims:

1. Create a new JSON file following the schema in `sample_cms1500_claim_1.json`
2. Ensure all PHI is properly anonymized/synthetic
3. Add corresponding expected output to `expected_output.json`
4. Document any special cases in this README
