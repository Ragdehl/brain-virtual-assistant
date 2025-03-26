# Common Tools Tests

This directory contains pytest tests for the common tools layer used across all Lambda functions in the Obsidian AI Assistant.

## Test Coverage

The tests cover the following utilities:

- **Validation Utilities**: Tests for field validation, type checking, regex validation, etc.
- **DynamoDB Utilities**: Tests for DynamoDB operations (get, put, update, delete, query, scan).
- **S3 Utilities**: Tests for S3 operations (get, put, delete object operations).
- **OpenSearch Utilities**: Tests for OpenSearch operations (create index, document CRUD, search, vector search).
- **Exception Handler**: Tests for the Lambda exception handling decorator.

## Running the Tests

To run the tests for the common tools layer:

1. Make sure you're in the project root directory
2. Install the development dependencies:
   ```
   pip install -r requirements-dev.txt
   ```
3. Run pytest on the common tools tests:
   ```
   pytest lambdas/layers/common_tools/tests/
   ```

## Running with Coverage

To run the tests with coverage reporting:

```
pytest lambdas/layers/common_tools/tests/ --cov=lambdas/layers/common_tools/python/lib
```

Generate a coverage report:

```
pytest lambdas/layers/common_tools/tests/ --cov=lambdas/layers/common_tools/python/lib --cov-report=html
```

This will generate an HTML coverage report in the `htmlcov` directory.

## Test Structure

- **conftest.py**: Contains shared fixtures used across all tests
- **test_validation_util.py**: Tests for validation utilities
- **test_dynamodb_util.py**: Tests for DynamoDB utilities
- **test_s3_util.py**: Tests for S3 utilities
- **test_opensearch_util.py**: Tests for OpenSearch utilities
- **test_exception_handler.py**: Tests for exception handling decorator

## Notes on Test Design

- Tests use mocking extensively to avoid actual AWS service calls
- Each utility's success and error scenarios are thoroughly tested
- Validation tests cover edge cases and invalid inputs
- The tests follow the AAA pattern (Arrange, Act, Assert) 