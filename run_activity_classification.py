#!/usr/bin/env python3
"""
Run Activity Classification (Phase 6)
Classify positive RI excerpts into 8 activity categories using AWS Bedrock
"""

import sys
import json
from collections import Counter

from config import AWS_CONFIG, FILE_PATHS
from activity_classifier import ActivityClassifier, deduplicate_excerpts


def main():
    """Main execution function for activity classification"""
    
    print("="*80)
    print("PHASE 6: ACTIVITY CLASSIFICATION")
    print("="*80)
    
    # Load positive RI results from Phase 5
    input_file = FILE_PATHS.get('final_results_positive', 'final_enriched_results_positive_only.json')
    
    try:
        with open(input_file, 'r') as f:
            positive_excerpts = json.load(f)
        print(f"✓ Loaded {len(positive_excerpts)} positive RI excerpts from: {input_file}")
    except FileNotFoundError:
        print(f"❌ Error: Input file not found: {input_file}")
        print(f"   Please run 'python run_results_processing.py' first (Phase 5)")
        sys.exit(1)
    
    if not positive_excerpts:
        print("❌ No positive excerpts found to classify")
        sys.exit(1)
    
    # Check if deduplication is needed
    deduplicate = input("\nRun deduplication on results? (y/n, default=y): ").strip().lower()
    deduplicate = deduplicate != 'n'  # Default to yes
    
    if deduplicate:
        similarity_threshold = input("Similarity threshold for deduplication (0-1, default=0.85): ").strip()
        try:
            similarity_threshold = float(similarity_threshold) if similarity_threshold else 0.85
        except ValueError:
            similarity_threshold = 0.85
            print(f"Invalid input, using default: {similarity_threshold}")
    
    # Confirm before proceeding
    response = input(f"\nProceed with activity classification of {len(positive_excerpts)} excerpts? (y/n): ")
    if response.lower() != 'y':
        print("Classification cancelled")
        return 0
    
    # Initialize classifier
    classifier = ActivityClassifier(
        s3_bucket=AWS_CONFIG['s3_bucket'],
        region=AWS_CONFIG['region']
    )
    
    try:
        # Prepare input (with padding if needed for Bedrock minimum)
        input_s3_key = classifier.prepare_activity_input(positive_excerpts)
        
        # Submit job
        job_arn = classifier.submit_activity_job(input_s3_key)
        
        # Monitor
        print(f"\n⏳ Processing activity classifications...")
        classifier.monitor_job(job_arn, poll_interval=30)
        
        # Download and parse
        final_results = classifier.download_and_parse_results(job_arn, positive_excerpts)
        
        # Deduplication (optional)
        if deduplicate and final_results:
            print(f"\nRunning deduplication with threshold: {similarity_threshold}")
            
            # Save version with duplicates
            with open('final_ri_classifications_with_duplicates.json', 'w') as f:
                json.dump(final_results, f, indent=2)
            print(f"✓ Saved version WITH duplicates to: final_ri_classifications_with_duplicates.json")
            
            # Deduplicate
            deduplicated_results = deduplicate_excerpts(final_results, similarity_threshold)
            
            # Save deduplicated version
            output_file = 'final_ri_classifications.json'
            with open(output_file, 'w') as f:
                json.dump(deduplicated_results, f, indent=2)
            print(f"✓ Saved deduplicated version to: {output_file}")
            
            results_to_summarize = deduplicated_results
        else:
            # Save without deduplication
            output_file = 'final_ri_classifications.json'
            with open(output_file, 'w') as f:
                json.dump(final_results, f, indent=2)
            print(f"\n✓ Saved {len(final_results)} final classifications to: {output_file}")
            results_to_summarize = final_results
        
        # Summary
        print("\n" + "="*80)
        print("ACTIVITY CLASSIFICATION SUMMARY")
        print("="*80)
        
        activity_counts = {}
        for result in results_to_summarize:
            activity = result.get('activity_type', 'Unknown')
            activity_counts[activity] = activity_counts.get(activity, 0) + 1
        
        print(f"\n📊 Breakdown by activity type ({len(results_to_summarize)} unique interventions):")
        for activity, count in sorted(activity_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(results_to_summarize) * 100) if results_to_summarize else 0
            print(f"  {activity}: {count} ({percentage:.1f}%)")
        
        # Confidence breakdown
        confidence_counts = Counter([r.get('activity_confidence', 'UNKNOWN') for r in results_to_summarize])
        print(f"\n📈 Confidence levels:")
        for conf, count in confidence_counts.most_common():
            percentage = (count / len(results_to_summarize) * 100) if results_to_summarize else 0
            print(f"  {conf}: {count} ({percentage:.1f}%)")
        
        # Show sample results
        print(f"\n📋 Sample results (first 3):")
        for i, result in enumerate(results_to_summarize[:3], 1):
            print(f"\n  {i}. Activity: {result.get('activity_type', 'Unknown')}")
            print(f"     Confidence: {result.get('activity_confidence', 'UNKNOWN')}")
            print(f"     Reasoning: {result.get('activity_reasoning', 'N/A')}")
            text_preview = result.get('text', '')[:150] + "..." if len(result.get('text', '')) > 150 else result.get('text', '')
            print(f"     Text: {text_preview}")
        
    except Exception as e:
        print(f"\n❌ Error during activity classification: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\n" + "="*80)
    print("ACTIVITY CLASSIFICATION COMPLETE")
    print(f"Final results saved to: {output_file}")
    print("="*80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
