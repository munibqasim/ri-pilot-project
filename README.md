# RI Pilot Project - Resilient Infrastructure Extraction Pipeline

Multi-phase AI pipeline for extracting resilient infrastructure interventions from World Bank Project Appraisal Documents (PADs).

## Project Structure

```
.
├── config.py                          # Configuration: keywords, queries, AWS settings
├── models.py                          # Data models (KeywordMatch, SemanticMatch, CombinedMatch)
│
├── keyword_search.py                  # Phase 1: Keyword-based search module
├── semantic_search.py                 # Phase 2: Semantic search module  
├── deduplication.py                   # Phase 3: Cross-store deduplication module
├── bedrock_classifier.py              # Phase 4: AWS Bedrock batch classification
│
├── run_keyword_search.py              # ► Run Phase 1
├── run_semantic_search.py             # ► Run Phase 2
├── run_deduplication.py               # ► Run Phase 3
├── run_bedrock_classification.py      # ► Run Phase 4
└── run_results_processing.py          # ► Run Phase 5 (Final enrichment)
```

## Pipeline Overview

### Phase 1: Keyword Search
- Uses comprehensive RI keyword taxonomy (energy, transport, water, etc.)
- Lemmatization for robust matching
- Context extraction (200-1000 characters)
- **Output**: `keyword_search_results.json`

### Phase 2: Semantic Search
- Sentence transformers (`all-MiniLM-L6-v2`)
- 8 sector-specific queries
- Top-10 results per query
- **Output**: `semantic_search_results.json`

### Phase 3: Deduplication
- Combines keyword + semantic matches
- Removes overlaps (>50% threshold)
- Tracks discovery method (keyword/semantic/both)
- **Output**: `combined_deduplicated_results.json`

### Phase 4: Bedrock Classification
- AWS Bedrock batch inference
- Claude Sonnet 4 for classification
- POSITIVE/NEGATIVE with confidence levels
- **Output**: `bedrock_classifications.json`

### Phase 5: Results Processing
- Enriches classifications with original chunk data
- Filters positive results
- **Output**: `final_enriched_results.json` & `final_enriched_results_positive_only.json`

## Setup

### 1. Install Dependencies

```bash
pip install --break-system-packages \
    spacy \
    nltk \
    sentence-transformers \
    torch \
    boto3 \
    PyPDF2
```

### 2. Download NLTK Data

```python
import nltk
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')
```

### 3. Download spaCy Model

```bash
python -m spacy download en_core_web_sm
```

### 4. Configure AWS

Update `config.py` with your S3 bucket and prefixes:

```python
AWS_CONFIG = {
    "region": "us-east-1",
    "s3_bucket": "your-bucket-name",
    "s3_input_prefix": "your-input-prefix",
    "s3_output_prefix": "your-output-prefix",
    ...
}
```

## Usage

### Run Complete Pipeline

```bash
# Phase 1: Keyword Search
python run_keyword_search.py pad_file1.txt pad_file2.txt

# Phase 2: Semantic Search  
python run_semantic_search.py pad_file1.txt pad_file2.txt

# Phase 3: Deduplication
python run_deduplication.py

# Phase 4: Bedrock Classification (requires AWS credentials)
python run_bedrock_classification.py

# Phase 5: Results Processing
python run_results_processing.py
```

### Run Individual Phases

Each script can be run independently if you already have the required input files:

```bash
# Run just keyword search
python run_keyword_search.py /path/to/your/pad.txt

# Run just semantic search
python run_semantic_search.py /path/to/your/pad.txt

# Deduplication requires keyword_search_results.json + semantic_search_results.json
python run_deduplication.py

# Classification requires combined_deduplicated_results.json
python run_bedrock_classification.py

# Processing requires combined_deduplicated_results.json + bedrock_classifications.json
python run_results_processing.py
```

## Configuration

### Customize Keywords

Edit `config.py` → `RI_KEYWORDS` dictionary to add/modify keywords by sector.

### Customize Semantic Queries

Edit `config.py` → `SEMANTIC_QUERIES` list to add/modify search queries.

### Adjust Search Parameters

Edit `config.py` → `SEARCH_PARAMS`:
- `keyword_context_sentences`: Context window for keyword matches
- `semantic_chunk_size`: Chunk size for semantic search
- `semantic_overlap`: Overlap between chunks
- `dedup_overlap_threshold`: Threshold for considering duplicates

## Core Methodology

### Keyword Search
- **Lemmatization**: Matches word variations (flood, flooding, floods)
- **Multi-word phrases**: Handles "climate-resilient pavement"
- **Context extraction**: Extracts surrounding sentences (3 before + 3 after)
- **Overlap merging**: Combines overlapping matches (>50%)

### Semantic Search
- **Chunking**: 500-character chunks with 100-character overlap
- **Cosine similarity**: Finds semantically similar content
- **Top-K selection**: Takes top 10 results per query
- **Position deduplication**: Keeps highest-scoring match per position

### Deduplication
- **Overlap calculation**: Character-level overlap between spans
- **Smart merging**: Combines keyword + semantic info when overlapping
- **Source tracking**: Maintains provenance (keyword/semantic/both)

### Bedrock Classification
- **Batch processing**: 5 chunks per batch request
- **Few-shot prompting**: 3 examples (1 positive, 2 negative)
- **Structured output**: JSON with classification, confidence, reasoning
- **Definition-based**: Uses official WBG resilient infrastructure definition

## File Outputs

All output files are saved to the working directory:

- `keyword_search_results.json` - Raw keyword matches
- `semantic_search_results.json` - Raw semantic matches
- `combined_deduplicated_results.json` - Deduplicated combined results
- `bedrock_classifications.json` - Classification results from Bedrock
- `final_enriched_results.json` - All results with classifications
- `final_enriched_results_positive_only.json` - Filtered positive interventions

## AWS Bedrock Requirements

- AWS account with Bedrock access
- IAM role: `BedrockBatchInferenceRole`
- S3 bucket for input/output
- Model access: Claude Sonnet 4 (`anthropic.claude-sonnet-4-20250514`)

## Notes

- **No core methodology changes**: All original logic is preserved
- **Modular design**: Each phase can be run independently
- **Progress tracking**: Verbose console output at each step
- **Error handling**: Graceful failures with informative messages
- **JSON serialization**: All results are JSON-serializable for easy processing

## Support

For questions or issues, refer to the original notebook or contact the project team.
