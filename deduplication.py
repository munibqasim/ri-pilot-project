"""
Deduplication Module for RI Pilot Project
Handles cross-store deduplication between keyword and semantic search results
"""

import json
from typing import List, Dict

from models import KeywordMatch, SemanticMatch, CombinedMatch


class CrossStoreDeduplicator:
    """Deduplicate matches across keyword and semantic search stores"""
    
    def __init__(self, overlap_threshold: float = 0.5):
        """
        Args:
            overlap_threshold: Minimum overlap ratio to consider duplicates (0-1)
        """
        self.overlap_threshold = overlap_threshold
    
    def _calculate_overlap(self, start1: int, end1: int, 
                          start2: int, end2: int) -> float:
        """Calculate overlap ratio between two text spans"""
        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)
        
        if overlap_start >= overlap_end:
            return 0.0  # No overlap
        
        overlap_length = overlap_end - overlap_start
        span1_length = end1 - start1
        
        # Calculate overlap as percentage of first span
        return overlap_length / span1_length if span1_length > 0 else 0.0
    
    def deduplicate(self, keyword_matches: List[KeywordMatch], 
                   semantic_matches: List[SemanticMatch]) -> List[CombinedMatch]:
        """
        Deduplicate keyword and semantic matches
        
        Returns:
            List of CombinedMatch objects with duplicates merged
        """
        print("\n" + "="*80)
        print("CROSS-STORE DEDUPLICATION")
        print("="*80)
        
        print(f"\nInput:")
        print(f"  Keyword matches: {len(keyword_matches)}")
        print(f"  Semantic matches: {len(semantic_matches)}")
        
        # Convert to combined format
        combined_matches = []
        
        # Add all keyword matches first
        for kw_match in keyword_matches:
            combined = CombinedMatch(
                chunk_id=kw_match.chunk_id,
                text=kw_match.text,
                char_start=kw_match.char_start,
                char_end=kw_match.char_end,
                sources=["keyword_search"],
                matched_keywords=kw_match.matched_keywords,
                found_by="keyword_only"
            )
            combined_matches.append(combined)
        
        # Process semantic matches
        matched_semantic = 0
        new_semantic = 0
        
        for sem_match in semantic_matches:
            # Check if this semantic match overlaps with any existing keyword match
            found_overlap = False
            
            for combined in combined_matches:
                if "keyword_search" in combined.sources:
                    overlap = self._calculate_overlap(
                        sem_match.char_start, sem_match.char_end,
                        combined.char_start, combined.char_end
                    )
                    
                    if overlap >= self.overlap_threshold:
                        # Found overlap - merge semantic info into existing match
                        combined.sources.append("semantic_search")
                        combined.similarity_score = sem_match.similarity_score
                        combined.matched_query = sem_match.matched_query
                        combined.sector = sem_match.sector
                        combined.found_by = "both"
                        
                        # Extend text range if semantic match is larger
                        combined.char_start = min(combined.char_start, sem_match.char_start)
                        combined.char_end = max(combined.char_end, sem_match.char_end)
                        
                        # Use longer text
                        if len(sem_match.text) > len(combined.text):
                            combined.text = sem_match.text
                        
                        matched_semantic += 1
                        found_overlap = True
                        break
            
            if not found_overlap:
                # No overlap - add as new semantic-only match
                combined = CombinedMatch(
                    chunk_id=f"combined_{len(combined_matches):04d}",
                    text=sem_match.text,
                    char_start=sem_match.char_start,
                    char_end=sem_match.char_end,
                    sources=["semantic_search"],
                    similarity_score=sem_match.similarity_score,
                    matched_query=sem_match.matched_query,
                    sector=sem_match.sector,
                    found_by="semantic_only"
                )
                combined_matches.append(combined)
                new_semantic += 1
        
        # Sort by position
        combined_matches.sort(key=lambda x: x.char_start)
        
        # Final deduplication pass (in case of any remaining overlaps)
        final_matches = self._final_dedup_pass(combined_matches)
        
        # Statistics
        print(f"\nResults:")
        print(f"  Total unique chunks: {len(final_matches)}")
        
        found_by_keyword = len([m for m in final_matches if m.found_by == "keyword_only"])
        found_by_semantic = len([m for m in final_matches if m.found_by == "semantic_only"])
        found_by_both = len([m for m in final_matches if m.found_by == "both"])
        
        print(f"\nBreakdown:")
        print(f"  Found by keyword only: {found_by_keyword}")
        print(f"  Found by semantic only: {found_by_semantic}")
        print(f"  Found by both: {found_by_both}")
        
        print(f"\nDuplicates removed: {len(keyword_matches) + len(semantic_matches) - len(final_matches)}")
        print(f"Overlap rate: {found_by_both / len(final_matches) * 100:.1f}%")
        
        return final_matches
    
    def _final_dedup_pass(self, matches: List[CombinedMatch]) -> List[CombinedMatch]:
        """Final pass to remove any remaining overlaps"""
        if not matches:
            return []
        
        deduplicated = [matches[0]]
        
        for current in matches[1:]:
            last = deduplicated[-1]
            
            overlap = self._calculate_overlap(
                current.char_start, current.char_end,
                last.char_start, last.char_end
            )
            
            if overlap >= self.overlap_threshold:
                # Merge into last match
                # Combine sources
                for source in current.sources:
                    if source not in last.sources:
                        last.sources.append(source)
                
                # Merge keywords
                last.matched_keywords.extend(current.matched_keywords)
                last.matched_keywords = list(set(last.matched_keywords))
                
                # Keep higher similarity score
                if current.similarity_score > last.similarity_score:
                    last.similarity_score = current.similarity_score
                    last.matched_query = current.matched_query
                    last.sector = current.sector
                
                # Update found_by
                if len(last.sources) > 1:
                    last.found_by = "both"
                
                # Extend range
                last.char_start = min(last.char_start, current.char_start)
                last.char_end = max(last.char_end, current.char_end)
                
                # Use longer text
                if len(current.text) > len(last.text):
                    last.text = current.text
            else:
                # No overlap - add as new
                deduplicated.append(current)
        
        return deduplicated


# Helper Functions
def json_to_keyword_matches(json_data: Dict) -> Dict:
    """Convert JSON data back to KeywordMatch objects"""
    matches = []
    for m in json_data['matches']:
        match = KeywordMatch(
            chunk_id=m['chunk_id'],
            text=m['text'],
            matched_keywords=m['matched_keywords'],
            char_start=m['char_start'],
            char_end=m['char_end'],
            source=m['source']
        )
        matches.append(match)
    return {
        'file_name': json_data['file_name'],
        'project_id': json_data['project_id'],
        'matches': matches
    }


def json_to_semantic_matches(json_data: Dict) -> Dict:
    """Convert JSON data back to SemanticMatch objects"""
    matches = []
    for m in json_data['matches']:
        match = SemanticMatch(
            chunk_id=m['chunk_id'],
            text=m['text'],
            similarity_score=m['similarity_score'],
            matched_query=m['matched_query'],
            sector=m['sector'],
            char_start=m['char_start'],
            char_end=m['char_end'],
            source=m['source']
        )
        matches.append(match)
    return {
        'file_name': json_data['file_name'],
        'project_id': json_data['project_id'],
        'matches': matches
    }


def process_pad_with_deduplication(keyword_results: Dict, semantic_results: Dict) -> Dict:
    """Process a single PAD with cross-store deduplication"""
    
    print(f"\n{'='*80}")
    print(f"Processing: {keyword_results['file_name']}")
    print(f"{'='*80}")
    
    # Initialize deduplicator
    deduplicator = CrossStoreDeduplicator(overlap_threshold=0.5)
    
    # Deduplicate
    combined_matches = deduplicator.deduplicate(
        keyword_results['matches'],
        semantic_results['matches']
    )
    
    # Calculate stats
    found_by_keyword = len([m for m in combined_matches if m.found_by == "keyword_only"])
    found_by_semantic = len([m for m in combined_matches if m.found_by == "semantic_only"])
    found_by_both = len([m for m in combined_matches if m.found_by == "both"])
    
    return {
        'file_name': keyword_results['file_name'],
        'project_id': keyword_results['project_id'],
        'total_matches': len(combined_matches),
        'found_by_keyword_only': found_by_keyword,
        'found_by_semantic_only': found_by_semantic,
        'found_by_both': found_by_both,
        'matches': combined_matches
    }


def save_combined_results(results: List[Dict], output_file: str = "combined_deduplicated_results.json"):
    """Save deduplicated combined results"""
    
    json_results = []
    
    for result in results:
        matches_dicts = []
        for match in result['matches']:
            matches_dicts.append({
                'chunk_id': match.chunk_id,
                'text': match.text,
                'char_start': match.char_start,
                'char_end': match.char_end,
                'sources': match.sources,
                'found_by': match.found_by,
                'matched_keywords': match.matched_keywords,
                'similarity_score': match.similarity_score,
                'matched_query': match.matched_query,
                'sector': match.sector
            })
        
        json_results.append({
            'file_name': result['file_name'],
            'project_id': result['project_id'],
            'total_matches': result['total_matches'],
            'found_by_keyword_only': result['found_by_keyword_only'],
            'found_by_semantic_only': result['found_by_semantic_only'],
            'found_by_both': result['found_by_both'],
            'matches': matches_dicts
        })
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Combined results saved to: {output_file}")
