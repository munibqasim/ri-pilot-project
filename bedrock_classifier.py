"""
Bedrock Batch Classification Module for RI Pilot Project
Handles AWS Bedrock batch inference for classifying resilient infrastructure chunks
"""

import os
import json
import time
import boto3
from datetime import datetime
from typing import List, Dict

from models import CombinedMatch


class BedrockBatchClassifier:
    """AWS Bedrock batch classifier for resilient infrastructure"""
    
    def __init__(self, 
                 s3_bucket: str,
                 s3_input_prefix: str = "bedrock-batch/input",
                 s3_output_prefix: str = "bedrock-batch/output",
                 region: str = "us-east-1"):
        """
        Initialize Bedrock batch classifier
        
        Args:
            s3_bucket: Your S3 bucket name
            s3_input_prefix: S3 prefix for input files
            s3_output_prefix: S3 prefix for output files
            region: AWS region
        """
        self.s3_bucket = s3_bucket
        self.s3_input_prefix = s3_input_prefix
        self.s3_output_prefix = s3_output_prefix
        self.region = region
        
        # Initialize clients
        self.s3_client = boto3.client('s3', region_name=region)
        self.bedrock_client = boto3.client('bedrock', region_name=region)
        
        # Model ID for Claude Sonnet 4
        self.model_id = "anthropic.claude-sonnet-4-20250514"
        
        print(f"✓ Initialized Bedrock client")
        print(f"  Region: {region}")
        print(f"  S3 Bucket: {s3_bucket}")
        print(f"  Model: {self.model_id}")
    
    def create_classification_prompt(self, chunk_text: str, chunk_id: str) -> str:
        """Create classification prompt for chunks"""
        
        prompt = f"""You are an expert in resilient infrastructure evaluation for World Bank projects.

Your task is to determine if the following text excerpt describes a genuine resilient infrastructure intervention according to the official definition.

---
RESILIENT INFRASTRUCTURE DEFINITION:

Resilient infrastructure refers to features or actions within infrastructure projects that enhance their ability to withstand and recover from adverse events, ensuring continued service and functionality, particularly to the most vulnerable groups of society. The focus is on infrastructure systems that are robust, redundant, flexible, and adaptive enough to respond effectively to various stresses, including environmental, economic, or social.

Resilient infrastructure investments start by clearly identifying the hazards that threaten the investments, and involve an assessment to select the measures that secure the economic return from the investment. A resilient infrastructure investment does not always require additional resources—it is a way of investing smartly by accounting for the uncertainty of occurrence of extreme events.

KEY ELEMENTS:
- Robustness: Physical strength or durability to resist impacts from identified risks
- Redundancy: Backup systems allowing infrastructure to operate even if one part fails
- Adaptability: Capacity to be modified in response to changing conditions or future risks
- Flexibility: Ability to change, evolve, and adapt when disruptions occur
- Rapidity: Capacity to quickly recover from disruptions
- Integration: Designing infrastructure with consideration for interdependencies and surrounding systems
- Preventive Maintenance: Routine checks, upgrades, and disaster recovery plans

QUALIFYING ACTIVITIES:
(i) Improved engineering design that considers exposure to identified hazards
(ii) Risk-informed asset management covering infrastructure condition monitoring, preventive maintenance, and rapid repair
(iii) Business continuity planning and contingency programming informed by early-warning systems
(iv) A systems approach to planning
(v) Strong stakeholder engagement, coordination and institutional capacity

---
EXAMPLES:

EXAMPLE 1 - POSITIVE:
Text: "The project will upgrade 15 substations to enhance their resilience to flooding and seismic events. This includes: (i) elevating critical equipment above the 100-year flood level; (ii) installing seismic isolation systems for transformers; (iii) deploying mobile substations for rapid response and recovery to climate events."

Classification:
{{
  "classification": "POSITIVE",
  "confidence": "HIGH",
  "reasoning": "Explicitly describes infrastructure upgrades with specific resilience features (elevation, seismic protection, mobile backups) to address identified hazards.",
  "intervention_type": "Engineering Design"
}}

EXAMPLE 2 - NEGATIVE (Boilerplate/Acronyms):
Text: "CERC - Contingent Emergency Response Component; DRM - Disaster Risk Management; ESMF - Environmental and Social Management Framework; GDP - Gross Domestic Product"

Classification:
{{
  "classification": "NEGATIVE",
  "confidence": "HIGH",
  "reasoning": "This is an acronym list with no description of actual resilient infrastructure interventions or measures.",
  "intervention_type": "NONE"
}}

EXAMPLE 3 - NEGATIVE (Problem Description Only):
Text: "The region faces significant climate risks including recurrent flooding, landslides, and extreme temperature events. These hazards threaten existing infrastructure and pose challenges to service delivery."

Classification:
{{
  "classification": "NEGATIVE",
  "confidence": "HIGH",
  "reasoning": "Describes climate risks and problems but does not describe any resilient infrastructure solutions, interventions, or measures to address these hazards.",
  "intervention_type": "NONE"
}}

---
TEXT EXCERPT TO EVALUATE:

{chunk_text}

---
CLASSIFICATION INSTRUCTIONS:

Analyze the text above and respond ONLY with a JSON object in this exact format:

{{
  "chunk_id": "{chunk_id}",
  "classification": "POSITIVE" or "NEGATIVE",
  "confidence": "HIGH" or "MEDIUM" or "LOW",
  "reasoning": "Brief explanation (1-2 sentences) of why this is/isn't resilient infrastructure",
  "intervention_type": "Select ONE: Engineering Design | Asset Management | Contingency Planning | System Planning | Institutional Capacity | Environmental Considerations | Cross-Sectoral Integration | Community Engagement | NONE"
}}

CRITICAL RULES:
- Mark POSITIVE only if text explicitly describes infrastructure features/actions that enhance resilience
- Mark NEGATIVE if it's general infrastructure, problem descriptions, acronym lists, or boilerplate text
- Respond with ONLY valid JSON, no additional text before or after"""
    
        return prompt
        
    def prepare_batch_input(self, chunks: List[CombinedMatch], 
                           batch_size: int = 5) -> str:
        """
        Prepare batch input files for Bedrock
        
        Args:
            chunks: List of CombinedMatch objects to classify
            batch_size: Number of chunks per batch request
        
        Returns:
            S3 key for uploaded input file
        """
        print(f"\nPreparing batch input...")
        print(f"  Total chunks: {len(chunks)}")
        print(f"  Batch size: {batch_size}")
        
        batches = []
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            batches.append(batch)
        
        print(f"  Number of batches: {len(batches)}")
        
        # Create JSONL file with all requests
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        input_file = f"ri_classification_input_{timestamp}.jsonl"
        
        requests = []
        for batch_idx, batch in enumerate(batches):
            # Create single request with multiple chunks
            combined_text = "\n\n---CHUNK SEPARATOR---\n\n".join([
                f"CHUNK {i+1} (ID: {chunk.chunk_id}):\n{chunk.text}"
                for i, chunk in enumerate(batch)
            ])
            
            prompt = self.create_classification_prompt(combined_text, f"batch_{batch_idx}")
            
            request = {
                "recordId": f"batch_{batch_idx}",
                "modelInput": {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 2000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }
            }
            requests.append(request)
        
        # Write to local file
        with open(input_file, 'w') as f:
            for request in requests:
                f.write(json.dumps(request) + '\n')
        
        # Upload to S3
        s3_key = f"{self.s3_input_prefix}/{input_file}"
        self.s3_client.upload_file(input_file, self.s3_bucket, s3_key)
        
        print(f"✓ Uploaded input file to s3://{self.s3_bucket}/{s3_key}")
        
        # Clean up local file
        os.remove(input_file)
        
        return s3_key
    
    def submit_batch_job(self, input_s3_key: str, job_name: str = None) -> str:
        """
        Submit batch inference job to Bedrock
        
        Args:
            input_s3_key: S3 key of input JSONL file
            job_name: Optional custom job name
        
        Returns:
            Job ARN
        """
        if job_name is None:
            job_name = f"ri-classification-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        print(f"\nSubmitting batch job: {job_name}")
        
        response = self.bedrock_client.create_model_invocation_job(
            roleArn=f"arn:aws:iam::{self._get_account_id()}:role/BedrockBatchInferenceRole",
            modelId=self.model_id,
            jobName=job_name,
            inputDataConfig={
                "s3InputDataConfig": {
                    "s3Uri": f"s3://{self.s3_bucket}/{input_s3_key}"
                }
            },
            outputDataConfig={
                "s3OutputDataConfig": {
                    "s3Uri": f"s3://{self.s3_bucket}/{self.s3_output_prefix}/"
                }
            }
        )
        
        job_arn = response['jobArn']
        print(f"✓ Job submitted successfully")
        print(f"  Job ARN: {job_arn}")
        
        return job_arn
    
    def _get_account_id(self) -> str:
        """Get AWS account ID"""
        sts = boto3.client('sts')
        return sts.get_caller_identity()['Account']
    
    def monitor_job(self, job_arn: str, poll_interval: int = 30):
        """
        Monitor batch job until completion
        
        Args:
            job_arn: Job ARN to monitor
            poll_interval: Seconds between status checks
        """
        print(f"\nMonitoring job: {job_arn}")
        print(f"Polling every {poll_interval} seconds...\n")
        
        while True:
            response = self.bedrock_client.get_model_invocation_job(
                jobIdentifier=job_arn
            )
            
            status = response['status']
            
            if status == 'Completed':
                print(f"\n✓ Job completed successfully!")
                print(f"  Output location: {response['outputDataConfig']['s3OutputDataConfig']['s3Uri']}")
                return response
            
            elif status == 'Failed':
                print(f"\n❌ Job failed!")
                print(f"  Message: {response.get('message', 'No error message')}")
                return response
            
            elif status in ['InProgress', 'Submitted']:
                print(f"  Status: {status} - waiting...", end='\r')
                time.sleep(poll_interval)
            
            else:
                print(f"  Unknown status: {status}")
                time.sleep(poll_interval)
    
    def download_results(self, job_arn: str, local_dir: str = "bedrock_results") -> str:
        """
        Download and parse batch results
        
        Args:
            job_arn: Job ARN
            local_dir: Local directory to save results
        
        Returns:
            Path to downloaded results file
        """
        # Get job details
        response = self.bedrock_client.get_model_invocation_job(
            jobIdentifier=job_arn
        )
        
        output_uri = response['outputDataConfig']['s3OutputDataConfig']['s3Uri']
        
        # Parse S3 URI
        parts = output_uri.replace("s3://", "").split("/")
        bucket = parts[0]
        prefix = "/".join(parts[1:])
        
        # List objects in output location
        response = self.s3_client.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix
        )
        
        # Find output file
        output_files = [obj['Key'] for obj in response.get('Contents', []) 
                       if obj['Key'].endswith('.out')]
        
        if not output_files:
            print("❌ No output files found")
            return None
        
        output_key = output_files[0]
        
        # Download
        os.makedirs(local_dir, exist_ok=True)
        local_file = os.path.join(local_dir, os.path.basename(output_key))
        
        self.s3_client.download_file(bucket, output_key, local_file)
        
        print(f"✓ Downloaded results to: {local_file}")
        
        return local_file
    
    def parse_results(self, results_file: str) -> List[Dict]:
        """Parse Bedrock batch results"""
        
        classifications = []
        
        with open(results_file, 'r') as f:
            for line in f:
                result = json.loads(line)
                
                if result.get('modelOutput'):
                    content = result['modelOutput']['content'][0]['text']
                    
                    # Parse JSON response
                    try:
                        # Strip markdown code blocks if present
                        content = content.replace('```json\n', '').replace('\n```', '').strip()
                        classification = json.loads(content)
                        classifications.append(classification)
                    except json.JSONDecodeError:
                        print(f"⚠️  Failed to parse response for record: {result.get('recordId')}")
                        continue
        
        print(f"✓ Parsed {len(classifications)} classifications")
        
        return classifications


def run_bedrock_batch_classification(chunks: List[CombinedMatch], 
                                     s3_bucket: str,
                                     s3_input_prefix: str,
                                     s3_output_prefix: str,
                                     batch_size: int = 5) -> List[Dict]:
    """
    Complete workflow for Bedrock batch classification
    
    Args:
        chunks: List of chunks to classify
        s3_bucket: Your S3 bucket name
        s3_input_prefix: S3 prefix for input files
        s3_output_prefix: S3 prefix for output files
        batch_size: Chunks per batch request
    
    Returns:
        List of classification results
    """
    
    print("="*80)
    print("BEDROCK BATCH CLASSIFICATION")
    print("="*80)
    
    # Initialize classifier
    classifier = BedrockBatchClassifier(
        s3_bucket=s3_bucket,
        s3_input_prefix=s3_input_prefix,
        s3_output_prefix=s3_output_prefix,
        region="us-east-1"
    )
    
    # Step 1: Prepare input
    input_s3_key = classifier.prepare_batch_input(chunks, batch_size=batch_size)
    
    # Step 2: Submit job
    job_arn = classifier.submit_batch_job(input_s3_key)
    
    # Step 3: Monitor
    classifier.monitor_job(job_arn, poll_interval=30)
    
    # Step 4: Download results
    results_file = classifier.download_results(job_arn)
    
    # Step 5: Parse results
    classifications = classifier.parse_results(results_file)
    
    return classifications
