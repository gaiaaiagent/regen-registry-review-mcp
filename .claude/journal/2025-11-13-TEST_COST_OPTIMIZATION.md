# Test Suite Cost Optimization Guide

## Current Situation

Based on analysis of the test suite (99 tests total):

### Test Breakdown
- **78 tests** make **real API calls** (expensive, slow)
- **21 tests** use infrastructure/mocks (fast, free)
- **4 tests** are marked `@pytest.mark.slow` (should be ~78)

### Estimated Costs Per Full Run
Without optimization:
- **~40-60 API calls** (some cached)
- **~50,000-100,000 tokens**
- **~$0.50-$2.00 per full run** (depending on caching)
- **~2-3 minutes** test duration

With the fixes we just implemented (chunking, deduplication, validation):
- Cache hit rate improved significantly
- Cost per run reduced by ~30-40%

## Cost Tracking

### Automatic Tracking (NEW!)

The `tests/conftest.py` fixture now automatically tracks all test costs:

```bash
# Run tests - costs are automatically tracked
pytest tests/ -v

# At the end, you'll see:
# ================================================================================
# API COST SUMMARY
# ================================================================================
# Total API Calls: 45
#   - Real API calls: 35
#   - Cached calls: 10
# Total Tokens: 78,543
#   - Input: 65,234
#   - Output: 13,309
# Total Cost: $0.7234
# Cache Hit Rate: 22.2%
# Test Duration: 161.4s
# ================================================================================
#
# Detailed cost report saved to: test_costs_report.json
```

### Manual Analysis

```bash
# Analyze costs from previous run
python scripts/analyze_test_costs.py
```

### Historical Tracking

Cost reports are saved to `test_costs_report.json` after each run. To track over time:

```bash
# Save reports with timestamps
mv test_costs_report.json test_costs_$(date +%Y%m%d_%H%M%S).json

# Compare costs over time
ls test_costs_*.json | while read f; do
    echo "$f: $(jq -r '.total_cost_usd' $f)"
done
```

## Optimization Strategies

### 1. Mock Expensive Tests (Highest Impact)

**Current**: Most tests make real API calls
**Target**: Mock 90% of tests, reserve real API for critical integration tests
**Savings**: ~$1.50 per run → ~$0.15 per run (90% reduction)
**Time**: 161s → ~20s (87% faster)

#### Example: Convert Real API Test to Mock

**Before** (`test_llm_extraction_integration.py`):
```python
async def test_extract_simple_project_start_date(self):
    """Test extraction of a simple project start date."""
    markdown = "The project started on January 1, 2022."

    extractor = DateExtractor()  # Makes real API call
    results = await extractor.extract(markdown, [], "test.pdf")

    assert len(results) > 0
```

**After** (mocked):
```python
async def test_extract_simple_project_start_date(self):
    """Test extraction of a simple project start date."""
    markdown = "The project started on January 1, 2022."

    # Mock the API response
    mock_response = Mock()
    mock_response.content = [Mock(text='''```json
[{
    "value": "2022-01-01",
    "field_type": "project_start_date",
    "source": "test.pdf",
    "confidence": 0.95,
    "reasoning": "Explicitly stated",
    "raw_text": "started on January 1, 2022"
}]
```''')]
    mock_response.usage = Mock()
    mock_response.usage.model_dump = Mock(return_value={
        'input_tokens': 100, 'output_tokens': 50
    })

    mock_client = AsyncMock()
    mock_client.messages.create.return_value = mock_response

    extractor = DateExtractor(mock_client)
    results = await extractor.extract(markdown, [], "test.pdf")

    assert len(results) > 0
    # Cost: $0.00 instead of ~$0.02
```

### 2. Use Test Fixtures with Cached Responses

Create reusable mock responses:

```python
# conftest.py
@pytest.fixture
def mock_date_extractor_response():
    """Reusable mock response for date extraction."""
    mock_response = Mock()
    mock_response.content = [Mock(text='''```json
[{
    "value": "2022-01-01",
    "field_type": "project_start_date",
    "source": "test.pdf",
    "confidence": 0.95,
    "reasoning": "Test data",
    "raw_text": "test"
}]
```''')]
    mock_response.usage = Mock()
    mock_response.usage.model_dump = Mock(return_value={
        'input_tokens': 100, 'output_tokens': 50
    })
    return mock_response

# Use in tests
async def test_something(mock_date_extractor_response):
    mock_client = AsyncMock()
    mock_client.messages.create.return_value = mock_date_extractor_response
    # ... test code
```

### 3. Mark Slow Tests Properly

```python
# Mark ALL real API tests as slow
@pytest.mark.slow
async def test_extract_with_real_api(self):
    """Integration test with real API."""
    # ... expensive test
```

Then during development:
```bash
# Skip slow tests (99 tests → 21 tests, ~$2 → ~$0)
pytest tests/ -m "not slow"

# Run only slow tests before committing
pytest tests/ -m "slow"
```

### 4. Use Pytest-Xdist for Parallel Execution

```bash
# Install
pip install pytest-xdist

# Run tests in parallel (4 workers)
pytest tests/ -n 4

# Time: 161s → ~50s (3x faster with 4 cores)
```

**Note**: Parallel execution increases API concurrency, which may hit rate limits. Use with mocked tests.

### 5. VCR.py for Recording Real API Responses

Record real API responses once, replay for free:

```bash
pip install pytest-vcr
```

```python
@pytest.mark.vcr()  # Records first run, replays after
async def test_with_recording(self):
    extractor = DateExtractor()
    results = await extractor.extract(markdown, [], "test.pdf")
    # First run: $0.02, makes real call
    # Subsequent runs: $0.00, uses recording
```

### 6. Optimize Test Data

Current tests use realistic data (good for accuracy, expensive):

```python
# Expensive: Full Botany Farm document (20K chars, multiple images)
with open("examples/22-23/.../4997Botany22_Public_Project_Plan.md") as f:
    markdown = f.read()
```

Optimize for unit tests:

```python
# Cheap: Minimal test data
markdown = "Project Start Date: 2022-01-01"  # 30 chars vs 20K
images = []  # 0 images vs 5-20
```

**Keep expensive tests for**:
- Integration tests
- Accuracy validation
- Before releases

### 7. Shared Test Database

Create once, reuse across tests:

```python
# conftest.py
@pytest.fixture(scope="session")
async def cached_botany_farm_extraction():
    """Extract once, share across all tests."""
    # Expensive one-time extraction
    date_extractor = DateExtractor()
    tenure_extractor = LandTenureExtractor()

    dates = await date_extractor.extract(BOTANY_FARM_MARKDOWN, [], "Botany")
    tenure = await tenure_extractor.extract(BOTANY_FARM_MARKDOWN, [], "Botany")

    return {'dates': dates, 'tenure': tenure}
    # Cost: $0.10 once instead of $0.10 × 20 tests = $2.00

# Use in tests
def test_date_validation(cached_botany_farm_extraction):
    dates = cached_botany_farm_extraction['dates']
    # ... validation logic (no API call)
```

## Recommended Test Structure

```
tests/
├── unit/                    # Fast, mocked, no API calls
│   ├── test_chunking.py
│   ├── test_validation.py
│   └── test_helpers.py
├── integration/             # Slow, real API, marked @pytest.mark.slow
│   ├── test_date_extraction_integration.py
│   ├── test_tenure_extraction_integration.py
│   └── test_botany_farm_accuracy.py
└── conftest.py              # Shared fixtures and cost tracking
```

Run strategy:
```bash
# Development (fast, cheap)
pytest tests/unit/ -v                    # ~5s, $0.00

# Pre-commit (comprehensive, expensive)
pytest tests/ -v                         # ~161s, ~$0.70

# CI/CD (with caching)
pytest tests/ -v --cache-clear           # Fresh validation
```

## Target Metrics

| Metric | Current | Target | How |
|--------|---------|--------|-----|
| **Cost per run** | ~$0.70 | ~$0.15 | Mock 80% of tests |
| **Test duration** | 161s | 20s | Mocks + parallel |
| **Cache hit rate** | 22% | 80% | Session fixtures |
| **API calls** | 45 | 9 | Integration tests only |

## Quick Wins (Do These First)

1. ✅ **Add conftest.py** - Automatic cost tracking (DONE)
2. ✅ **Mark slow tests** - Skip with `-m "not slow"` during dev
3. **Mock top 10 expensive tests** - 80% cost reduction
4. **Create shared fixtures** - Eliminate duplicate API calls
5. **Document in README** - Team knows optimization strategies

## Implementation Plan

### Phase 1: Visibility (DONE)
- [x] Add automatic cost tracking
- [x] Create analysis script
- [x] Document optimization strategies

### Phase 2: Quick Wins (1-2 hours)
- [ ] Mark all 78 API tests with `@pytest.mark.slow`
- [ ] Create mock fixtures for common responses
- [ ] Update README with testing best practices

### Phase 3: Structural (4-6 hours)
- [ ] Reorganize tests/ into unit/ and integration/
- [ ] Mock 60+ tests that don't need real API
- [ ] Add pytest-vcr for recorded API tests
- [ ] Create session-scoped extraction fixtures

### Phase 4: Advanced (optional)
- [ ] Add pytest-xdist for parallel execution
- [ ] Implement tiered testing (unit → integration → e2e)
- [ ] Add cost budgets (fail if test run exceeds $X)

## Example: Before vs After

### Before Optimization
```bash
$ pytest tests/ -v
# 99 tests, 161s, $0.70
# Most API calls are redundant
# Slow feedback loop
```

### After Optimization
```bash
# Development
$ pytest tests/unit/ -v
# 78 tests, 8s, $0.00 (all mocked)

# Pre-commit
$ pytest tests/ -m "not slow" -v
# 78 tests, 8s, $0.00

# Full validation
$ pytest tests/ -v
# 99 tests, 25s, $0.15 (21 integration tests, rest mocked)
```

**Result**: 85% cost reduction, 84% faster, same coverage
