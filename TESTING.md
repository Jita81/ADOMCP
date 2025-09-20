# ADOMCP Testing Framework

This document describes the comprehensive testing framework for the Azure DevOps Multi-Platform MCP (ADOMCP) server.

## Overview

The testing framework consists of three main components:

1. **Regression Tests** (`regression_tests.py`) - Comprehensive end-to-end functionality testing
2. **Performance Tests** (`performance_tests.py`) - Load testing and performance analysis  
3. **Test Runner** (`run_tests.py`) - Unified interface to run all tests

## Test Files

### 🧪 Regression Tests (`regression_tests.py`)

Comprehensive end-to-end testing of all MCP functionality including:

- **MCP Server Health** - Server availability and basic endpoints
- **Endpoint Accessibility** - All API endpoints responding correctly
- **JSON-RPC Protocol** - MCP protocol compliance testing
- **Azure DevOps Integration** - Real API connection and authentication
- **GitHub Integration** - Real API connection and authentication  
- **Work Item CRUD** - Complete lifecycle testing (Create, Read, Update)
- **GitHub Issue Creation** - Cross-platform integration testing
- **API Key Management** - Secure storage and retrieval simulation
- **Supabase Configuration** - Database setup and configuration
- **Error Handling** - Validation and error response testing

**Features:**
- ✅ Uses real API credentials for live testing
- ✅ Comprehensive logging with timestamps
- ✅ Detailed JSON result output
- ✅ Individual test success/failure tracking
- ✅ Creates actual work items and issues for validation

### ⚡ Performance Tests (`performance_tests.py`)

Performance and load testing including:

- **Response Time Analysis** - Latency testing across all endpoints
- **Concurrent Request Handling** - Multi-threaded load testing
- **Load Sustainability** - Sustained load over time
- **Azure DevOps Performance** - External API latency testing
- **GitHub Performance** - External API latency testing

**Features:**
- ✅ Configurable concurrency levels (1, 2, 5, 10 concurrent requests)
- ✅ Response time thresholds and SLA monitoring
- ✅ Performance degradation detection
- ✅ Detailed metrics collection (avg, median, P95, max response times)
- ✅ Success rate monitoring

### 🎯 Test Runner (`run_tests.py`)

Unified test execution interface with options:

```bash
# Run regression tests only
python3 run_tests.py --regression

# Run performance tests only  
python3 run_tests.py --performance

# Run all tests
python3 run_tests.py --all

# Run quick smoke test
python3 run_tests.py --quick
```

## Installation & Requirements

```bash
# Install required packages
pip install requests aiohttp

# Make scripts executable
chmod +x regression_tests.py performance_tests.py run_tests.py
```

## Configuration

Tests are pre-configured with the following:

- **MCP Server**: `https://adomcp.vercel.app`
- **Azure DevOps**: Uses provided PAT token and MCPTest project
- **GitHub**: Uses provided token and ADOMCP repository
- **Response Thresholds**: 5 seconds for standard endpoints, 10 seconds for Azure DevOps

## Usage Examples

### Quick Health Check
```bash
./run_tests.py --quick
```

### Full Regression Test
```bash
./regression_tests.py
```

### Performance Testing
```bash
./performance_tests.py
```

### Complete Test Suite
```bash
./run_tests.py --all
```

## Output and Logging

### Console Output
- Real-time test progress with ✅/❌ status indicators
- Detailed metrics and timing information
- Summary statistics and success rates

### Log Files
- `regression_test_YYYYMMDD_HHMMSS.log` - Detailed regression test logs
- `performance_test_YYYYMMDD_HHMMSS.log` - Detailed performance test logs

### Result Files
- `regression_results_YYYYMMDD_HHMMSS.json` - Complete regression test results
- `performance_results_YYYYMMDD_HHMMSS.json` - Complete performance test results

## Test Coverage

### ✅ What's Tested

#### Infrastructure & Deployment
- Vercel serverless function deployment
- All API endpoint accessibility  
- HTTP status code validation
- JSON response format validation

#### MCP Protocol Compliance
- JSON-RPC 2.0 standard compliance
- `tools/list` method functionality
- `tools/call` method functionality
- Error handling and response format

#### Real API Integrations
- Azure DevOps connection and authentication
- GitHub connection and authentication
- Work item creation, reading, and updating
- Issue creation and cross-platform linking

#### Security & Configuration
- API key storage and validation
- Platform validation (azure_devops, github, gitlab)
- User ID requirements and validation
- Supabase configuration management

#### Performance & Reliability
- Response time analysis under load
- Concurrent request handling
- Sustained load testing
- Performance degradation detection

### ⏳ Not Yet Tested

- **Attachment Management** - File upload/download to work items
- **Real Supabase Integration** - Actual database operations
- **GitLab Integration** - Third platform API testing
- **Work Item Relationships** - Parent-child hierarchies
- **Batch Operations** - Multiple work item creation
- **Rate Limiting** - API quota and throttling behavior

## Performance Benchmarks

### Target Metrics
- **Response Time**: < 5 seconds for standard endpoints
- **Azure DevOps API**: < 10 seconds (external dependency)
- **GitHub API**: < 5 seconds (external dependency)
- **Success Rate**: > 95% under normal load
- **Concurrent Requests**: Handle up to 10 concurrent requests

### Current Results
Run the performance tests to see current benchmarks for your deployment.

## Troubleshooting

### Common Issues

1. **Connection Timeouts**
   - Check internet connectivity
   - Verify Vercel deployment is running
   - Confirm API tokens are valid

2. **API Authentication Failures**
   - Verify Azure DevOps PAT token permissions
   - Check GitHub token scope and expiration
   - Confirm organization/repository access

3. **Performance Issues**
   - Monitor Vercel function cold starts
   - Check external API response times
   - Review concurrent request limits

### Debug Mode
Add detailed logging by modifying the logging level:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Integration with CI/CD

The test framework is designed for integration with CI/CD pipelines:

```bash
# Exit codes
# 0 = All tests passed
# 1 = One or more tests failed

# Example CI script
./run_tests.py --all
if [ $? -eq 0 ]; then
    echo "✅ All tests passed - safe to deploy"
else
    echo "❌ Tests failed - blocking deployment"
    exit 1
fi
```

## Contributing

When adding new functionality to ADOMCP:

1. **Add regression test** - Ensure new features have test coverage
2. **Update performance tests** - If new endpoints added  
3. **Run full test suite** - Verify no regressions introduced
4. **Update benchmarks** - Document any performance changes

## Test Data Management

### Test Artifacts Created
- Azure DevOps work items with "regression-test" tags
- GitHub issues with "regression-test" labels
- Log files with timestamps

### Cleanup
Test artifacts are left in place for verification but can be manually cleaned up:
- Delete test work items from Azure DevOps
- Close test issues in GitHub
- Remove old log files locally

---

**For questions or issues with the testing framework, check the logs first, then review the test output for specific error messages.**
