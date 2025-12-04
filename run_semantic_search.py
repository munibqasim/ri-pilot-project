#!/usr/bin/env python3
"""
Run Semantic Search
Execute semantic search on PAD documents for resilient infrastructure
"""

import sys

from config import SEMANTIC_QUERIES, SEARCH_PARAMS, FILE_PATHS
from semantic_search import process_pad_semantic_search, save_semantic_results


def main():
    """Main execution function for semantic search"""
    
    print("="*80)
    print("SEMANTIC SEARCH - RESILIENT INFRASTRUCTURE")
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
        print("\nUsage: python run_semantic_search.py <pad_file1> <pad_file2> ...")
    
    print(f"\nSemantic queries to use: {len(SEMANTIC_QUERIES)}")
    for i, query in enumerate(SEMANTIC_QUERIES, 1):
        print(f"  {i}. {query['sector']}")
    
    # Process each PAD
    all_results = []
    
    for pad_file in pad_files:
        try:
            result = process_pad_semantic_search(
                pad_file, 
                SEMANTIC_QUERIES, 
                top_k=10  # Top-10 results per query
            )
            all_results.append(result)
            
            # Display sample matches
            print(f"\n--- Sample Matches (top 3) ---")
            for i, match in enumerate(result['matches'][:3]):
                print(f"\nMatch #{i+1}:")
                print(f"  Sector: {match.sector}")
                print(f"  Similarity: {match.similarity_score:.3f}")
                print(f"  Query: {match.matched_query}")
                print(f"  Text: {match.text[:200]}...")
            
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
    
    # Summary
    print("\n" + "="*80)
    print("SEMANTIC SEARCH SUMMARY")
    print("="*80)
    
    total_matches = sum(r['total_matches'] for r in all_results)
    print(f"\nTotal PADs processed: {len(all_results)}")
    print(f"Total semantic matches: {total_matches}")
    
    for result in all_results:
        print(f"\n{result['file_name']}:")
        print(f"  Total: {result['total_matches']}")
        for sector, count in result['sector_breakdown'].items():
            print(f"    - {sector}: {count}")
    
    # Save results
    output_file = FILE_PATHS['semantic_results']
    save_semantic_results(all_results, output_file)
    
    print("\n" + "="*80)
    print("SEMANTIC SEARCH COMPLETE")
    print(f"Results saved to: {output_file}")
    print("="*80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
