# Quick Start Guide - RI Pilot Project

## Installation

```bash
# Install Python dependencies
pip install spacy nltk sentence-transformers torch boto3 PyPDF2 --break-system-packages

# Download models
python -m spacy download en_core_web_sm

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('wordnet'); nltk.download('averaged_perceptron_tagger')"
```

## Configuration

1. Edit `config.py` and update your AWS settings:

```python
AWS_CONFIG = {
    "s3_bucket": "your-bucket-name",
    "s3_input_prefix": "your-input-prefix",
    "s3_output_prefix": "your-output-prefix",
    ...
}
```

## Running the Pipeline

### Option 1: Run All Phases Sequentially

```bash
# Replace with your actual PAD files
PAD_FILES="pad_file1.txt pad_file2.txt"

# Phase 1: Keyword Search
python run_keyword_search.py $PAD_FILES

# Phase 2: Semantic Search
python run_semantic_search.py $PAD_FILES

# Phase 3: Deduplication
python run_deduplication.py

# Phase 4: Bedrock Classification
python run_bedrock_classification.py

# Phase 5: Results Processing
python run_results_processing.py

# Phase 6: Activity Classification (optional)
python run_activity_classification.py
```

### Option 2: Run Individual Phases

Each phase can be run independently if you have the required input files:

```bash
# Phase 1 only (creates keyword_search_results.json)
python run_keyword_search.py path/to/your/pad.txt

# Phase 2 only (creates semantic_search_results.json)
python run_semantic_search.py path/to/your/pad.txt

# Phase 3 only (requires Phase 1 & 2 outputs)
python run_deduplication.py

# Phase 4 only (requires Phase 3 output)
python run_bedrock_classification.py

# Phase 5 only (requires Phase 3 & 4 outputs)
python run_results_processing.py
```

## Output Files

After running all phases, you'll have:

1. `keyword_search_results.json` - Keyword matches
2. `semantic_search_results.json` - Semantic matches
3. `combined_deduplicated_results.json` - Deduplicated results
4. `bedrock_classifications.json` - Classification results
5. `final_enriched_results.json` - Complete results
6. `final_enriched_results_positive_only.json` - Positive RI interventions only
7. `final_ri_classifications.json` - Positive interventions with activity categories

## Typical Workflow

```bash
# 1. Prepare your PAD text files
ls *.txt

# 2. Run keyword + semantic search on your files
python run_keyword_search.py *.txt
python run_semantic_search.py *.txt

# 3. Deduplicate results
python run_deduplication.py

# 4. Classify with Bedrock (requires AWS credentials)
python run_bedrock_classification.py

# 5. Generate final results
python run_results_processing.py

# 6. Check your results
cat final_enriched_results_positive_only.json | jq '.[] | .text' | head -20
```

## Customization

### Add/Modify Keywords

Edit `config.py` → `RI_KEYWORDS` dictionary

### Add/Modify Semantic Queries

Edit `config.py` → `SEMANTIC_QUERIES` list

### Adjust Parameters

Edit `config.py` → `SEARCH_PARAMS`:
- `keyword_context_sentences`: 3 (sentences before/after)
- `semantic_chunk_size`: 500 (characters)
- `semantic_overlap`: 100 (characters)
- `dedup_overlap_threshold`: 0.5 (50% overlap)

## Troubleshooting

### Missing Input Files

```
❌ Error: File not found: keyword_search_results.json
```
→ Run `python run_keyword_search.py` first

### AWS Credentials

```
❌ Error: Unable to locate credentials
```
→ Configure AWS CLI: `aws configure`

### Module Not Found

```
ModuleNotFoundError: No module named 'spacy'
```
→ Install dependencies: `pip install spacy --break-system-packages`

## Performance Tips

- **Batch size**: Default is 5 chunks per Bedrock request. Adjust in `config.py` if needed
- **Top-K**: Default is top-10 semantic results per query. Adjust in scripts if needed
- **Parallel processing**: For multiple PADs, run keyword/semantic phases separately then combine

## Support

See `README.md` for detailed documentation.
