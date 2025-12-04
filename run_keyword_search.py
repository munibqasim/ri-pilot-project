#!/usr/bin/env python3
"""
Run Keyword Search
Execute keyword-based search on PAD documents for resilient infrastructure
"""

import sys
from typing import List

from config import RI_KEYWORDS, FILE_PATHS
from keyword_search import KeywordSearcher, process_pad, display_sample_matches, save_results


def flatten_keywords(keyword_dict: dict) -> List[str]:
    """Flatten the nested keyword dictionary into a single list"""
    all_keywords = []
    for category, keywords in keyword_dict.items():
        all_keywords.extend(keywords)
    return all_keywords


def main():
    """Main execution function for keyword search"""
    
    print("="*80)
    print("KEYWORD SEARCH - RESILIENT INFRASTRUCTURE")
    print("="*80)
    
    # Get PAD files from command line or use default
    if len(sys.argv) > 1:
        pad_files = sys.argv[1:]
    else:
        # Default example - user should replace with their actual files
        pad_files = [
            "pad_P162151_2020-05-07_D32037168.txt",
            "pad_P150816_2017-04-14_D27370130.txt"
        ]
        print("\n⚠️  No input files specified. Using example files:")
        for f in pad_files:
            print(f"  - {f}")
        print("\nUsage: python run_keyword_search.py <pad_file1> <pad_file2> ...")
    
    # Flatten keywords
    all_keywords = flatten_keywords(RI_KEYWORDS)
    
    # Initialize searcher
    print(f"\nInitializing keyword searcher...")
    searcher = KeywordSearcher(all_keywords)
    print(f"✓ Loaded {len(all_keywords)} keywords across {len(RI_KEYWORDS)} categories")
    
    # Process each PAD
    all_results = []
    
    for pad_file in pad_files:
        try:
            result = process_pad(pad_file, searcher)
            all_results.append(result)
            
            # Display sample matches
            display_sample_matches(result['matches'], num_samples=3)
            
        except FileNotFoundError:
            print(f"\n❌ Error: File not found: {pad_file}")
            print(f"   Please provide valid file paths")
            continue
        except Exception as e:
            print(f"\n❌ Error processing {pad_file}: {str(e)}")
            import traceback
            traceback.print_exc()
            continue
    
    if not all_results:
        print("\n❌ No files were successfully processed")
        sys.exit(1)
    
    # Summary across all PADs
    print("\n" + "="*80)
    print("SUMMARY ACROSS ALL PADS")
    print("="*80)
    
    total_matches = sum(r['total_matches'] for r in all_results)
    print(f"\nTotal PADs processed: {len(all_results)}")
    print(f"Total keyword matches: {total_matches}")
    
    for result in all_results:
        print(f"\n{result['file_name']}:")
        print(f"  - Matches: {result['total_matches']}")
        print(f"  - Unique keywords: {result['unique_keywords']}")
    
    # Save results
    output_file = FILE_PATHS['keyword_results']
    save_results(all_results, output_file)
    
    print("\n" + "="*80)
    print("KEYWORD SEARCH COMPLETE")
    print(f"Results saved to: {output_file}")
    print("="*80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
