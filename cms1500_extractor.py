"""
CMS-1500 Claims Data Extractor using Qwen 3B Model

This module extracts structured data from CMS-1500 claims in JSON and TIFF formats
using the Qwen 3B Instruct model and returns standardized key-value pairs.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from PIL import Image
import cv2
import numpy as np
from pydantic import BaseModel, Field
from tqdm import tqdm
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExtractionField(BaseModel):
    """Pydantic model for extracted fields"""
    field_name: str = Field(..., description="Name of the extracted field")
    field_value: Any = Field(..., description="Value of the extracted field")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    source: str = Field(default="model", description="Source of extraction")


class ClaimExtraction(BaseModel):
    """Pydantic model for complete claim extraction"""
    claim_id: str
    extracted_fields: List[ExtractionField]
    standardized_output: Dict[str, Any]
    extraction_confidence: float
    processing_status: str


class Qwen3BExtractor:
    """
    CMS-1500 Claims Extractor using Qwen 3B Instruct Model
    """

    def __init__(self, model_name: str = "Qwen/Qwen-1.8B-Chat"):
        """
        Initialize the Qwen 3B extractor model
        
        Args:
            model_name: HuggingFace model identifier
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")
        
        try:
            logger.info(f"Loading model: {model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                trust_remote_code=True
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto",
                trust_remote_code=True
            )
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise

    def extract_from_json(self, json_path: str) -> Dict[str, Any]:
        """
        Extract data from JSON formatted CMS-1500 claims
        
        Args:
            json_path: Path to JSON file
            
        Returns:
            Dictionary containing extracted claim data
        """
        try:
            with open(json_path, 'r') as f:
                claim_data = json.load(f)
            
            logger.info(f"Processing JSON file: {json_path}")
            
            # Direct extraction from JSON structure
            extracted_fields = self._parse_json_structure(claim_data)
            
            return {
                "source": "json",
                "file_path": json_path,
                "extracted_fields": extracted_fields,
                "claim_id": claim_data.get("claim_id", "UNKNOWN")
            }
        except Exception as e:
            logger.error(f"Error extracting from JSON {json_path}: {str(e)}")
            raise

    def _parse_json_structure(self, data: Dict) -> List[ExtractionField]:
        """
        Parse JSON structure and extract key fields
        
        Args:
            data: JSON data dictionary
            
        Returns:
            List of extracted fields
        """
        extracted_fields = []
        
        # Patient Information
        if "patient_info" in data:
            patient = data["patient_info"]
            extracted_fields.extend([
                ExtractionField(
                    field_name="PATIENT_NAME",
                    field_value=patient.get("name", ""),
                    confidence=1.0,
                    source="json"
                ),
                ExtractionField(
                    field_name="PATIENT_DOB",
                    field_value=patient.get("date_of_birth", ""),
                    confidence=1.0,
                    source="json"
                ),
                ExtractionField(
                    field_name="PATIENT_GENDER",
                    field_value=patient.get("gender", ""),
                    confidence=1.0,
                    source="json"
                ),
                ExtractionField(
                    field_name="PATIENT_ID",
                    field_value=patient.get("patient_account_number", ""),
                    confidence=1.0,
                    source="json"
                ),
            ])
        
        # Provider Information
        if "provider_info" in data:
            provider = data["provider_info"]
            extracted_fields.extend([
                ExtractionField(
                    field_name="PROVIDER_NAME",
                    field_value=provider.get("provider_name", ""),
                    confidence=1.0,
                    source="json"
                ),
                ExtractionField(
                    field_name="PROVIDER_ID",
                    field_value=provider.get("provider_id", ""),
                    confidence=1.0,
                    source="json"
                ),
                ExtractionField(
                    field_name="PROVIDER_ADDRESS",
                    field_value=provider.get("provider_address", ""),
                    confidence=1.0,
                    source="json"
                ),
            ])
        
        # Claim Information
        if "claim_info" in data:
            claim = data["claim_info"]
            extracted_fields.extend([
                ExtractionField(
                    field_name="SERVICE_DATE_FROM",
                    field_value=claim.get("service_date_from", ""),
                    confidence=1.0,
                    source="json"
                ),
                ExtractionField(
                    field_name="SERVICE_DATE_TO",
                    field_value=claim.get("service_date_to", ""),
                    confidence=1.0,
                    source="json"
                ),
                ExtractionField(
                    field_name="CLAIM_SUBMISSION_DATE",
                    field_value=claim.get("claim_submission_date", ""),
                    confidence=1.0,
                    source="json"
                ),
            ])
        
        # Diagnosis Codes
        if "diagnosis_codes" in data:
            diagnoses = data["diagnosis_codes"]
            if diagnoses:
                primary_diag = next(
                    (d for d in diagnoses if d.get("primary")), 
                    diagnoses[0]
                )
                extracted_fields.append(
                    ExtractionField(
                        field_name="PRIMARY_DIAGNOSIS_CODE",
                        field_value=primary_diag.get("code", ""),
                        confidence=1.0,
                        source="json"
                    )
                )
                extracted_fields.append(
                    ExtractionField(
                        field_name="PRIMARY_DIAGNOSIS_DESC",
                        field_value=primary_diag.get("description", ""),
                        confidence=1.0,
                        source="json"
                    )
                )
        
        # Charges and Payments
        if "charges_and_payments" in data:
            charges = data["charges_and_payments"]
            extracted_fields.extend([
                ExtractionField(
                    field_name="TOTAL_CHARGE_AMOUNT",
                    field_value=charges.get("total_charge", 0.0),
                    confidence=1.0,
                    source="json"
                ),
                ExtractionField(
                    field_name="TOTAL_PAID_AMOUNT",
                    field_value=charges.get("total_paid", 0.0),
                    confidence=1.0,
                    source="json"
                ),
                ExtractionField(
                    field_name="PATIENT_RESPONSIBILITY",
                    field_value=charges.get("patient_responsibility", 0.0),
                    confidence=1.0,
                    source="json"
                ),
            ])
        
        # Insurance Information
        if "insurance_info" in data:
            insurance = data["insurance_info"]
            extracted_fields.append(
                ExtractionField(
                    field_name="INSURANCE_CARRIER",
                    field_value=insurance.get("primary_insurance", ""),
                    confidence=1.0,
                    source="json"
                )
            )
        
        return extracted_fields

    def extract_from_tiff(self, tiff_path: str) -> Dict[str, Any]:
        """
        Extract data from TIFF formatted CMS-1500 claims using OCR and model inference
        
        Args:
            tiff_path: Path to TIFF file
            
        Returns:
            Dictionary containing extracted claim data
        """
        try:
            logger.info(f"Processing TIFF file: {tiff_path}")
            
            # Load and preprocess TIFF image
            image = Image.open(tiff_path)
            image_array = np.array(image)
            
            # Preprocess image for better OCR
            processed_image = self._preprocess_image(image_array)
            
            # Extract text using OCR-like approach
            text_content = self._extract_text_from_image(processed_image)
            
            # Use Qwen model to structure extracted text
            extracted_fields = self._structure_text_with_qwen(text_content)
            
            return {
                "source": "tiff",
                "file_path": tiff_path,
                "extracted_fields": extracted_fields,
                "raw_text": text_content
            }
        except Exception as e:
            logger.error(f"Error extracting from TIFF {tiff_path}: {str(e)}")
            raise

    def _preprocess_image(self, image_array: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better text extraction
        
        Args:
            image_array: Input image as numpy array
            
        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        if len(image_array.shape) == 3:
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = image_array
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(enhanced, h=10)
        
        return denoised

    def _extract_text_from_image(self, image: np.ndarray) -> str:
        """
        Extract text from preprocessed image
        
        Args:
            image: Preprocessed image
            
        Returns:
            Extracted text
        """
        try:
            import pytesseract
            text = pytesseract.image_to_string(image)
            return text
        except ImportError:
            logger.warning("pytesseract not available, using placeholder extraction")
            return "Image content placeholder - pytesseract not installed"

    def _structure_text_with_qwen(self, text_content: str) -> List[ExtractionField]:
        """
        Use Qwen model to structure extracted text into key-value pairs
        
        Args:
            text_content: Raw extracted text
            
        Returns:
            List of structured extraction fields
        """
        prompt = f"""Extract structured information from the following CMS-1500 claim text and return as key-value pairs.
Focus on: Patient Name, Patient DOB, Provider Name, Provider ID, Diagnosis Code, Service Date, Total Charge, Insurance Carrier.

Text:
{text_content}

Return the extracted information as structured data:"""

        try:
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=512
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=256,
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True
                )
            
            response = self.tokenizer.decode(
                outputs[0],
                skip_special_tokens=True
            )
            
            # Parse response into structured fields
            extracted_fields = self._parse_model_response(response)
            return extracted_fields
        except Exception as e:
            logger.error(f"Error in model inference: {str(e)}")
            return []

    def _parse_model_response(self, response: str) -> List[ExtractionField]:
        """
        Parse model response into structured fields
        
        Args:
            response: Model generated response
            
        Returns:
            List of extraction fields
        """
        extracted_fields = []
        lines = response.split('\n')
        
        for line in lines:
            if ':' in line:
                try:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Skip empty values
                    if key and value:
                        extracted_fields.append(
                            ExtractionField(
                                field_name=key.upper().replace(' ', '_'),
                                field_value=value,
                                confidence=0.85,  # Model-based confidence
                                source="model"
                            )
                        )
                except ValueError:
                    continue
        
        return extracted_fields

    def standardize_output(
        self,
        extracted_fields: List[ExtractionField],
        claim_id: str = "UNKNOWN"
    ) -> Dict[str, Any]:
        """
        Standardize extracted fields to CMS-1500 standard key-value pairs
        
        Args:
            extracted_fields: List of extracted fields
            claim_id: Claim identifier
            
        Returns:
            Standardized output dictionary
        """
        standardized = {
            "CLAIM_ID": claim_id,
            "EXTRACTION_TIMESTAMP": str(np.datetime64('today')),
        }
        
        # Map extracted fields to standard format
        field_mapping = {
            "PATIENT_NAME": "PATIENT_NAME",
            "PATIENT_DOB": "PATIENT_DATE_OF_BIRTH",
            "PATIENT_GENDER": "PATIENT_GENDER",
            "PATIENT_ID": "PATIENT_ACCOUNT_NUMBER",
            "PROVIDER_NAME": "PROVIDER_NAME",
            "PROVIDER_ID": "PROVIDER_NPI",
            "PROVIDER_ADDRESS": "PROVIDER_ADDRESS",
            "PRIMARY_DIAGNOSIS_CODE": "PRIMARY_DIAGNOSIS_CODE",
            "PRIMARY_DIAGNOSIS_DESC": "PRIMARY_DIAGNOSIS_DESCRIPTION",
            "SERVICE_DATE_FROM": "SERVICE_DATE_FROM",
            "SERVICE_DATE_TO": "SERVICE_DATE_TO",
            "CLAIM_SUBMISSION_DATE": "CLAIM_SUBMISSION_DATE",
            "TOTAL_CHARGE_AMOUNT": "TOTAL_CHARGE_AMOUNT",
            "TOTAL_PAID_AMOUNT": "TOTAL_PAID_AMOUNT",
            "PATIENT_RESPONSIBILITY": "PATIENT_RESPONSIBILITY",
            "INSURANCE_CARRIER": "PRIMARY_INSURANCE_CARRIER",
        }
        
        for field in extracted_fields:
            standard_key = field_mapping.get(
                field.field_name,
                field.field_name
            )
            standardized[standard_key] = {
                "value": field.field_value,
                "confidence": field.confidence,
                "source": field.source
            }
        
        return standardized

    def process_directory(
        self,
        directory_path: str,
        output_file: str = "extraction_results.json"
    ) -> List[ClaimExtraction]:
        """
        Process all CMS-1500 claim files in a directory
        
        Args:
            directory_path: Path to directory containing claim files
            output_file: Output file for results
            
        Returns:
            List of extraction results
        """
        results = []
        directory = Path(directory_path)
        
        # Find all JSON and TIFF files
        json_files = list(directory.glob("**/*.json"))
        tiff_files = list(directory.glob("**/*.tiff")) + list(directory.glob("**/*.tif"))
        
        all_files = json_files + tiff_files
        logger.info(f"Found {len(all_files)} claim files to process")
        
        for file_path in tqdm(all_files, desc="Processing claims"):
            try:
                if file_path.suffix.lower() == ".json":
                    extraction_result = self.extract_from_json(str(file_path))
                    file_type = "json"
                else:
                    extraction_result = self.extract_from_tiff(str(file_path))
                    file_type = "tiff"
                
                # Standardize output
                standardized = self.standardize_output(
                    extraction_result["extracted_fields"],
                    extraction_result["claim_id"]
                )
                
                # Calculate overall confidence
                confidences = [
                    f.confidence for f in extraction_result["extracted_fields"]
                ]
                avg_confidence = (
                    sum(confidences) / len(confidences)
                    if confidences else 0.0
                )
                
                result = ClaimExtraction(
                    claim_id=extraction_result["claim_id"],
                    extracted_fields=extraction_result["extracted_fields"],
                    standardized_output=standardized,
                    extraction_confidence=avg_confidence,
                    processing_status="SUCCESS"
                )
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
                result = ClaimExtraction(
                    claim_id="UNKNOWN",
                    extracted_fields=[],
                    standardized_output={},
                    extraction_confidence=0.0,
                    processing_status=f"FAILED: {str(e)}"
                )
                results.append(result)
        
        # Save results
        self._save_results(results, output_file)
        
        return results

    def _save_results(
        self,
        results: List[ClaimExtraction],
        output_file: str
    ) -> None:
        """
        Save extraction results to JSON file
        
        Args:
            results: List of extraction results
            output_file: Output file path
        """
        output_data = {
            "total_claims": len(results),
            "successful_extractions": sum(
                1 for r in results if r.processing_status == "SUCCESS"
            ),
            "failed_extractions": sum(
                1 for r in results if r.processing_status != "SUCCESS"
            ),
            "average_confidence": np.mean([
                r.extraction_confidence for r in results
            ]),
            "results": [
                {
                    "claim_id": r.claim_id,
                    "extraction_confidence": r.extraction_confidence,
                    "processing_status": r.processing_status,
                    "standardized_output": r.standardized_output,
                    "extracted_fields_count": len(r.extracted_fields)
                }
                for r in results
            ]
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        
        logger.info(f"Results saved to {output_file}")


def main():
    """
    Main function to demonstrate CMS-1500 claims extraction
    """
    # Initialize extractor
    extractor = Qwen3BExtractor(model_name="Qwen/Qwen-1.8B-Chat")
    
    # Process example data directory
    data_dir = "data/examples"
    
    if os.path.exists(data_dir):
        logger.info(f"Processing claims from {data_dir}")
        results = extractor.process_directory(
            data_dir,
            output_file="extraction_results.json"
        )
        
        # Print summary
        logger.info("\n" + "="*50)
        logger.info("EXTRACTION SUMMARY")
        logger.info("="*50)
        successful = sum(1 for r in results if r.processing_status == "SUCCESS")
        logger.info(f"Total claims processed: {len(results)}")
        logger.info(f"Successful extractions: {successful}")
        logger.info(f"Failed extractions: {len(results) - successful}")
        logger.info(f"Average confidence: {np.mean([r.extraction_confidence for r in results]):.2%}")
        logger.info("="*50)
        
        # Print first result example
        if results:
            logger.info("\nFirst extraction result:")
            logger.info(json.dumps(
                results[0].standardized_output,
                indent=2,
                default=str
            ))
    else:
        logger.error(f"Data directory {data_dir} not found")
        logger.info("Please ensure example files are in data/examples/")


if __name__ == "__main__":
    main()
