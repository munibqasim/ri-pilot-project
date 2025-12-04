"""
Semantic Search Module for RI Pilot Project
Handles semantic search using sentence embeddings
"""

import json
import torch
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer

from models import SemanticMatch


class SemanticSearcher:
    """Handles semantic search using sentence embeddings"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize semantic searcher
        
        Args:
            model_name: Sentence transformer model
                - "all-MiniLM-L6-v2" - Fast, good quality (default)
                - "all-mpnet-base-v2" - Better quality, slower
        """
        print(f"Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        print("✓ Model loaded")
    
    def _create_chunks(self, text: str, chunk_size: int = 500, 
                       overlap: int = 100) -> List[Tuple[str, int, int]]:
        """
        Create overlapping text chunks
        
        Args:
            text: Full document text
            chunk_size: Target chunk size in characters
            overlap: Overlap between chunks in characters
        
        Returns:
            List of (chunk_text, start_pos, end_pos)
        """
        chunks = []
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        
        current_chunk = ""
        chunk_start = 0
        current_pos = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                current_pos += 2  # \n\n
                continue
            
            # If adding this paragraph exceeds chunk_size, save current chunk
            if len(current_chunk) + len(para) > chunk_size and current_chunk:
                chunks.append((
                    current_chunk.strip(),
                    chunk_start,
                    current_pos
                ))
                
                # Start new chunk with overlap
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_text + " " + para
                chunk_start = current_pos - len(overlap_text)
            else:
                # Add to current chunk
                if current_chunk:
                    current_chunk += " " + para
                else:
                    current_chunk = para
                    chunk_start = current_pos
            
            current_pos += len(para) + 2  # +2 for \n\n
        
        # Add final chunk
        if current_chunk:
            chunks.append((
                current_chunk.strip(),
                chunk_start,
                current_pos
            ))
        
        return chunks
    
    def search(self, text: str, queries: List[Dict[str, str]], 
           top_k: int = 10) -> List[SemanticMatch]:
        """
        Search for semantically similar content
        
        Args:
            text: Document text to search
            queries: List of dicts with 'sector' and 'query' keys
            top_k: Number of top results per query
        
        Returns:
            List of SemanticMatch objects
        """
        print(f"\nCreating text chunks...")
        chunks = self._create_chunks(text, chunk_size=500, overlap=100)
        print(f"✓ Created {len(chunks)} chunks")
        
        if not chunks:
            return []
        
        # Encode all chunks
        print("Encoding chunks...")
        chunk_texts = [c[0] for c in chunks]
        chunk_embeddings = self.model.encode(
            chunk_texts,
            convert_to_tensor=True,
            show_progress_bar=True
        )
        
        # Search with each query
        all_matches = []
        
        for query_info in queries:
            sector = query_info['sector']
            query = query_info['query']
            
            print(f"\nSearching with {sector} query...")
            
            # Encode query
            query_embedding = self.model.encode(
                query,
                convert_to_tensor=True
            )
            
            # Compute cosine similarities
            similarities = torch.nn.functional.cosine_similarity(
                query_embedding.unsqueeze(0),
                chunk_embeddings
            )
            
            # Diagnostic output
            max_sim = similarities.max().item()
            mean_sim = similarities.mean().item()
            print(f"  Max similarity: {max_sim:.3f}, Mean: {mean_sim:.3f}")
            
            # Get top-k results
            top_indices = torch.argsort(similarities, descending=True)[:top_k]
            
            print(f"  Top-{top_k} scores: {[f'{similarities[i].item():.3f}' for i in top_indices[:5]]}")
            
            # Create matches for all top-k results
            for idx in top_indices:
                score = similarities[idx].item()
                chunk_text, start, end = chunks[idx]
                
                match = SemanticMatch(
                    chunk_id=f"semantic_{len(all_matches):04d}",
                    text=chunk_text,
                    similarity_score=score,
                    matched_query=query[:100] + "...",
                    sector=sector,
                    char_start=start,
                    char_end=end
                )
                
                all_matches.append(match)
            
            print(f"  Added {top_k} matches")
        
        # Remove duplicate chunks (same position, keep highest score)
        deduplicated = self._deduplicate_by_position(all_matches)
        
        print(f"\n✓ Total semantic matches (after dedup): {len(deduplicated)}")
        return deduplicated
    
    def _deduplicate_by_position(self, matches: List[SemanticMatch]) -> List[SemanticMatch]:
        """Remove duplicate matches at the same position, keeping highest score"""
        if not matches:
            return []
        
        # Group by position
        position_map = {}
        
        for match in matches:
            key = (match.char_start, match.char_end)
            
            if key not in position_map:
                position_map[key] = match
            else:
                # Keep the one with higher similarity score
                if match.similarity_score > position_map[key].similarity_score:
                    position_map[key] = match
        
        return list(position_map.values())


# Helper Functions
def process_pad_semantic_search(file_path: str, queries: List[Dict[str, str]], 
                                top_k: int = 10) -> Dict:
    """Process a PAD with semantic search"""
    
    print(f"\n{'='*80}")
    print(f"SEMANTIC SEARCH: {file_path.split('/')[-1]}")
    print(f"{'='*80}")
    
    # Load text
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    print(f"Document length: {len(text):,} characters")
    
    # Initialize searcher
    searcher = SemanticSearcher(model_name="all-MiniLM-L6-v2")
    
    # Search
    matches = searcher.search(text, queries, top_k=top_k)
    
    # Summary by sector
    sector_counts = {}
    for match in matches:
        sector_counts[match.sector] = sector_counts.get(match.sector, 0) + 1
    
    print(f"\n--- Matches by Sector ---")
    for sector, count in sorted(sector_counts.items()):
        print(f"  {sector}: {count} matches")
    
    return {
        'file_name': file_path.split('/')[-1],
        'project_id': file_path.split('_')[1] if '_' in file_path else 'unknown',
        'total_matches': len(matches),
        'sector_breakdown': sector_counts,
        'matches': matches
    }


def save_semantic_results(results: List[Dict], output_file: str = "semantic_search_results.json"):
    """Save semantic search results to JSON"""
    
    json_results = []
    
    for result in results:
        matches_dicts = []
        for match in result['matches']:
            matches_dicts.append({
                'chunk_id': match.chunk_id,
                'text': match.text,
                'similarity_score': match.similarity_score,
                'matched_query': match.matched_query,
                'sector': match.sector,
                'char_start': match.char_start,
                'char_end': match.char_end,
                'source': match.source
            })
        
        json_results.append({
            'file_name': result['file_name'],
            'project_id': result['project_id'],
            'total_matches': result['total_matches'],
            'sector_breakdown': result['sector_breakdown'],
            'matches': matches_dicts
        })
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Semantic search results saved to: {output_file}")
