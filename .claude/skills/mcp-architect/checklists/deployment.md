# Production Deployment Checklist

Comprehensive checklist for deploying MCP servers to production environments.

## Pre-Deployment

### Code Quality
- [ ] All tests passing (`uv run pytest`)
- [ ] Code linted and formatted (`uv run ruff check . && uv run ruff format .`)
- [ ] Type checking passes (`uv run mypy src/`)
- [ ] No security vulnerabilities in dependencies
- [ ] Error handling implemented for all tools
- [ ] Input validation with Pydantic models
- [ ] Logging configured to stderr only
- [ ] No hardcoded credentials or API keys

### Configuration
- [ ] `uv.lock` committed to version control
- [ ] `.python-version` file specifies Python 3.10+
- [ ] `pyproject.toml` has correct `requires-python = ">=3.10"`
- [ ] All dependencies pinned with version constraints
- [ ] Development dependencies separated (`[tool.uv.dev-dependencies]`)
- [ ] Entry point configured in `[project.scripts]`

### Documentation
- [ ] README.md with setup instructions
- [ ] Tool descriptions clear and actionable for agents
- [ ] Resource URI patterns documented
- [ ] Environment variables documented
- [ ] Configuration examples provided
- [ ] Troubleshooting guide included

## Deployment Configuration

### Claude Desktop Configuration
- [ ] Use absolute paths (not relative)
- [ ] Use `uv` command with `--directory` flag
- [ ] Environment variables as strings (not numbers/booleans)
- [ ] Test configuration on actual Claude Desktop

**Example:**
```json
{
  "mcpServers": {
    "my-server": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/project",
        "run",
        "my-server"
      ],
      "env": {
        "API_KEY": "value",
        "LOG_LEVEL": "info",
        "PORT": "8000"
      }
    }
  }
}
```

### Environment Variables
- [ ] All secrets via environment variables
- [ ] No sensitive data in code or config files
- [ ] Document all required environment variables
- [ ] Provide `.env.example` template
- [ ] Validate environment variables on startup

### Docker Deployment
- [ ] Multi-stage Dockerfile for minimal image size
- [ ] Non-root user configured
- [ ] Health check endpoint implemented
- [ ] `.dockerignore` excludes unnecessary files
- [ ] Environment variables configurable
- [ ] Volumes for persistent data (if needed)
- [ ] Network configuration for service communication
- [ ] Resource limits set (memory, CPU)

**Test Docker Build:**
```bash
docker build -t mcp-server:test .
docker run --rm -e API_KEY=test mcp-server:test
```

## Testing Before Production

### Local Testing
- [ ] Test with MCP Inspector: `npx @modelcontextprotocol/inspector python server.py`
- [ ] Test with Claude Desktop locally
- [ ] Test all tools with various inputs
- [ ] Test error conditions and edge cases
- [ ] Test with `--frozen` flag: `uv run --frozen python server.py`
- [ ] Verify logs go to stderr only
- [ ] Check memory usage under load
- [ ] Test connection pooling (if applicable)

### Integration Testing
- [ ] Test with actual external services (not mocks)
- [ ] Test authentication and authorization
- [ ] Test timeout handling
- [ ] Test rate limiting
- [ ] Test concurrent requests
- [ ] Test graceful shutdown (SIGTERM/SIGINT)
- [ ] Test restart resilience

### Performance Testing
- [ ] Measure context window usage (should be <10%)
- [ ] Measure tool response times (P95 <100ms, P99 <500ms)
- [ ] Test with realistic data volumes
- [ ] Identify and optimize slow operations
- [ ] Verify caching works correctly
- [ ] Test connection pool efficiency

## Production Deployment

### Server Configuration
- [ ] Use production Python version (3.10-3.13)
- [ ] Set `UV_COMPILE_BYTECODE=1` for faster startup
- [ ] Use `--frozen` flag to enforce lockfile
- [ ] Configure log level appropriately (INFO or WARNING)
- [ ] Set up log aggregation (if applicable)
- [ ] Configure monitoring and alerting
- [ ] Set up health check endpoint

### Security Hardening
- [ ] Run as non-root user
- [ ] Minimal file system permissions
- [ ] Network isolation (if applicable)
- [ ] API keys rotated regularly
- [ ] HTTPS for HTTP transport
- [ ] Input validation on all tools
- [ ] Error masking enabled: `FastMCP(..., mask_error_details=True)`
- [ ] SQL injection prevention (parameterized queries)
- [ ] Path traversal protection
- [ ] Rate limiting implemented

### CI/CD Pipeline
- [ ] Automated testing on push
- [ ] Automated linting and type checking
- [ ] Security scanning for vulnerabilities
- [ ] Docker image building and scanning
- [ ] Automated deployment to staging
- [ ] Manual approval for production
- [ ] Rollback procedure documented

**Example GitHub Actions:**
```yaml
- uses: astral-sh/setup-uv@v7
  with:
    version: "0.9.8"
- run: uv sync --frozen
- run: uv run pytest
- run: uv run ruff check .
- run: uv run mypy src/
```

### Deployment Process
- [ ] Deploy to staging first
- [ ] Run smoke tests on staging
- [ ] Monitor staging for 24-48 hours
- [ ] Review logs for errors or warnings
- [ ] Check performance metrics
- [ ] Deploy to production with gradual rollout
- [ ] Monitor production closely for first hour
- [ ] Have rollback plan ready

## Post-Deployment

### Monitoring
- [ ] Set up uptime monitoring
- [ ] Monitor error rates
- [ ] Monitor response times
- [ ] Monitor resource usage (CPU, memory, disk)
- [ ] Set up alerts for anomalies
- [ ] Dashboard for key metrics

**Key Metrics to Track:**
- Tool call success rate (target: >99%)
- P95 response time (target: <100ms)
- P99 response time (target: <500ms)
- Error rate (target: <0.1%)
- Context window usage (target: <10%)
- Concurrent connections
- Cache hit rate (if applicable)

### Logging
- [ ] Structured logging implemented
- [ ] Log aggregation configured
- [ ] Log retention policy set
- [ ] Sensitive data not logged
- [ ] Log levels appropriate (ERROR, WARN, INFO)
- [ ] Request IDs for tracing

**Log Format:**
```python
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Maintenance
- [ ] Regular dependency updates scheduled
- [ ] Security patches applied promptly
- [ ] Performance review monthly
- [ ] Log review weekly
- [ ] Incident response procedure documented
- [ ] Backup and disaster recovery tested

### Documentation Updates
- [ ] Deployment process documented
- [ ] Runbook for common issues
- [ ] Architecture diagrams current
- [ ] API documentation updated
- [ ] Change log maintained

## Platform-Specific Checklists

### Docker Deployment
- [ ] Image size optimized (<500MB target)
- [ ] Layers cached effectively
- [ ] Base image from trusted source
- [ ] Security scanning passed
- [ ] Container restart policy configured
- [ ] Resource limits set
- [ ] Volume mounts for persistence
- [ ] Network policies configured

### Kubernetes Deployment
- [ ] Deployment manifest with replicas
- [ ] Service for load balancing
- [ ] ConfigMap for configuration
- [ ] Secret for sensitive data
- [ ] Resource requests and limits
- [ ] Liveness and readiness probes
- [ ] Horizontal Pod Autoscaling (HPA)
- [ ] Pod Disruption Budget (PDB)
- [ ] Network policies for security

### Serverless Deployment (Lambda, Cloud Run)
- [ ] Cold start optimized (<5s)
- [ ] Memory allocation appropriate
- [ ] Timeout configured
- [ ] Environment variables set
- [ ] IAM roles minimal permissions
- [ ] VPC configuration (if needed)
- [ ] Concurrency limits set
- [ ] Cost monitoring enabled

## Rollback Procedure

### Pre-Rollback
- [ ] Identify issue requiring rollback
- [ ] Document issue for post-mortem
- [ ] Notify stakeholders
- [ ] Prepare previous version

### Rollback Execution
- [ ] Stop new deployments
- [ ] Revert to previous version
- [ ] Verify rollback successful
- [ ] Monitor for stability
- [ ] Confirm issue resolved

### Post-Rollback
- [ ] Root cause analysis
- [ ] Document lessons learned
- [ ] Plan fix for next deployment
- [ ] Update procedures if needed

## Common Production Issues

### Issue: Server Not Connecting
**Check:**
- [ ] Path is absolute in configuration
- [ ] UV installed and in PATH
- [ ] Python version correct (3.10+)
- [ ] Dependencies installed (`uv sync`)
- [ ] No syntax errors in server code
- [ ] Logs for error messages

### Issue: High Context Usage
**Fix:**
- [ ] Reduce number of tools (target: 10-15 max)
- [ ] Optimize tool descriptions (concise but clear)
- [ ] Consider CLI/scripts alternative
- [ ] Implement progressive disclosure with prompts

### Issue: Slow Response Times
**Optimize:**
- [ ] Enable connection pooling
- [ ] Implement caching
- [ ] Use async/await properly
- [ ] Reduce external API calls
- [ ] Profile and optimize bottlenecks

### Issue: Memory Leaks
**Check:**
- [ ] Close connections properly
- [ ] Clear caches periodically
- [ ] No circular references
- [ ] Monitor memory usage over time
- [ ] Use `lifespan` for cleanup

### Issue: Authentication Failures
**Verify:**
- [ ] Environment variables set correctly
- [ ] API keys valid and not expired
- [ ] Permissions configured properly
- [ ] Network access allowed
- [ ] SSL/TLS certificates valid

## Final Checklist Summary

Before marking deployment complete:

- [ ] All pre-deployment checks passed
- [ ] Staging deployment successful
- [ ] Production deployment successful
- [ ] Monitoring configured and active
- [ ] Documentation complete and current
- [ ] Team trained on operations
- [ ] Rollback procedure tested
- [ ] Post-deployment review scheduled

## Resources

**Testing:**
- MCP Inspector: `npx @modelcontextprotocol/inspector`
- UV commands: `uv run --frozen`, `uv sync`

**Monitoring Tools:**
- Logs: stderr output
- Metrics: Prometheus, CloudWatch, etc.
- Tracing: OpenTelemetry

**Documentation:**
- Official MCP docs: https://modelcontextprotocol.io/
- UV docs: https://docs.astral.sh/uv/

## Success Criteria

Your MCP server is production-ready when:

✅ All tests passing
✅ Security hardened
✅ Monitoring in place
✅ Documentation complete
✅ Team trained
✅ Rollback tested
✅ Performance validated
✅ 24-hour stability confirmed

---

**Remember:** Production readiness is a journey, not a destination. Continuous improvement and monitoring are essential for long-term success.
