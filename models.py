"""
Data models for RI Pilot Project
Contains all dataclass definitions used across the pipeline
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class KeywordMatch:
    """Store information about a keyword match"""
    chunk_id: str
    text: str
    matched_keywords: List[str]
    char_start: int
    char_end: int
    source: str = "keyword_search"
    section_name: str = ""
    page_number: int = 0


@dataclass
class SemanticMatch:
    """Store information about a semantic search match"""
    chunk_id: str
    text: str
    similarity_score: float
    matched_query: str
    sector: str
    char_start: int
    char_end: int
    source: str = "semantic_search"


@dataclass
class CombinedMatch:
    """Unified match structure after deduplication"""
    chunk_id: str
    text: str
    char_start: int
    char_end: int
    sources: List[str]  # ["keyword_search", "semantic_search"] or just one
    
    # Keyword-specific
    matched_keywords: List[str] = field(default_factory=list)
    
    # Semantic-specific
    similarity_score: float = 0.0
    matched_query: str = ""
    sector: str = ""
    
    # Metadata
    found_by: str = ""  # "keyword_only", "semantic_only", "both"
