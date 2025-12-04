#!/usr/bin/env python3
"""
Run Results Processing
Enrich Bedrock classifications with original chunk data and create final output
"""

import sys
import json

from config import FILE_PATHS


def main():
    """Main execution function for results processing"""
    
    print("="*80)
    print("PROCESSING FINAL RESULTS")
    print("="*80)
    
    # Load combined results (original chunks)
    combined_file = FILE_PATHS['combined_results']
    try:
        with open(combined_file, 'r') as f:
            combined_results = json.load(f)
        print(f"✓ Loaded combined results from: {combined_file}")
    except FileNotFoundError:
        print(f"❌ Error: Combined results file not found: {combined_file}")
        sys.exit(1)
    
    # Load classifications
    classifications_file = FILE_PATHS['bedrock_classifications']
    try:
        with open(classifications_file, 'r') as f:
            classifications = json.load(f)
        print(f"✓ Loaded classifications from: {classifications_file}")
    except FileNotFoundError:
        print(f"❌ Error: Classifications file not found: {classifications_file}")
        print(f"   Please run 'python run_bedrock_classification.py' first")
        sys.exit(1)
    
    # Collect all chunks IN ORDER (same as they were sent to Bedrock)
    all_chunks = []
    for result in combined_results:
        for match_dict in result['matches']:
            all_chunks.append(match_dict)
    
    print(f"\nTotal original chunks: {len(all_chunks)}")
    print(f"Total classifications: {len(classifications)}")
    
    # Create mapping: batch_X → original chunk_id
    batch_to_original = {}
    for i, chunk in enumerate(all_chunks):
        batch_id = f"batch_{i}"
        batch_to_original[batch_id] = chunk
    
    print(f"Created mapping for {len(batch_to_original)} chunks")
    
    # Enrich classifications with original data
    enriched_classifications = []
    missing_count = 0
    
    for classification in classifications:
        chunk_id = classification.get('chunk_id', '')
        
        # Find original chunk
        if chunk_id in batch_to_original:
            original_chunk = batch_to_original[chunk_id]
            
            # Merge classification with original chunk data
            enriched = {
                **original_chunk,  # Include all original chunk data
                'classification': classification.get('classification'),
                'confidence': classification.get('confidence'),
                'reasoning': classification.get('reasoning'),
                'intervention_type': classification.get('intervention_type')
            }
            enriched_classifications.append(enriched)
        else:
            print(f"⚠️  Warning: Could not find original chunk for {chunk_id}")
            missing_count += 1
            enriched_classifications.append(classification)
    
    if missing_count > 0:
        print(f"\n⚠️  Warning: {missing_count} classifications could not be mapped to original chunks")
    
    # Filter for positive classifications
    positive_chunks = [c for c in enriched_classifications if c.get('classification') == 'POSITIVE']
    
    print(f"\n📊 Final Results:")
    print(f"  Total classified chunks: {len(enriched_classifications)}")
    print(f"  POSITIVE (Resilient Infrastructure): {len(positive_chunks)} ({len(positive_chunks)/len(enriched_classifications)*100:.1f}%)")
    
    # Breakdown by intervention type
    intervention_types = {}
    for chunk in positive_chunks:
        int_type = chunk.get('intervention_type', 'Unknown')
        intervention_types[int_type] = intervention_types.get(int_type, 0) + 1
    
    if intervention_types:
        print(f"\n📋 Positive Chunks by Intervention Type:")
        for int_type, count in sorted(intervention_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {int_type}: {count}")
    
    # Breakdown by source (keyword/semantic/both)
    source_breakdown = {}
    for chunk in positive_chunks:
        found_by = chunk.get('found_by', 'unknown')
        source_breakdown[found_by] = source_breakdown.get(found_by, 0) + 1
    
    if source_breakdown:
        print(f"\n🔍 Positive Chunks by Discovery Method:")
        for method, count in sorted(source_breakdown.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {method}: {count}")
    
    # Save all enriched results
    output_file = FILE_PATHS['final_results']
    with open(output_file, 'w') as f:
        json.dump(enriched_classifications, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Saved enriched results to: {output_file}")
    
    # Save just positive results
    positive_file = output_file.replace('.json', '_positive_only.json')
    with open(positive_file, 'w') as f:
        json.dump(positive_chunks, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved positive-only results to: {positive_file}")
    
    print("\n" + "="*80)
    print("RESULTS PROCESSING COMPLETE")
    print("="*80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
