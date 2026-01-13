# SDK Tests

## Overview

Tests for the Node.js SDK focus on:

1. **Middleware Behavior** (`index.test.ts`): Tests for the Express error ingestion middleware including:
   - Error capture and transmission
   - Path sanitization (numeric IDs, UUIDs)
   - Query string removal
   - Status code handling
   - Duplicate error prevention
   - Error handling and resilience

## Running Tests

```bash
cd sdks/node
npm test
```

Tests use Vitest with mocked HTTP requests (axios) to avoid making real network calls.
