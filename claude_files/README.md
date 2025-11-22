# Document Processing Pipeline

Async document processing pipeline with real-time progress tracking for patent analysis.

## Features

- ✅ **Async Processing**: Non-blocking document upload and processing
- ✅ **Real-time Progress**: WebSocket-based progress updates
- ✅ **Modular Architecture**: Clean separation of concerns
- ✅ **Patent-Optimized**: Uses PatentSBERTa for embeddings
- ✅ **Structured Extraction**: Unstructured.io for intelligent parsing
- ✅ **Semantic Chunking**: LlamaIndex for context-aware chunking
- ✅ **Domain Classification**: Automatic technical domain detection

## Architecture

```
preprocessing/
├── extractors/       # Document content extraction
├── chunkers/         # Semantic text chunking
├── embedders/        # Embedding generation
├── classifiers/      # Domain classification
└── pipeline.py       # Main orchestration

api/
└── documents/
    ├── routes.py     # FastAPI endpoints
    ├── services.py   # Business logic
    ├── schemas.py    # Pydantic models
    └── websocket.py  # WebSocket manager
```

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install system dependencies (for Unstructured)
# Ubuntu/Debian:
sudo apt-get install poppler-utils tesseract-ocr

# macOS:
brew install poppler tesseract
```

## Usage

### 1. Start FastAPI Server

```python
from fastapi import FastAPI
from api.documents.routes import router

app = FastAPI()
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 2. Upload Document (Frontend)

```javascript
// Upload file
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch(
    '/api/documents/upload?project_id=YOUR_PROJECT_ID&is_primary=true',
    { method: 'POST', body: formData }
);

const document = await response.json();
console.log('Document ID:', document.id);
```

### 3. Track Progress (WebSocket)

```javascript
const ws = new WebSocket(`ws://localhost:8000/api/documents/ws/${document.id}`);

ws.onmessage = (event) => {
    const { stage, progress, error } = JSON.parse(event.data);
    
    console.log(`${stage}: ${progress}%`);
    
    if (stage === 'complete') {
        console.log('Processing complete!');
        ws.close();
    }
};
```

### 4. Retrieve Chunks

```javascript
const response = await fetch(`/api/documents/${document.id}/chunks`);
const chunks = await response.json();
```

## Progress Stages

The pipeline sends progress updates through WebSocket:

| Stage | Progress | Description |
|-------|----------|-------------|
| `extracting` | 20% | Extracting content with Unstructured.io |
| `classifying` | 35% | Classifying technical domain |
| `chunking` | 50% | Creating semantic chunks |
| `embedding` | 70% | Generating embeddings (slowest step) |
| `storing` | 85% | Saving to database |
| `complete` | 100% | Processing finished |
| `failed` | 0% | Error occurred |

## Processing Time

For a 10-page PDF (~5,000 words):
- **Best case** (GPU): ~7-12 seconds
- **Typical** (CPU): ~15-25 seconds
- **With OCR**: ~30-45 seconds

## Database Schema

### Document Table
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL,
    filename VARCHAR(255),
    file_type VARCHAR(50),
    processing_status VARCHAR(50),
    metadata JSONB,
    uploaded_at TIMESTAMP,
    processed_at TIMESTAMP,
    deleted_at TIMESTAMP
);
```

### DocumentChunk Table
```sql
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_text TEXT,
    chunk_index INTEGER,
    embedding VECTOR(768),  -- pgvector
    section_type VARCHAR(50),
    token_count INTEGER,
    metadata JSONB
);
```

## Configuration

```python
# src/config/settings.py
class Settings:
    STORAGE_PATH = "/tmp/documents"
    EMBEDDING_MODEL = "AI-Growth-Lab/PatentSBERTa"
    EMBEDDING_DEVICE = "cpu"  # or "cuda" for GPU
    CHUNK_SIZE = 512
    CHUNK_OVERLAP = 50
```

## API Endpoints

### POST /api/documents/upload
Upload and queue document for processing.

**Parameters:**
- `project_id` (query): Project UUID
- `is_primary` (query): Whether primary disclosure
- `file` (form): Document file

**Returns:** Document object with ID

### WebSocket /api/documents/ws/{document_id}
Real-time processing progress updates.

**Messages:**
```json
{
    "stage": "embedding",
    "progress": 70,
    "error": null
}
```

### GET /api/documents/{document_id}
Get document details.

### GET /api/documents/{document_id}/chunks
Get document chunks.

**Parameters:**
- `limit` (query): Max chunks to return

### DELETE /api/documents/{document_id}
Soft delete document.

## Testing

```python
import asyncio
from preprocessing.pipeline import DocumentPreprocessingPipeline

async def test_pipeline():
    pipeline = DocumentPreprocessingPipeline(db_session)
    
    async def progress_callback(data):
        print(f"{data['stage']}: {data['progress']}%")
    
    result = await pipeline.process_document(
        document_id="...",
        file_path="test.pdf",
        project_id="...",
        progress_callback=progress_callback
    )
    
    print(f"Created {result['chunks_created']} chunks")

asyncio.run(test_pipeline())
```

## Performance Optimization

### Use GPU for Embeddings
```python
# Change device to 'cuda'
embedder = PatentEmbedder(device='cuda')
# 5-10x faster embedding generation
```

### Batch Processing
```python
# Process multiple documents in parallel
tasks = [
    pipeline.process_document(doc_id, path, proj_id)
    for doc_id, path, proj_id in documents
]
results = await asyncio.gather(*tasks)
```

## Troubleshooting

### Slow Processing
- Use GPU for embeddings (5-10x faster)
- Reduce chunk_size if memory limited
- Check for slow disk I/O

### WebSocket Connection Issues
- Ensure CORS is configured
- Check firewall settings
- Verify WebSocket URL scheme (ws:// or wss://)

### Import Errors
```bash
# Make sure all dependencies are installed
pip install -r requirements.txt

# Install system dependencies
sudo apt-get install poppler-utils tesseract-ocr
```

## License

MIT
