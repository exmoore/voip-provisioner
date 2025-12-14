# Integration Tests

This directory contains integration tests that verify the complete VOIP provisioner system with a real Asterisk instance running in Docker.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.9+ with pytest
- All project dependencies installed: `pip install -e ".[dev]"`

## Test Structure

- `conftest.py` - Pytest fixtures for Docker services and test data
- `test_phone_asterisk_integration.py` - Phone CRUD + Asterisk integration tests
- `test_phonebook_integration.py` - Phonebook CRUD tests
- `test_settings_integration.py` - Global settings tests
- `test_e2e_workflow.py` - End-to-end workflow tests
- `docker/` - Docker configuration for test environment
  - `asterisk/` - Asterisk Docker image and configuration
  - `docker-compose.test.yml` - Docker Compose configuration

## Running Integration Tests

### Run all integration tests:

```bash
pytest tests/integration/ -v -m integration
```

### Run specific test file:

```bash
pytest tests/integration/test_phone_asterisk_integration.py -v
```

### Run specific test:

```bash
pytest tests/integration/test_phone_asterisk_integration.py::TestPhoneAsteriskIntegration::test_create_phone_generates_asterisk_config -v
```

### Run with coverage:

```bash
pytest tests/integration/ -v -m integration --cov=provisioner --cov-report=html
```

## Manual Docker Setup

If you want to manually start the test environment:

```bash
cd tests/integration/docker
docker-compose -f docker-compose.test.yml up -d --build
```

Wait for services to be ready (check logs):

```bash
docker-compose -f docker-compose.test.yml logs -f
```

The provisioner API will be available at `http://localhost:8080`

To stop and clean up:

```bash
docker-compose -f docker-compose.test.yml down -v
```

## Test Environment

The integration tests create:

1. **Asterisk Container**:
   - Asterisk 18+ with PJSIP
   - AMI enabled on port 5038 (admin/testsecret)
   - SIP on port 5060
   - Health checks enabled

2. **Provisioner Container**:
   - Python provisioner application
   - API on port 8080
   - Connected to Asterisk via AMI
   - Shared volume for Asterisk config files

3. **Shared Volume**:
   - `/etc/asterisk` - Configuration files
   - Provisioner writes pjsip.conf and extensions.conf
   - Asterisk reads configurations

## What's Tested

### Phone Management
- Create, read, update, delete phones via API
- Automatic Asterisk config generation
- Endpoint registration in Asterisk
- Config preview functionality
- Multiple phones with different settings

### Phonebook
- CRUD operations for directory entries
- XML generation for Yealink and Fanvil phones
- Persistence across operations

### Settings
- Global settings management
- Settings inheritance for new phones
- Validation
- Persistence

### End-to-End Workflows
- Complete phone lifecycle
- Settings override behavior
- Provisioning workflow (phone fetches config)
- Multi-tenant scenarios
- System health and stats

## Debugging Failed Tests

### View container logs:

```bash
cd tests/integration/docker
docker-compose -f docker-compose.test.yml logs provisioner
docker-compose -f docker-compose.test.yml logs asterisk
```

### Access Asterisk CLI:

```bash
docker exec -it test-asterisk asterisk -rvvv
```

Common Asterisk commands:
- `core show version` - Show Asterisk version
- `pjsip show endpoints` - Show PJSIP endpoints
- `dialplan show` - Show dialplan
- `manager show connected` - Show AMI connections

### Access provisioner container:

```bash
docker exec -it test-provisioner bash
```

### Check network connectivity:

```bash
docker-compose -f docker-compose.test.yml exec provisioner ping asterisk
```

## CI/CD Integration

The integration tests are run automatically in GitHub Actions on every push and pull request. See `.github/workflows/ci.yml` for the complete CI configuration.

## Troubleshooting

### Tests hang waiting for services
- Increase wait time in conftest.py
- Check Docker logs for errors
- Verify Docker has enough resources

### AMI connection failures
- Check Asterisk is fully started (takes ~10 seconds)
- Verify AMI credentials in manager.conf
- Check network connectivity between containers

### Config generation failures
- Verify shared volume is mounted correctly
- Check file permissions in container
- Look for errors in provisioner logs

### Port conflicts
- Ensure ports 5038, 5060, 8080 are not in use
- Modify docker-compose.test.yml to use different ports if needed
