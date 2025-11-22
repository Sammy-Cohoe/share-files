import asyncio
import json
import sys
from pathlib import Path

# Add src to path so we can import from preprocessing
sys.path.insert(0, str(Path(__file__).parent / "src"))

from preprocessing.extractors import UnstructuredExtractor
from preprocessing.chunkers import LlamaChunker
from preprocessing.embedders import PatentEmbedder


async def test_unstructured_extractor():
    """Test the UnstructuredExtractor with dune_analysis.pdf"""

    # Initialize the extractor
    extractor = UnstructuredExtractor()

    # Get the PDF file path
    pdf_path = Path(__file__).parent / "src/preprocessing/extractors/dune_analysis_with_tables.pdf"

    print(f"Testing UnstructuredExtractor")
    print(f"PDF path: {pdf_path}")
    print(f"File exists: {pdf_path.exists()}")
    print("=" * 80)

    if not pdf_path.exists():
        print("ERROR: PDF file not found!")
        return

    # Test 1: Check if file type is supported
    print("\n1. Testing file type support:")
    is_supported = extractor.supports_file_type(str(pdf_path))
    print(f"   PDF file supported: {is_supported}")

    if not is_supported:
        print("   ERROR: PDF files should be supported!")
        return

    # Test 2: Extract content
    print("\n2. Extracting content from PDF...")
    try:
        content = await extractor.extract(str(pdf_path))

        print(f"   ✓ Extraction successful!")
        print(f"   - Number of sections: {len(content.sections)}")
        print(f"   - Number of tables: {len(content.tables)}")
        print(f"   - Has tables: {content.has_tables}")
        print(f"   - Full text length: {len(content.full_text)} characters")

        # Test 3: Display sections
        print("\n3. Sections found:")
        for section_name, section_content in content.sections.items():
            print(f"   - {section_name}: {len(section_content)} items")
            if section_content:
                # Show first item in each section
                preview = section_content[0][:100] if len(section_content[0]) > 100 else section_content[0]
                print(f"     Preview: {preview}...")

        # Test 4: Display first few lines of text
        print("\n4. First 50 characters of extracted text:")
        print(f"   {content.full_text[:50]}...")

        # Test 5: Display tables info
        if content.has_tables:
            print(f"\n5. Tables found ({len(content.tables)}):")
            for i, table in enumerate(content.tables[:3], 1):  # Show first 3 tables
                print(f"   Table {i}:")
                text_preview = table['text'][:150].replace('\n', ' ')
                print(f"   - Text preview: {text_preview}...")
                if table['metadata']:
                    print(f"   - Metadata keys: {list(table['metadata'].keys())}")
        else:
            print("\n5. No tables found in document")

        # Test 6: Convert to dict and save as JSON
        print("\n6. Saving extracted content to JSON:")
        output_path = Path(__file__).parent / "extraction_output.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(content.to_dict(), f, indent=2, ensure_ascii=False)
        print(f"   ✓ Saved to: {output_path}")

        print("\n" + "=" * 80)
        print("✓ All tests completed successfully!")
        print("=" * 80)

    except Exception as e:
        print(f"   ✗ Extraction failed: {e}")
        import traceback
        traceback.print_exc()


async def test_llama_chunker():
    """Test the LlamaChunker with extracted content from UnstructuredExtractor"""

    # Initialize the extractor and chunker
    extractor = UnstructuredExtractor()
    chunker = LlamaChunker(chunk_size=512, chunk_overlap=128)

    # Get the PDF file path
    pdf_path = Path(__file__).parent / "src/preprocessing/extractors/dune_analysis_with_tables.pdf"

    print(f"\n{'=' * 80}")
    print(f"Testing LlamaChunker")
    print(f"PDF path: {pdf_path}")
    print("=" * 80)

    if not pdf_path.exists():
        print("ERROR: PDF file not found!")
        return

    try:
        # First extract the content
        print("\n1. Extracting content from PDF...")
        content = await extractor.extract(str(pdf_path))
        print(f"   ✓ Extraction successful!")
        print(f"   - Number of sections: {len(content.sections)}")
        print(f"   - Number of tables: {len(content.tables)}")

        # Test 2: Chunk sections
        print("\n2. Chunking sections...")
        base_metadata = {
            "source_file": pdf_path.name,
            "file_type": "pdf"
        }

        section_chunks = await chunker.chunk_sections(content.sections, base_metadata)
        print(f"   ✓ Chunking successful!")
        print(f"   - Total chunks created: {len(section_chunks)}")

        # Display chunk statistics
        print("\n3. Chunk statistics:")
        total_tokens = sum(chunk.token_count for chunk in section_chunks)
        avg_tokens = total_tokens / len(section_chunks) if section_chunks else 0
        print(f"   - Total tokens: {total_tokens}")
        print(f"   - Average tokens per chunk: {avg_tokens:.2f}")

        # Show first few chunks
        print("\n4. Sample chunks (first 3):")
        for chunk in section_chunks[:3]:
            print(f"\n   Chunk {chunk.chunk_index}:")
            print(f"   - Section: {chunk.section}")
            print(f"   - Token count: {chunk.token_count}")
            print(f"   - Text preview: {chunk.text[:100]}...")
            print(f"   - Metadata: {list(chunk.metadata.keys())}")

        # Test 3: Chunk tables if available
        if content.has_tables:
            print(f"\n5. Chunking tables ({len(content.tables)} tables)...")
            table_chunks = await chunker.chunk_tables(content.tables, base_metadata)
            print(f"   ✓ Table chunking successful!")
            print(f"   - Total table chunks created: {len(table_chunks)}")

            # Show first table chunk
            if table_chunks:
                print(f"\n6. Sample table chunk:")
                chunk = table_chunks[0]
                print(f"   - Chunk index: {chunk.chunk_index}")
                print(f"   - Token count: {chunk.token_count}")
                print(f"   - Text preview: {chunk.text[:150]}...")
        else:
            print("\n5. No tables to chunk")

        # Test 4: Save all chunks to JSON
        print("\n7. Saving chunks to JSON:")
        output_path = Path(__file__).parent / "chunking_output.json"

        all_chunks_dict = {
            "section_chunks": [chunk.to_dict() for chunk in section_chunks],
            "table_chunks": [chunk.to_dict() for chunk in table_chunks] if content.has_tables else [],
            "statistics": {
                "total_section_chunks": len(section_chunks),
                "total_table_chunks": len(table_chunks) if content.has_tables else 0,
                "total_chunks": len(section_chunks) + (len(table_chunks) if content.has_tables else 0),
                "total_tokens": total_tokens,
                "average_tokens_per_chunk": avg_tokens
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_chunks_dict, f, indent=2, ensure_ascii=False)
        print(f"   ✓ Saved to: {output_path}")

        print("\n" + "=" * 80)
        print("✓ All chunker tests completed successfully!")
        print("=" * 80)

    except Exception as e:
        print(f"   ✗ Chunking failed: {e}")
        import traceback
        traceback.print_exc()


async def test_patent_embedder():
    """Test the PatentEmbedder with chunked content"""

    # Initialize components
    extractor = UnstructuredExtractor()
    chunker = LlamaChunker(chunk_size=512, chunk_overlap=128)
    embedder = PatentEmbedder(device="cpu")

    # Get the PDF file path
    pdf_path = Path(__file__).parent / "src/preprocessing/extractors/dune_analysis_with_tables.pdf"

    print(f"\n{'=' * 80}")
    print(f"Testing PatentEmbedder")
    print(f"PDF path: {pdf_path}")
    print("=" * 80)

    if not pdf_path.exists():
        print("ERROR: PDF file not found!")
        return

    try:
        # Step 1: Extract content
        print("\n1. Extracting content from PDF...")
        content = await extractor.extract(str(pdf_path))
        print(f"   ✓ Extraction successful!")

        # Step 2: Chunk the content
        print("\n2. Chunking content...")
        base_metadata = {
            "source_file": pdf_path.name,
            "file_type": "pdf"
        }
        section_chunks = await chunker.chunk_sections(content.sections, base_metadata)
        print(f"   ✓ Chunking successful!")
        print(f"   - Total chunks: {len(section_chunks)}")

        # Step 3: Test single embedding generation
        print("\n3. Testing single embedding generation...")
        if section_chunks:
            test_text = section_chunks[0].text
            single_embedding = await embedder.generate_single_embeddings(test_text)
            print(f"   ✓ Single embedding generated!")
            print(f"   - Embedding dimension: {len(single_embedding)}")
            print(f"   - First 5 values: {single_embedding[:5]}")

        # Step 4: Test batch embedding generation
        print("\n4. Testing batch embedding generation...")
        # Use first 5 chunks for testing (or all if less than 5)
        test_chunks = section_chunks[:min(5, len(section_chunks))]
        test_texts = [chunk.text for chunk in test_chunks]

        batch_embeddings = await embedder.generate_embeddings(test_texts, batch_size=2)
        print(f"   ✓ Batch embeddings generated!")
        print(f"   - Number of embeddings: {len(batch_embeddings)}")
        if batch_embeddings:
            print(f"   - Embedding dimension: {len(batch_embeddings[0])}")
            print(f"   - First embedding preview: {batch_embeddings[0][:1]}")

        # Step 5: Test empty text handling
        print("\n5. Testing empty text handling...")
        empty_embedding = await embedder.generate_single_embeddings("")
        print(f"   ✓ Empty text handled correctly!")
        print(f"   - Empty embedding result: {empty_embedding}")

        # Step 6: Save embeddings to JSON
        print("\n6. Saving embeddings to JSON:")
        output_path = Path(__file__).parent / "embedding_output.json"

        embeddings_output = {
            "model_name": "AI-Growth-Lab/PatentSBERTa",
            "embedding_dimension": len(single_embedding) if single_embedding else 0,
            "test_chunks": [
                {
                    "chunk_index": chunk.chunk_index,
                    "section": chunk.section,
                    "text_preview": chunk.text[:100],
                    "embedding": batch_embeddings[i] if i < len(batch_embeddings) else None
                }
                for i, chunk in enumerate(test_chunks)
            ],
            "statistics": {
                "total_test_chunks": len(test_chunks),
                "embeddings_generated": len(batch_embeddings)
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(embeddings_output, f, indent=2, ensure_ascii=False)
        print(f"   ✓ Saved to: {output_path}")

        print("\n" + "=" * 80)
        print("✓ All embedder tests completed successfully!")
        print("=" * 80)

    except Exception as e:
        print(f"   ✗ Embedding failed: {e}")
        import traceback
        traceback.print_exc()


async def run_all_tests():
    """Run extractor, chunker, and embedder tests"""
    await test_unstructured_extractor()
    await test_llama_chunker()
    await test_patent_embedder()


if __name__ == "__main__":
    print("Starting UnstructuredExtractor, LlamaChunker, and PatentEmbedder tests...\n")
    asyncio.run(run_all_tests())
