# Supported Queries

## Supported question categories

This module is scoped to conversational analytics over structured hospital data in PostgreSQL.

Supported categories:

- Count queries
- Aggregation queries
- Top-N and ranking queries
- Department-based filtering
- Downtime analysis
- Inventory threshold analysis

## Example questions

- What is the total count of our ICU assets?
- Which medical device experiences the highest downtime?
- Which spare parts are currently below the reorder level?
- Top 5 assets by downtime
- Count assets by department
- Average downtime per asset type
- Total maintenance cost by asset
- Which departments have the highest number of assets?

## Current limitations

- The module is intentionally read-only and only allows SELECT queries.
- Multiple SQL statements are blocked.
- Unsafe SQL keywords are blocked before execution.
- The current implementation is focused on structured data only; there is no RAG, PDF retrieval, forecasting, or multi-agent orchestration.
- Raw SQL returned from the agent path is not relied on directly; the production path uses controlled SQL generation, validation, and direct execution so the query can be safely inspected before execution.
- The SQL output quality depends on the schema quality and the availability of descriptive table and column names.

## Suggestions for future extension

- Add a schema-aware table whitelist for stricter query control.
- Add query result caching for repeated analytics questions.
- Add role-based access control for departmental or asset-level visibility.
- Add audit logging for questions, generated SQL, and execution timing.
- Add pagination or export support for larger result sets.
- Add read-only database credentials with a dedicated reporting role.
