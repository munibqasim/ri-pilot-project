#!/usr/bin/env python3
"""
Run Bedrock Batch Classification
Submit deduplicated chunks to AWS Bedrock for classification
"""

import sys
import json

from config import AWS_CONFIG, FILE_PATHS
from models import CombinedMatch
from bedrock_classifier import run_bedrock_batch_classification


def json_to_combined_matches(json_data: dict) -> list:
    """Convert JSON data back to CombinedMatch objects"""
    matches = []
    for m in json_data['matches']:
        match = CombinedMatch(
            chunk_id=m['chunk_id'],
            text=m['text'],
            char_start=m['char_start'],
            char_end=m['char_end'],
            sources=m['sources'],
            matched_keywords=m.get('matched_keywords', []),
            similarity_score=m.get('similarity_score', 0.0),
            matched_query=m.get('matched_query', ''),
            sector=m.get('sector', ''),
            found_by=m['found_by']
        )
        matches.append(match)
    return matches


def main():
    """Main execution function for Bedrock classification"""
    
    print("="*80)
    print("AWS BEDROCK BATCH CLASSIFICATION")
    print("="*80)
    
    # Load combined results
    combined_file = FILE_PATHS['combined_results']
    
    try:
        with open(combined_file, 'r') as f:
            combined_results = json.load(f)
        print(f"✓ Loaded combined results from: {combined_file}")
    except FileNotFoundError:
        print(f"❌ Error: Combined results file not found: {combined_file}")
        print(f"   Please run 'python run_deduplication.py' first")
        sys.exit(1)
    
    # Collect all chunks across all files
    all_chunks = []
    for result in combined_results:
        chunks = json_to_combined_matches(result)
        all_chunks.extend(chunks)
    
    print(f"\nTotal chunks to classify: {len(all_chunks)}")
    
    # Confirm before proceeding (optional)
    response = input("\nProceed with Bedrock batch classification? (y/n): ")
    if response.lower() != 'y':
        print("Classification cancelled")
        return 0
    
    # Run classification
    try:
        classifications = run_bedrock_batch_classification(
            chunks=all_chunks,
            s3_bucket=AWS_CONFIG['s3_bucket'],
            s3_input_prefix=AWS_CONFIG['s3_input_prefix'],
            s3_output_prefix=AWS_CONFIG['s3_output_prefix'],
            batch_size=AWS_CONFIG['batch_size']
        )
        
        # Save classifications
        output_file = FILE_PATHS['bedrock_classifications']
        with open(output_file, 'w') as f:
            json.dump(classifications, f, indent=2)
        
        print(f"\n✓ Saved classifications to: {output_file}")
        
        # Quick summary
        positive = [c for c in classifications if c.get('classification') == 'POSITIVE']
        negative = [c for c in classifications if c.get('classification') == 'NEGATIVE']
        
        print(f"\n📊 Classification Results:")
        print(f"  Total: {len(classifications)}")
        print(f"  POSITIVE: {len(positive)} ({len(positive)/len(classifications)*100:.1f}%)")
        print(f"  NEGATIVE: {len(negative)} ({len(negative)/len(classifications)*100:.1f}%)")
        
    except Exception as e:
        print(f"\n❌ Error during classification: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\n" + "="*80)
    print("BEDROCK CLASSIFICATION COMPLETE")
    print("="*80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
