"""
Activity Classification Module for RI Pilot Project
Classifies RI excerpts into 8 activity categories using AWS Bedrock
"""

import os
import json
import time
import boto3
from datetime import datetime
from typing import List, Dict
from difflib import SequenceMatcher


class ActivityClassifier:
    """Classify RI excerpts into 8 activity types"""
    
    def __init__(self, s3_bucket: str, region: str = "us-east-1"):
        self.s3_bucket = s3_bucket
        self.region = region
        self.s3_input_prefix = "bedrock-ri-batch/activity-input"
        self.s3_output_prefix = "bedrock-ri-batch/activity-output"
        
        self.s3_client = boto3.client('s3', region_name=region)
        self.bedrock_client = boto3.client('bedrock', region_name=region)
        
        self.model_id = "anthropic.claude-sonnet-4-20250514"
        
        print(f"✓ Initialized Activity Classifier")
    
    def create_activity_classification_prompt(self, excerpt: str, chunk_id: str) -> str:
        """Create prompt for activity classification"""
        
        prompt = f"""You are an expert in resilient infrastructure evaluation for World Bank projects.

Your task is to classify the following resilient infrastructure excerpt into ONE of the 8 activity categories.

---
ACTIVITY CATEGORIES:

1. **Institutional Capacity**: Ability of institutions to manage and govern infrastructure systems, including policy formulation, regulation enforcement, resource mobilization, and stakeholder coordination.

2. **System Planning**: Strategic planning of infrastructure considering urban growth, demographics, economic development, and climate change impacts to ensure resilience and sustainability.

3. **Engineering Design**: Technical design incorporating resilience features to withstand hazards using durable materials, innovative construction, and climate considerations.

4. **Asset Management**: Regular maintenance and operation throughout lifecycle, including condition monitoring, preventive maintenance, and rapid repair.

5. **Contingency Planning and Business Continuity**: Emergency response plans, backup systems, and alternative service delivery to ensure infrastructure continues operating during/after disruptions.

6. **Environmental and Ecosystem Considerations**: Integrating environmental and ecosystem-based approaches for natural solutions that enhance resilience and support biodiversity.

7. **Cross-Sectoral Integration**: Addressing interdependencies between infrastructure systems to ensure resilience in one sector enhances others.

8. **Community Engagement and Public Awareness**: Engaging communities in planning, operation, and maintenance to ensure projects are socially inclusive and meet user needs.

---
RI EXCERPT TO CLASSIFY:

{excerpt}

---
CLASSIFICATION INSTRUCTIONS:

Analyze the excerpt and determine which ONE activity category best describes it. Consider:
- What is the PRIMARY focus of this intervention?
- Which activity type does this most closely align with?
- If it spans multiple categories, choose the most dominant one

Respond ONLY with a JSON object:

{{
  "chunk_id": "{chunk_id}",
  "activity_type": "Select ONE: Institutional Capacity | System Planning | Engineering Design | Asset Management | Contingency Planning | Environmental Considerations | Cross-Sectoral Integration | Community Engagement",
  "confidence": "HIGH" or "MEDIUM" or "LOW",
  "reasoning": "Brief explanation (1 sentence) of why this activity type was chosen"
}}

Respond with ONLY valid JSON, no additional text."""

        return prompt
    
    def prepare_activity_input(self, extracted_excerpts: List[Dict]) -> str:
        """Prepare batch input for activity classification with padding"""
        
        print(f"\nPreparing activity classification input...")
        print(f"  Total excerpts: {len(extracted_excerpts)}")
        
        # AWS Bedrock requires minimum 100 records for batch jobs
        MIN_BATCH_SIZE = 100
        
        excerpts_to_process = extracted_excerpts.copy()
        
        if len(excerpts_to_process) < MIN_BATCH_SIZE:
            shortage = MIN_BATCH_SIZE - len(excerpts_to_process)
            print(f"  ⚠️  Need minimum {MIN_BATCH_SIZE} records, padding with {shortage} duplicates...")
            
            # Duplicate excerpts to reach minimum
            padding_excerpts = []
            for i in range(shortage):
                duplicate = excerpts_to_process[i % len(excerpts_to_process)].copy()
                # Mark as duplicate with unique ID
                duplicate['chunk_id'] = f"{duplicate['chunk_id']}_ACTIVITY_DUP_{i+1}"
                padding_excerpts.append(duplicate)
            
            excerpts_to_process.extend(padding_excerpts)
            print(f"  ✓ Padded to {len(excerpts_to_process)} records")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        input_file = f"ri_activity_input_{timestamp}.jsonl"
        
        requests = []
        for excerpt_data in excerpts_to_process:
            chunk_id = excerpt_data['chunk_id']
            excerpt = excerpt_data.get('extracted_excerpt', excerpt_data.get('text', ''))
            
            prompt = self.create_activity_classification_prompt(excerpt, chunk_id)
            
            request = {
                "recordId": chunk_id,
                "modelInput": {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 500,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }
            }
            requests.append(request)
        
        # Write and upload
        with open(input_file, 'w') as f:
            for request in requests:
                f.write(json.dumps(request) + '\n')
        
        s3_key = f"{self.s3_input_prefix}/{input_file}"
        self.s3_client.upload_file(input_file, self.s3_bucket, s3_key)
        
        print(f"✓ Uploaded to s3://{self.s3_bucket}/{s3_key}")
        print(f"  Total requests: {len(requests)}")
        
        os.remove(input_file)
        
        return s3_key
    
    def submit_activity_job(self, input_s3_key: str) -> str:
        """Submit activity classification job"""
        
        job_name = f"ri-activity-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        print(f"\nSubmitting activity classification job: {job_name}")
        
        account_id = boto3.client('sts').get_caller_identity()['Account']
        
        response = self.bedrock_client.create_model_invocation_job(
            roleArn=f"arn:aws:iam::{account_id}:role/BedrockBatchInferenceRole",
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
        print(f"✓ Job submitted: {job_arn}")
        
        return job_arn
    
    def monitor_job(self, job_arn: str, poll_interval: int = 30):
        """Monitor activity classification job"""
        
        print(f"\nMonitoring activity classification job...")
        print(f"Polling every {poll_interval} seconds...\n")
        
        while True:
            response = self.bedrock_client.get_model_invocation_job(
                jobIdentifier=job_arn
            )
            
            status = response['status']
            
            if status == 'Completed':
                print(f"\n✓ Activity classification completed!")
                return response
            elif status == 'Failed':
                print(f"\n❌ Job failed: {response.get('message', 'Unknown error')}")
                return response
            elif status in ['InProgress', 'Submitted', 'Validating', 'Scheduled']:
                print(f"  Status: {status} - waiting...", end='\r')
                time.sleep(poll_interval)
            else:
                print(f"  Unknown status: {status}")
                time.sleep(poll_interval)
    
    def download_and_parse_results(self, job_arn: str, 
                                   original_excerpts: List[Dict]) -> List[Dict]:
        """Download and parse activity classification results"""
        
        # Download
        response = self.bedrock_client.get_model_invocation_job(
            jobIdentifier=job_arn
        )
        
        output_uri = response['outputDataConfig']['s3OutputDataConfig']['s3Uri']
        parts = output_uri.replace("s3://", "").split("/")
        bucket = parts[0]
        prefix = "/".join(parts[1:])
        
        response = self.s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        output_files = [
            obj['Key'] for obj in response.get('Contents', []) 
            if obj['Key'].endswith('.out') and 'manifest' not in obj['Key'].lower()
        ]
        
        if not output_files:
            print("❌ No output files found")
            return []
        
        output_key = output_files[0]
        
        os.makedirs('activity_results', exist_ok=True)
        local_file = f"activity_results/{os.path.basename(output_key)}"
        
        self.s3_client.download_file(bucket, output_key, local_file)
        print(f"✓ Downloaded to: {local_file}")
        
        # Parse results
        activities = []
        
        with open(local_file, 'r') as f:
            for line in f:
                result = json.loads(line)
                
                if result.get('modelOutput'):
                    content = result['modelOutput']['content'][0]['text']
                    
                    try:
                        # Strip markdown if present
                        content = content.replace('```json\n', '').replace('\n```', '').strip()
                        activity = json.loads(content)
                        activities.append(activity)
                    except json.JSONDecodeError:
                        print(f"⚠️  Failed to parse: {result.get('recordId')}")
        
        print(f"✓ Parsed {len(activities)} activity classifications")
        
        # Remove duplicates (anything with _ACTIVITY_DUP_ in chunk_id)
        original_activities = [a for a in activities if '_ACTIVITY_DUP_' not in a['chunk_id']]
        duplicate_count = len(activities) - len(original_activities)
        
        if duplicate_count > 0:
            print(f"✓ Removed {duplicate_count} duplicate padding records")
        
        print(f"✓ Final count: {len(original_activities)} unique activity classifications")
        
        # Merge with excerpts
        excerpt_map = {e['chunk_id']: e for e in original_excerpts}
        
        final_results = []
        for activity in original_activities:
            chunk_id = activity['chunk_id']
            excerpt_data = excerpt_map.get(chunk_id, {})
            
            final = {
                'chunk_id': chunk_id,
                'text': excerpt_data.get('extracted_excerpt', excerpt_data.get('text', '')),
                'activity_type': activity['activity_type'],
                'activity_confidence': activity.get('confidence', 'UNKNOWN'),
                'activity_reasoning': activity.get('reasoning', ''),
                'classification': excerpt_data.get('classification', 'POSITIVE'),
                'confidence': excerpt_data.get('confidence', ''),
                'reasoning': excerpt_data.get('reasoning', ''),
                'intervention_type': excerpt_data.get('intervention_type', ''),
                'matched_keywords': excerpt_data.get('matched_keywords', []),
                'similarity_score': excerpt_data.get('similarity_score', 0.0),
                'sector': excerpt_data.get('sector', ''),
                'sources': excerpt_data.get('sources', []),
                'found_by': excerpt_data.get('found_by', '')
            }
            
            final_results.append(final)
        
        return final_results


def deduplicate_excerpts(results: List[Dict], similarity_threshold: float = 0.85) -> List[Dict]:
    """
    Deduplicate results based on text similarity
    
    Args:
        results: List of result dictionaries
        similarity_threshold: Similarity threshold for considering duplicates (0-1)
    
    Returns:
        Deduplicated list of results
    """
    
    print("\n" + "="*80)
    print("DEDUPLICATION")
    print("="*80)
    
    print(f"\nInput: {len(results)} classifications")
    
    # Remove empty texts first
    non_empty = [r for r in results if r.get('text') and len(r['text'].strip()) > 0]
    empty_count = len(results) - len(non_empty)
    
    if empty_count > 0:
        print(f"Removed {empty_count} empty excerpts")
    
    if not non_empty:
        print("⚠️  No non-empty excerpts to deduplicate")
        return []
    
    # Sort by text length (keep longer, more detailed versions)
    non_empty.sort(key=lambda x: len(x['text']), reverse=True)
    
    # Deduplicate based on text similarity
    unique_results = []
    duplicates = []
    
    for result in non_empty:
        text = result['text'].strip().lower()
        
        # Check if similar to any existing unique result
        is_duplicate = False
        for unique in unique_results:
            unique_text = unique['text'].strip().lower()
            
            # Calculate similarity
            similarity = SequenceMatcher(None, text, unique_text).ratio()
            
            if similarity >= similarity_threshold:
                is_duplicate = True
                duplicates.append({
                    'duplicate_id': result['chunk_id'],
                    'kept_id': unique['chunk_id'],
                    'similarity': similarity
                })
                break
        
        if not is_duplicate:
            unique_results.append(result)
    
    print(f"\nDeduplication results:")
    print(f"  Unique excerpts: {len(unique_results)}")
    print(f"  Duplicates removed: {len(duplicates)}")
    print(f"  Similarity threshold: {similarity_threshold}")
    
    return unique_results
