# PDF Extractor Agent

A comprehensive PDF processing MCP Mesh service for the AI Interviewer system. Provides intelligent document analysis, text extraction, metadata parsing, and content processing capabilities.

## Features

### Core Capabilities
- **Text Extraction**: Advanced text extraction with PyMuPDF and pdfplumber
- **Metadata Extraction**: Comprehensive PDF metadata and document properties
- **Image Extraction**: Extract embedded images with format conversion
- **Table Extraction**: Intelligent table detection and structured data extraction
- **Document Validation**: Security and integrity validation
- **Comprehensive Processing**: All-in-one PDF processing workflow

### Advanced Features
- **MCP Mesh Integration**: Full dependency injection and service discovery
- **LLM Service Integration**: Enhanced analysis with optional LLM service dependency
- **Intelligent Caching**: Performance optimization for repeated operations
- **Security Validation**: File validation, size limits, and malicious content detection
- **Multiple Output Formats**: JSON, CSV, and structured data formats
- **Section Detection**: Resume/document structure analysis

## Package Structure

```
pdf_extractor_agent/
├── __init__.py              # Package initialization and exports
├── __main__.py              # Entry point for python -m execution
├── main.py                  # Main agent implementation with MCP tools
├── pyproject.toml           # Python packaging configuration
├── README.md                # This documentation
│
├── config/                  # Configuration management
│   ├── __init__.py
│   └── settings.py          # Settings classes and environment handling
│
├── tools/                   # Core PDF processing tools
│   ├── __init__.py
│   ├── text_extraction.py   # PyMuPDF + pdfplumber text extraction
│   ├── metadata_extraction.py # PDF metadata and properties
│   ├── image_extraction.py  # Image extraction and processing
│   └── table_extraction.py  # Table detection and extraction
│
└── utils/                   # Utility modules
    ├── __init__.py
    ├── validation.py        # PDF validation and security checks
    ├── formatting.py        # Text formatting and display helpers
    └── caching.py           # Caching system implementation
```

## Installation & Usage

### Dependencies
This service uses published **mcp-mesh 0.4.0** and requires:
- PyMuPDF (fitz) for fast PDF processing
- pdfplumber for complex layout handling
- Pillow for image processing
- python-magic for file type detection

### Development Installation
```bash
# From ai-interviewer root directory
pip install -e services/pdf_extractor_agent/
```

### Running the Agent
```bash
# Method 1: Python Module Execution (Recommended)
python -m pdf_extractor_agent

# Method 2: Direct Script Execution  
python services/pdf_extractor_agent/main.py
```

## MCP Tools Interface

### Primary Tools

#### `extract_text_from_pdf`
Extract text content with intelligent processing.
```python
result = await agent.extract_text_from_pdf(
    file_path="/path/to/document.pdf",
    extraction_method="auto"  # "auto", "pymupdf", "pdfplumber"
)
```

#### `extract_pdf_metadata`
Extract comprehensive metadata and document properties.
```python
result = await agent.extract_pdf_metadata(file_path="/path/to/document.pdf")
```

#### `extract_pdf_images`
Extract embedded images from PDF.
```python
result = await agent.extract_pdf_images(
    file_path="/path/to/document.pdf",
    save_images=False  # Save to disk or return base64
)
```

#### `extract_pdf_tables`
Extract tables with structure detection.
```python
result = await agent.extract_pdf_tables(
    file_path="/path/to/document.pdf",
    save_tables=False  # Save to disk or return structured data
)
```

#### `get_pdf_info`
Get PDF information without full processing.
```python
result = await agent.get_pdf_info(file_path="/path/to/document.pdf")
```

#### `process_pdf_comprehensive`
Perform all extractions in one operation.
```python
result = await agent.process_pdf_comprehensive(
    file_path="/path/to/document.pdf",
    extract_text=True,
    extract_metadata=True,
    extract_images=False,
    extract_tables=True
)
```

### Utility Tools

#### `get_agent_status`
Get agent status and configuration.

#### `clear_cache`
Clear processing cache.

## MCP Mesh Integration

### Service Configuration
- **Capability**: `"pdf_processing"`
- **Dependencies**: `["llm-service"]` (optional)
- **Port**: 9093 (configurable)
- **Timeout**: 300 seconds for large files
- **Retry**: 2 attempts with backoff

### Enhanced Proxy Features
- Custom headers for service identification
- Configurable timeouts for large document processing
- Automatic retry on transient failures
- Streaming support for large extractions

## Configuration

Configure via environment variables:

### Processing Limits
```bash
export PDF_MAX_FILE_SIZE_MB=50
export PDF_MAX_PAGES=100
export PDF_TIMEOUT_SECONDS=300
export PDF_MAX_IMAGE_COUNT=20
export PDF_MAX_IMAGE_SIZE_MB=10
```

### Security Settings
```bash
export PDF_ALLOW_ENCRYPTED=false
export PDF_SANITIZE_METADATA=true
export PDF_VALIDATE_HEADERS=true
export PDF_QUARANTINE_SUSPICIOUS=true
```

### Extraction Options
```bash
export PDF_PRESERVE_FORMATTING=true
export PDF_EXTRACT_IMAGES=true
export PDF_EXTRACT_TABLES=true
export PDF_IMAGE_FORMAT=PNG
export PDF_TABLE_FORMAT=json
```

### Cache Configuration
```bash
export PDF_CACHE_ENABLED=true
export PDF_CACHE_TTL_SECONDS=3600
export PDF_CACHE_MAX_ENTRIES=1000
```

## Integration with AI Interviewer

The PDF extractor integrates with the AI Interviewer system:

1. **Resume Upload**: Process uploaded PDF resumes
2. **Content Analysis**: Extract structured data for interview preparation
3. **Session Storage**: Cache results in Redis for quick access
4. **LLM Integration**: Enhanced analysis with LLM service when available

### Usage Flow
```
User Upload → FastAPI Backend → PDF Extractor (via MCP Mesh) → Structured Data → Interview Questions
```

## Security Considerations

- File validation and size limits
- MIME type verification
- Malicious content detection
- Metadata sanitization
- Secure temporary file handling
- Resource usage limits

## Performance Features

- Intelligent caching by file hash
- Multiple extraction methods with fallback
- Memory-efficient processing for large files
- Parallel page processing
- Configurable resource limits

## Development

### Testing
```bash
pytest tests/
```

### Code Quality
```bash
black pdf_extractor_agent/
isort pdf_extractor_agent/
flake8 pdf_extractor_agent/
mypy pdf_extractor_agent/
```

## License

MIT License - Part of the AI Interviewer project.