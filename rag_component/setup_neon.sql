-- ─────────────────────────────────────────────────────────────────
-- setup_neon.sql
-- Run these commands ONCE in your Neon SQL Editor
-- Dashboard → Your Project → SQL Editor → paste and run
-- ─────────────────────────────────────────────────────────────────

-- Step 1: Enable the pgvector extension
-- This adds vector data type and similarity search to your Neon DB
CREATE EXTENSION IF NOT EXISTS vector;

-- Step 2: Verify it was enabled (should return 1 row)
SELECT extname, extversion 
FROM pg_extension 
WHERE extname = 'vector';

-- ─────────────────────────────────────────────────────────────────
-- After running run_ingestion.py, you can verify your vectors with:
-- ─────────────────────────────────────────────────────────────────

-- Count total stored chunks
-- SELECT COUNT(*) FROM langchain_pg_embedding;

-- Count chunks per manual
-- SELECT 
--     cmetadata->>'source_manual'  AS manual,
--     COUNT(*)                      AS chunk_count
-- FROM langchain_pg_embedding
-- GROUP BY cmetadata->>'source_manual'
-- ORDER BY chunk_count DESC;

-- Count chunks per section type
-- SELECT 
--     cmetadata->>'section_type'   AS section_type,
--     COUNT(*)                      AS chunk_count
-- FROM langchain_pg_embedding
-- GROUP BY cmetadata->>'section_type'
-- ORDER BY chunk_count DESC;

-- Preview a sample chunk
-- SELECT 
--     cmetadata->>'source_manual'  AS manual,
--     cmetadata->>'page'           AS page,
--     cmetadata->>'section_type'   AS section,
--     LEFT(document, 200)           AS preview
-- FROM langchain_pg_embedding
-- LIMIT 5;
