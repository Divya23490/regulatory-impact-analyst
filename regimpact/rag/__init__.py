"""Retrieval-augmented generation (RAG) layer.

Pipeline, offline then online:

    ingest      official text (EUR-Lex / Cellar XHTML)  ->  data/regulations/*.md
    chunking    markdown + policy register CSV          ->  Chunk[]  (one per article paragraph / policy)
    embeddings  Chunk.text                              ->  unit-length vectors
    store       vectors + metadata                      ->  Chroma collection (HNSW, cosine)
    bm25        Chunk.text                              ->  in-memory lexical index
    retriever   query -> BM25 ranks + dense ranks       ->  Reciprocal Rank Fusion -> top-k
    verify      cited chunk ids                         ->  exist in corpus? actually retrieved?

`KnowledgeBase` (knowledge_base.py) is the single entry point the agents use.
Import it from the submodule — this package deliberately doesn't re-export it,
so `import regimpact.rag.ingest` (or the chunker tests) never pulls in Chroma
or the Gemini client.
"""
