#!/usr/bin/env python3
"""
Run Deduplication
Combine and deduplicate keyword and semantic search results
"""

import sys
import json

from config import FILE_PATHS, SEARCH_PARAMS
from deduplication import (
    json_to_keyword_matches,
    json_to_semantic_matches,
    process_pad_with_deduplication,
    save_combined_results
)


def main():
    """Main execution function for deduplication"""
    
    print("="*80)
    print("COMBINING KEYWORD + SEMANTIC RESULTS")
    print("="*80)
    
    # Load results from JSON files
    keyword_file = FILE_PATHS['keyword_results']
    semantic_file = FILE_PATHS['semantic_results']
    
    try:
        with open(keyword_file, 'r') as f:
            keyword_results_list = json.load(f)
        print(f"✓ Loaded keyword results from: {keyword_file}")
    except FileNotFoundError:
        print(f"❌ Error: Keyword results file not found: {keyword_file}")
        print(f"   Please run 'python run_keyword_search.py' first")
        sys.exit(1)
    
    try:
        with open(semantic_file, 'r') as f:
            semantic_results_list = json.load(f)
        print(f"✓ Loaded semantic results from: {semantic_file}")
    except FileNotFoundError:
        print(f"❌ Error: Semantic results file not found: {semantic_file}")
        print(f"   Please run 'python run_semantic_search.py' first")
        sys.exit(1)
    
    # Check if number of files match
    if len(keyword_results_list) != len(semantic_results_list):
        print(f"\n⚠️  Warning: Number of files don't match!")
        print(f"   Keyword results: {len(keyword_results_list)} files")
        print(f"   Semantic results: {len(semantic_results_list)} files")
        print(f"   Will process only matching files")
    
    # Convert JSON to objects
    print("\nConverting JSON to objects...")
    keyword_results_all = [json_to_keyword_matches(kw) for kw in keyword_results_list]
    semantic_results_all = [json_to_semantic_matches(sem) for sem in semantic_results_list]
    
    # Process files
    all_combined = []
    num_files = min(len(keyword_results_all), len(semantic_results_all))
    
    for i in range(num_files):
        combined = process_pad_with_deduplication(
            keyword_results_all[i],
            semantic_results_all[i]
        )
        all_combined.append(combined)
    
    # Combined summary
    print("\n" + "="*80)
    print("FINAL SUMMARY ACROSS ALL PADS")
    print("="*80)
    
    total_matches = sum(r['total_matches'] for r in all_combined)
    total_keyword_only = sum(r['found_by_keyword_only'] for r in all_combined)
    total_semantic_only = sum(r['found_by_semantic_only'] for r in all_combined)
    total_both = sum(r['found_by_both'] for r in all_combined)
    
    print(f"\nTotal unique chunks across all PADs: {total_matches}")
    print(f"\nMethod comparison:")
    print(f"  Keyword only: {total_keyword_only} ({total_keyword_only/total_matches*100:.1f}%)")
    print(f"  Semantic only: {total_semantic_only} ({total_semantic_only/total_matches*100:.1f}%)")
    print(f"  Both methods: {total_both} ({total_both/total_matches*100:.1f}%)")
    
    print(f"\n📊 Key Insights:")
    print(f"  - Keyword recall: {(total_keyword_only + total_both) / total_matches * 100:.1f}%")
    print(f"  - Semantic recall: {(total_semantic_only + total_both) / total_matches * 100:.1f}%")
    print(f"  - Complementary value: {total_semantic_only} chunks ONLY found by semantic search")
    
    # Show per-PAD breakdown
    print(f"\n📄 Per-PAD Breakdown:")
    for result in all_combined:
        print(f"\n{result['file_name']}:")
        print(f"  Total: {result['total_matches']}")
        print(f"  Keyword only: {result['found_by_keyword_only']}")
        print(f"  Semantic only: {result['found_by_semantic_only']}")
        print(f"  Both: {result['found_by_both']}")
    
    # Save results
    output_file = FILE_PATHS['combined_results']
    save_combined_results(all_combined, output_file)
    
    print("\n" + "="*80)
    print("DEDUPLICATION COMPLETE")
    print(f"Results saved to: {output_file}")
    print("="*80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
