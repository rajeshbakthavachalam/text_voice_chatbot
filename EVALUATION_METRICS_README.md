# 📈 Evaluation Metrics Documentation

This document describes the comprehensive evaluation metrics system added to the knowledge base chatbot.

## 🎯 Overview

The evaluation metrics system provides quantitative assessment of the knowledge base search performance, helping you understand how well the system answers questions and retrieves relevant information.

## 📊 Metrics Included

### 1. **Answer Relevance**
- **Description**: Measures how similar the actual answer is to the expected answer
- **Calculation**: Jaccard similarity between word sets of expected and actual answers
- **Range**: 0.0 (no similarity) to 1.0 (perfect match)
- **Formula**: `|expected_words ∩ actual_words| / |expected_words ∪ actual_words|`

### 2. **Keyword Coverage**
- **Description**: Measures how many keywords from the expected answer appear in the actual answer
- **Calculation**: Ratio of common keywords to total expected keywords
- **Range**: 0.0 (no keywords covered) to 1.0 (all keywords covered)
- **Formula**: `|expected_keywords ∩ actual_keywords| / |expected_keywords|`

### 3. **Source Accuracy Metrics**
- **Source Precision**: Ratio of correctly identified sources to total returned sources
- **Source Recall**: Ratio of correctly identified sources to total expected sources
- **Source F1-Score**: Harmonic mean of precision and recall
- **Source Accuracy**: Overall accuracy of source identification

### 4. **Length Ratio**
- **Description**: Compares the length of actual answer to expected answer
- **Calculation**: `actual_word_count / expected_word_count`
- **Range**: 0.0+ (actual answer can be shorter or longer)
- **Interpretation**: 
  - < 1.0: Actual answer is shorter than expected
  - = 1.0: Same length
  - > 1.0: Actual answer is longer than expected

### 5. **Confidence Score**
- **Description**: System's confidence in the answer (from ChromaDB)
- **Range**: 0.0 (low confidence) to 1.0 (high confidence)

## 🚀 How to Use

### Method 1: Streamlit App (Recommended)

1. **Run the app**:
   ```bash
   streamlit run knowledge_base_app_tabs.py
   ```

2. **Navigate to Evaluation Tab**:
   - Go to the "📈 Evaluation Metrics" tab
   - Use the sidebar to load sample queries or create custom ones
   - Click "▶️ Run Evaluation" to start the evaluation

3. **View Results**:
   - Interactive charts and metrics
   - Detailed results table
   - Download results as CSV
   - Compare single vs multi-PDF performance

### Method 2: Command Line

1. **Run the demo script**:
   ```bash
   python evaluation_demo.py
   ```

2. **View console output** with detailed metrics

## 📋 Creating Test Queries

### Sample Queries (Auto-generated)
The system provides sample queries for insurance-related documents:
- "What are the insurance benefits?"
- "What is the coverage limit?"
- "What expenses are not covered?"

### Custom Queries
You can create custom test queries with:
- **Query**: The question to ask
- **Expected Answer**: Ground truth answer
- **Expected Sources**: Expected PDF sources (optional)
- **PDF Name**: Specific PDF for single-PDF search (optional)

## 📊 Understanding Results

### Overall Metrics
- **Total Queries**: Number of test queries evaluated
- **Single PDF Queries**: Queries tested on specific PDFs
- **Multi PDF Queries**: Queries tested across all PDFs

### Performance Indicators
- **High Answer Relevance** (>0.7): System provides relevant answers
- **High Keyword Coverage** (>0.8): System covers most expected keywords
- **Balanced Length Ratio** (0.8-1.2): Answer length is appropriate
- **High Confidence** (>0.8): System is confident in answers

### Source Accuracy
- **High Precision** (>0.8): Most returned sources are correct
- **High Recall** (>0.8): System finds most expected sources
- **High F1-Score** (>0.8): Good balance of precision and recall

## 📈 Visualization Features

### Charts Available
1. **Answer Relevance Distribution**: Histogram showing relevance scores
2. **Keyword Coverage Distribution**: Histogram showing coverage scores
3. **Search Type Comparison**: Box plot comparing single vs multi-PDF performance

### Interactive Features
- Hover over charts for detailed values
- Zoom and pan capabilities
- Download charts as images

## 💾 Data Management

### Saving Results
- Results are automatically saved as JSON files
- Timestamped filenames: `evaluation_results_YYYYMMDD_HHMMSS.json`
- Stored in the `chroma_db` directory

### Loading Previous Results
- Access evaluation history from the sidebar
- Compare results across different runs
- Track performance improvements over time

### Export Options
- **CSV Export**: Download detailed results as spreadsheet
- **JSON Export**: Full results with metadata
- **Charts**: Interactive visualizations

## 🔧 Advanced Usage

### Custom Evaluation Scripts
```python
from knowledge_base_manager import KnowledgeBaseManager

# Initialize manager
kb_manager = KnowledgeBaseManager()

# Create custom test queries
test_queries = [
    {
        'query': 'Your question here',
        'expected_answer': 'Expected answer here',
        'expected_sources': ['source1.pdf', 'source2.pdf'],
        'pdf_name': 'specific.pdf'  # Optional
    }
]

# Run evaluation
results = kb_manager.evaluate_search_performance(test_queries)

# Access results
summary = results['summary']
detailed = results['detailed_results']

# Save results
filename = kb_manager.save_evaluation_results(results)
```

### Batch Evaluation
```python
# Evaluate multiple query sets
query_sets = [
    kb_manager.create_sample_test_queries(),
    your_custom_queries,
    another_query_set
]

for i, queries in enumerate(query_sets):
    results = kb_manager.evaluate_search_performance(queries)
    kb_manager.save_evaluation_results(results, f"batch_{i}.json")
```

## 🎯 Best Practices

### 1. **Diverse Test Queries**
- Include different question types
- Test both simple and complex queries
- Mix single-PDF and multi-PDF queries

### 2. **Realistic Expected Answers**
- Use actual content from your PDFs
- Include key terminology and concepts
- Match the expected level of detail

### 3. **Regular Evaluation**
- Run evaluations after system changes
- Track performance over time
- Use results to guide improvements

### 4. **Interpret Results Contextually**
- Consider your specific use case
- Balance accuracy vs. completeness
- Focus on metrics most relevant to your needs

## 🐛 Troubleshooting

### Common Issues
1. **No PDFs Indexed**: Index PDFs first using the sidebar
2. **Low Relevance Scores**: Check if expected answers match actual content
3. **Missing Sources**: Ensure expected sources are correctly specified
4. **Evaluation Errors**: Check that all required fields are provided

### Performance Tips
- Use smaller test sets for quick evaluation
- Save results for later comparison
- Use the interactive charts for detailed analysis

## 📚 Technical Details

### Dependencies
- `numpy`: Statistical calculations
- `pandas`: Data manipulation
- `plotly`: Interactive visualizations
- `streamlit`: Web interface

### File Structure
```
chroma_db/
├── evaluation_results_*.json    # Evaluation results
├── knowledge_base_index.json    # PDF index
└── [collection files]           # ChromaDB collections
```

### Metrics Formulas
- **Jaccard Similarity**: `|A ∩ B| / |A ∪ B|`
- **Precision**: `|relevant ∩ retrieved| / |retrieved|`
- **Recall**: `|relevant ∩ retrieved| / |relevant|`
- **F1-Score**: `2 × (precision × recall) / (precision + recall)`

## 🎉 Conclusion

The evaluation metrics system provides comprehensive insights into your knowledge base performance. Use these metrics to:

- **Monitor Performance**: Track how well your system answers questions
- **Identify Improvements**: Find areas for enhancement
- **Compare Configurations**: Test different settings and approaches
- **Validate Changes**: Ensure updates improve performance

For questions or issues, refer to the main application documentation or run the evaluation demo script for examples. 