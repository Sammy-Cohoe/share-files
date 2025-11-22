# Document Processing Pipeline - Architecture Overview

## Component Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │ File Upload  │───▶│  WebSocket   │◀───│  Progress    │     │
│  │   Component  │    │  Connection  │    │   Display    │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
└────────┬──────────────────────┬──────────────────────┬─────────┘
         │                      │                      │
         │ POST /upload         │ WS /ws/{doc_id}     │ GET /chunks
         ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    routes.py (140 lines)                  │  │
│  │   • POST /upload → Upload + Queue Background Task        │  │
│  │   • WS /ws/{id} → Real-time Progress Updates             │  │
│  │   • GET /chunks → Retrieve Processed Chunks              │  │
│  └────────────┬─────────────────────────────────────────────┘  │
│               │                                                  │
│  ┌────────────▼────────────────────────────────────────────┐   │
│  │              services.py (120 lines)                     │   │
│  │   • Upload file to storage                               │   │
│  │   • Create Document record                               │   │
│  │   • Trigger async processing                             │   │
│  └────────────┬─────────────────────────────────────────────┘  │
│               │                                                  │
│  ┌────────────▼────────────────────────────────────────────┐   │
│  │           websocket.py (70 lines)                        │   │
│  │   • Manage WebSocket connections                         │   │
│  │   • Send progress updates to clients                     │   │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          │ Async Call
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              DocumentPreprocessingPipeline (180 lines)          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  process_document(doc_id, file_path, progress_callback)  │  │
│  └──┬───────┬───────┬────────┬────────┬─────────────────────┘  │
│     │       │       │        │        │                         │
│     ▼       ▼       ▼        ▼        ▼                         │
│  Extract Classify Chunk  Embed   Store                          │
│   (20%)   (35%)   (50%)  (70%)  (85%)                          │
└─────┬───────┬───────┬────────┬────────┬─────────────────────────┘
      │       │       │        │        │
      │       │       │        │        └──────────────────┐
      │       │       │        │                           │
      ▼       ▼       ▼        ▼                           ▼
┌──────────────────────────────────────────┐    ┌────────────────────┐
│      Processing Components               │    │   PostgreSQL +     │
│  ┌────────────────────────────────┐     │    │     pgvector       │
│  │ UnstructuredExtractor (80)     │     │    │                    │
│  │  • PDF/DOCX/PPTX/TXT parsing   │     │    │  documents table   │
│  │  • Table extraction            │     │    │  ├─ id             │
│  │  • Section detection           │     │    │  ├─ status         │
│  └────────────────────────────────┘     │    │  ├─ metadata       │
│                                          │    │  └─ processed_at   │
│  ┌────────────────────────────────┐     │    │                    │
│  │ DomainClassifier (150)         │     │    │  chunks table      │
│  │  • Technical domain detection  │     │    │  ├─ id             │
│  │  • CPC hint extraction         │     │    │  ├─ chunk_text     │
│  │  • Technical terms             │     │    │  ├─ embedding      │
│  └────────────────────────────────┘     │    │  └─ metadata       │
│                                          │    └────────────────────┘
│  ┌────────────────────────────────┐     │
│  │ LlamaChunker (120)             │     │
│  │  • Semantic chunking           │     │
│  │  • Section-aware splitting     │     │
│  │  • Token counting              │     │
│  └────────────────────────────────┘     │
│                                          │
│  ┌────────────────────────────────┐     │
│  │ PatentEmbedder (90)            │     │
│  │  • PatentSBERTa embeddings     │     │
│  │  • Batch processing            │     │
│  │  • CPU/GPU support             │     │
│  └────────────────────────────────┘     │
└──────────────────────────────────────────┘


## Processing Timeline (10-page PDF)

0s  ─────┬─────────────────────────────────────────────────────▶
     │   Upload Complete
     │   Document ID returned to user
     │   WebSocket connected
     │
1s   ├─▶ Stage: EXTRACTING (20%)
     │   Unstructured.io parsing PDF
     │   
9s   ├─▶ Stage: CLASSIFYING (35%)
     │   Domain detection (software/mechanical/etc)
     │
10s  ├─▶ Stage: CHUNKING (50%)
     │   Creating semantic chunks with LlamaIndex
     │
11s  ├─▶ Stage: EMBEDDING (70%)
     │   Generating vectors with PatentSBERTa
     │   [SLOWEST STEP - 8 seconds]
     │
19s  ├─▶ Stage: STORING (85%)
     │   Saving chunks to PostgreSQL
     │
20s  ├─▶ Stage: COMPLETE (100%)
     │   ✅ Processing finished
     └─▶ WebSocket closed


## File Organization

preprocessing/              # Core processing logic
├── extractors/            # Document parsing
│   ├── base.py           #   - Abstract interface
│   └── unstructured_extractor.py  # - Unstructured.io impl
├── chunkers/             # Text chunking
│   └── llama_chunker.py  #   - LlamaIndex semantic chunking
├── embedders/            # Vector generation
│   └── patent_embedder.py #  - PatentSBERTa embeddings
├── classifiers/          # Domain detection
│   └── domain_classifier.py  # - Technical classification
└── pipeline.py           # Main orchestrator

api/documents/             # API layer
├── routes.py             # FastAPI endpoints
├── services.py           # Business logic
├── schemas.py            # Pydantic models
└── websocket.py          # WebSocket manager


## Data Flow

1. User uploads file.pdf
   ↓
2. routes.py receives upload
   ↓
3. services.py saves to storage
   ↓
4. Document record created (status: "pending")
   ↓
5. Background task started
   ↓
6. pipeline.py orchestrates processing:
   a. UnstructuredExtractor.extract()
   b. DomainClassifier.classify()
   c. LlamaChunker.chunk_sections()
   d. PatentEmbedder.generate_embeddings()
   e. Save to DocumentChunk table
   ↓
7. Document status → "completed"
   ↓
8. WebSocket sends "complete" message
   ↓
9. Frontend displays success


## Key Design Decisions

✅ **Async Processing**: User doesn't wait for processing
✅ **Progress Tracking**: Real-time WebSocket updates
✅ **Modular Design**: Each file <200 lines, single responsibility
✅ **Database Integration**: Works with existing schema
✅ **Free Tools**: Unstructured.io + LlamaIndex (open source)
✅ **Patent-Optimized**: PatentSBERTa for embeddings
✅ **Error Handling**: Graceful failures with status tracking
✅ **Soft Delete**: Documents can be recovered


## Performance Notes

Component Speed (10-page PDF):
- Extraction: ~8s (I/O bound)
- Classification: ~0.4s (CPU)
- Chunking: ~0.8s (Memory)
- Embedding: ~8s CPU / ~1.5s GPU (Slowest!)
- Storage: ~0.4s (I/O)

Total: ~18s (CPU) or ~12s (GPU)

Optimization:
- Use GPU for 5-10x faster embeddings
- Process multiple documents in parallel
- Cache embeddings for repeated content
