"""
Keyword Search Module for RI Pilot Project
Handles keyword-based search with lemmatization and context extraction
"""

import re
import json
from typing import List, Dict, Tuple
from nltk import word_tokenize, sent_tokenize
from nltk.stem import WordNetLemmatizer

from models import KeywordMatch


class KeywordSearcher:
    """Handles keyword-based search with lemmatization"""
    
    def __init__(self, keywords: List[str]):
        self.keywords = keywords
        self.lemmatizer = WordNetLemmatizer()
        self.lemmatized_keywords = self._create_keyword_patterns()
    
    def _lemmatize_word(self, word: str) -> str:
        """Lemmatize a single word"""
        word = word.lower().strip()
        # Try as noun, verb, adjective
        lemmas = {
            self.lemmatizer.lemmatize(word, pos='n'),
            self.lemmatizer.lemmatize(word, pos='v'),
            self.lemmatizer.lemmatize(word, pos='a'),
        }
        # Return the shortest lemma (usually most canonical)
        return min(lemmas, key=len)
    
    def _create_keyword_patterns(self) -> Dict[str, List[str]]:
        """Create lemmatized patterns for each keyword"""
        patterns = {}
        
        for keyword in self.keywords:
            # Handle multi-word phrases
            words = keyword.lower().split()
            
            if len(words) == 1:
                # Single word - create lemma
                lemma = self._lemmatize_word(words[0])
                if lemma not in patterns:
                    patterns[lemma] = []
                patterns[lemma].append(keyword)
            else:
                # Multi-word phrase - lemmatize each word
                lemmas = [self._lemmatize_word(w) for w in words]
                pattern_key = " ".join(lemmas)
                if pattern_key not in patterns:
                    patterns[pattern_key] = []
                patterns[pattern_key].append(keyword)
        
        return patterns
    
    def _find_keyword_positions(self, text: str) -> List[Tuple[int, int, str]]:
        """Find all positions where keywords appear (with lemmatization)
        Returns: List of (start_pos, end_pos, single_keyword)
        """
        text_lower = text.lower()
        matches = []
        
        for pattern, original_keywords in self.lemmatized_keywords.items():
            pattern_words = pattern.split()
            
            # Use just the FIRST original keyword (they're lemma equivalents anyway)
            representative_keyword = original_keywords[0]
            
            if len(pattern_words) == 1:
                # Single word search with lemmatization
                words = word_tokenize(text_lower)
                
                for i, word in enumerate(words):
                    word_lemma = self._lemmatize_word(word)
                    if word_lemma == pattern:
                        # Find actual position in original text
                        start = text_lower.find(word, sum(len(w) + 1 for w in words[:i]))
                        if start != -1:
                            end = start + len(word)
                            matches.append((start, end, representative_keyword))
            else:
                # Multi-word phrase
                regex_pattern = r'\b' + r'\s+'.join(
                    [re.escape(w) for w in pattern_words]
                ) + r'\b'
                
                for match in re.finditer(regex_pattern, text_lower):
                    matches.append((match.start(), match.end(), representative_keyword))
        
        return matches
    
    def _extract_context(self, text: str, match_start: int, match_end: int) -> Tuple[str, int, int]:
        """Extract context around a match (paragraph or sentence-based)"""
        
        # First try: Extract by paragraph
        paragraphs = text.split('\n\n')
        current_pos = 0
        
        for para in paragraphs:
            para_end = current_pos + len(para)
            
            if current_pos <= match_start <= para_end:
                para_clean = para.strip()
                
                # Check character limits
                if 200 <= len(para_clean) <= 1000:
                    return para_clean, current_pos, para_end
                elif len(para_clean) < 200:
                    # Too short - expand
                    return self._expand_context(text, current_pos, para_end)
                else:
                    # Too long - use sentence-based extraction
                    return self._extract_by_sentences(text, match_start)
            
            current_pos = para_end + 2  # +2 for \n\n
        
        # Fallback: sentence-based extraction
        return self._extract_by_sentences(text, match_start)
    
    def _extract_by_sentences(self, text: str, match_pos: int, 
                              before: int = 3, after: int = 3) -> Tuple[str, int, int]:
        """Extract context using sentence boundaries"""
        sentences = sent_tokenize(text)
        
        # Find sentence containing match
        current_pos = 0
        target_idx = None
        
        for idx, sent in enumerate(sentences):
            sent_end = current_pos + len(sent)
            if current_pos <= match_pos <= sent_end:
                target_idx = idx
                break
            current_pos = sent_end + 1
        
        if target_idx is None:
            # Fallback: fixed window
            start = max(0, match_pos - 300)
            end = min(len(text), match_pos + 300)
            return text[start:end], start, end
        
        # Get surrounding sentences
        start_idx = max(0, target_idx - before)
        end_idx = min(len(sentences), target_idx + after + 1)
        
        context_sents = sentences[start_idx:end_idx]
        context_text = " ".join(context_sents)
        
        # Calculate character positions (approximate)
        char_start = sum(len(s) + 1 for s in sentences[:start_idx])
        char_end = char_start + len(context_text)
        
        # Ensure within character limits
        if len(context_text) < 200:
            return self._expand_context(text, char_start, char_end)
        elif len(context_text) > 1000:
            match_offset = match_pos - char_start
            half = 500
            truncated = context_text[max(0, match_offset - half):match_offset + half]
            return truncated, char_start, char_start + len(truncated)
        
        return context_text, char_start, char_end
    
    def _expand_context(self, text: str, start: int, end: int) -> Tuple[str, int, int]:
        """Expand context to meet minimum 200 character requirement"""
        while (end - start) < 200 and (start > 0 or end < len(text)):
            if start > 0:
                start = max(0, start - 100)
            if end < len(text):
                end = min(len(text), end + 100)
        
        expanded_text = text[start:end].strip()
        return expanded_text, start, start + len(expanded_text)
    
    def search(self, text: str, section_name: str = "", 
               page_number: int = 0) -> List[KeywordMatch]:
        """Search for all keyword matches in text"""
        
        # Find all keyword positions
        keyword_positions = self._find_keyword_positions(text)
        
        if not keyword_positions:
            return []
        
        # Group keywords by position
        position_keywords = {}
        
        for start, end, keyword in keyword_positions:
            key = (start, end)
            if key not in position_keywords:
                position_keywords[key] = []
            position_keywords[key].append(keyword)
        
        # Extract context for each unique position
        matches = []
        seen_positions = set()
        
        for (start, end), keywords in position_keywords.items():
            # Deduplicate keywords at this position
            unique_keywords = list(set(keywords))
            
            # Skip if overlapping
            if start in seen_positions:
                continue
            seen_positions.add(start)
            
            # Extract context
            context_text, context_start, context_end = self._extract_context(text, start, end)
            
            # Create match object
            match = KeywordMatch(
                chunk_id=f"keyword_{len(matches):04d}",
                text=context_text,
                matched_keywords=unique_keywords,
                char_start=context_start,
                char_end=context_end,
                section_name=section_name,
                page_number=page_number
            )
            
            matches.append(match)
        
        # Merge overlapping matches
        merged = self._merge_overlapping(matches)
        
        return merged
    
    def _merge_overlapping(self, matches: List[KeywordMatch]) -> List[KeywordMatch]:
        """Merge matches with overlapping text positions"""
        if not matches:
            return []
        
        # Sort by start position
        sorted_matches = sorted(matches, key=lambda x: x.char_start)
        merged = [sorted_matches[0]]
        
        for current in sorted_matches[1:]:
            last = merged[-1]
            
            # Calculate overlap
            overlap_start = max(last.char_start, current.char_start)
            overlap_end = min(last.char_end, current.char_end)
            
            if overlap_start < overlap_end:
                overlap_ratio = (overlap_end - overlap_start) / (last.char_end - last.char_start)
                
                if overlap_ratio > 0.5:
                    # Merge
                    all_keywords = last.matched_keywords + current.matched_keywords
                    last.matched_keywords = list(set(all_keywords))
                    last.char_end = max(last.char_end, current.char_end)
                    if len(current.text) > len(last.text):
                        last.text = current.text
                    continue
            
            merged.append(current)
        
        return merged


# Helper Functions
def load_pad_text(file_path: str) -> str:
    """Load text from PAD file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def process_pad(file_path: str, searcher: KeywordSearcher) -> Dict:
    """Process a single PAD document"""
    print(f"\n{'='*80}")
    print(f"Processing: {file_path.split('/')[-1]}")
    print(f"{'='*80}")
    
    # Load text
    text = load_pad_text(file_path)
    print(f"Document length: {len(text):,} characters")
    
    # Search for keywords
    matches = searcher.search(text)
    print(f"✓ Found {len(matches)} keyword matches")
    
    # Count keyword occurrences
    keyword_counts = {}
    for match in matches:
        for kw in match.matched_keywords:
            keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
    
    unique_keywords = set(keyword_counts.keys())
    print(f"✓ Unique keywords matched: {len(unique_keywords)}")
    print(f"\nTop matched keywords:")
    
    # Show top 10
    top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    for kw, count in top_keywords:
        print(f"  - {kw}: {count} matches")
    
    # Return results
    return {
        'file_path': file_path,
        'file_name': file_path.split('/')[-1],
        'project_id': file_path.split('_')[1] if '_' in file_path else 'unknown',
        'total_matches': len(matches),
        'unique_keywords': len(unique_keywords),
        'matches': matches,
        'keyword_counts': keyword_counts
    }


def display_sample_matches(matches: List[KeywordMatch], num_samples: int = 3):
    """Display sample matches for review"""
    print(f"\n--- Sample Matches (showing {min(num_samples, len(matches))} of {len(matches)}) ---\n")
    
    for i, match in enumerate(matches[:num_samples]):
        print(f"Match #{i+1}:")
        print(f"  Chunk ID: {match.chunk_id}")
        print(f"  Keywords: {', '.join(match.matched_keywords[:5])}")
        print(f"  Position: {match.char_start}-{match.char_end}")
        print(f"  Text preview:")
        preview = match.text[:300] + "..." if len(match.text) > 300 else match.text
        print(f"    {preview}")
        print()


def save_results(results: List[Dict], output_file: str = "keyword_search_results.json"):
    """Save results to JSON file"""
    # Convert KeywordMatch objects to dicts for JSON serialization
    json_results = []
    
    for result in results:
        matches_dicts = []
        for match in result['matches']:
            matches_dicts.append({
                'chunk_id': match.chunk_id,
                'text': match.text,
                'matched_keywords': match.matched_keywords,
                'char_start': match.char_start,
                'char_end': match.char_end,
                'source': match.source
            })
        
        json_results.append({
            'file_name': result['file_name'],
            'project_id': result['project_id'],
            'total_matches': result['total_matches'],
            'unique_keywords': result['unique_keywords'],
            'keyword_counts': result['keyword_counts'],
            'matches': matches_dicts
        })
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Results saved to: {output_file}")
