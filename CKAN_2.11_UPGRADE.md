# CKAN 2.11 Upgrade Guide for ckanext-unaids

This document outlines the requirements and steps needed when upgrading a CKAN instance running ckanext-unaids to CKAN 2.11 with Python 3.10.

## Prerequisites

- CKAN 2.11
- Python 3.10
- PostgreSQL 13+ (recommended)
- Solr 9 with CKAN 2.11 schema

## Docker Stack Updates

### Container Images

Update your docker-compose.yml to use CKAN 2.11 compatible images:

```yaml
services:
  ckan:
    image: ckan/ckan-dev:2.11-py3.10
    # or for production: ckan/ckan-base:2.11-py3.10

  solr:
    image: ckan/ckan-solr:2.11-solr9

  postgres:
    image: ckan/ckan-postgres-dev:2.11
    # or for production: postgres:13-alpine

  redis:
    image: redis:7-alpine
```

## Required Dependency Extensions

Ensure the following extensions are also updated to CKAN 2.11 compatible versions:

| Extension | Notes |
|-----------|-------|
| ckanext-scheming | Required for dataset schemas |
| ckanext-validation | Required for resource validation |
| ckanext-versions | Required for dataset versioning/releases |
| ckanext-blob-storage | Required for LFS/Giftless file storage |
| ckanext-authz-service | Required for authorization service |
| ckanext-ytp-request | Required for membership requests |
| ckanext-pages | Required for static pages |

## Python Package Dependencies

The following packages are required (see requirements.txt):

```
giftless-client==0.1.1
frictionless>=5.0.0
tableschema>=1.21.0
```

## Database Migrations

### Automatic Migrations

CKAN 2.11 will run database migrations automatically on startup. Ensure you run:

```bash
ckan db upgrade
```

### Activity Plugin Migration

The activity plugin in CKAN 2.11 requires a `permission_labels` column in the activity table. This is added automatically by the activity plugin migration, but ensure it exists:

```sql
ALTER TABLE activity ADD COLUMN IF NOT EXISTS permission_labels text[];
```

### Extension-Specific Tables

Ensure the following extension tables are created:

1. **ckanext-validation**: Validation results table
2. **ckanext-versions**: Dataset versions table
3. **ckanext-unaids**: Dataset transfer table

Run extension migrations:

```bash
ckan unaids init-db
```

## Configuration Changes

### Plugin Order

The plugin order matters. Recommended order in your ckan.ini:

```ini
ckan.plugins = activity scheming_datasets scheming_groups scheming_organizations
               validation authz_service blob_storage versions
               ytp_request pages unaids
```

### Required Configuration Options

```ini
# Scheming configuration
scheming.dataset_schemas = ckanext.unaids:dataset_schemas/dataset.json
scheming.presets = ckanext.unaids:presets.json
                   ckanext.scheming:presets.json

# Resource formats (for custom file types like .pjnz)
ckan.resource_formats = /path/to/ckanext-unaids/ckanext/unaids/resource_formats.json

# Schema directory for table schemas
ckanext.unaids.schema_directory = /path/to/schemas

# Auth0/OAuth2 configuration (if using)
ckanext.unaids.auth0_domain = your-domain.auth0.com
ckanext.unaids.oauth2_api_audience = https://your-api-audience
ckanext.unaids.oauth2_required_scope = access:adr

# Blob storage / Giftless configuration
ckanext.blob_storage.storage_service_url = https://your-giftless-server
ckanext.authz_service.jwt_algorithm = RS256
ckanext.authz_service.jwt_private_key_file = /path/to/private-key.pem
```

## Breaking Changes in CKAN 2.11

### 1. Activity Plugin User Context

All API calls that create or modify data now require a user context. If you have custom code calling CKAN actions:

```python
# Before (CKAN 2.10)
toolkit.get_action('package_create')(context, data_dict)

# After (CKAN 2.11) - context must include 'user'
context = {'user': 'username'}
toolkit.get_action('package_create')(context, data_dict)
```

### 2. IResourceController Interface Changes

If you have custom plugins implementing IResourceController:

| Old Method | New Method |
|------------|------------|
| `before_create` | `before_resource_create` |
| `before_update` | `before_resource_update` |
| `before_show` | `before_resource_show` |
| N/A | `after_resource_update` (new) |

### 3. Flask Request Context

`_request_ctx_stack` has been removed. Use `flask.g` for request-scoped storage:

```python
# Before
from flask import _request_ctx_stack
ctx = _request_ctx_stack.top

# After
from flask import g, has_request_context
if has_request_context():
    # Use flask.g for storage
```

### 4. SQLAlchemy 2.0 Compatibility

Table operations now require explicit engine parameter:

```python
# Before
table.exists()
table.create()

# After
from ckan.model.meta import engine
table.exists(bind=engine)
table.create(bind=engine)
```

## Testing the Upgrade

1. **Backup your database** before upgrading

2. **Run tests** to verify the extension works:
   ```bash
   pytest --ckan-ini=test.ini ckanext/unaids/tests/
   ```

3. **Expected results**: 160 passed, 1 skipped
   - The skipped test (`test_giftless_resource_create`) requires a running Giftless server

## Troubleshooting

### Common Issues

1. **"User not found" errors in tests or API calls**
   - Ensure user context is passed to all action calls

2. **"Activity not found" or missing activity entries**
   - Check that the activity plugin is loaded and migrations are run

3. **Scheming validation errors**
   - Verify scheming.presets includes all required preset files
   - Check dataset type matches the scheming schema

4. **Foreign key violations during tests**
   - This is usually a test isolation issue, not a production concern

### Logs to Check

- CKAN logs: `/var/log/ckan/ckan.log`
- uWSGI/Gunicorn logs
- PostgreSQL logs for database errors

## Rollback Procedure

If issues occur:

1. Restore database from backup
2. Revert to previous CKAN version containers
3. Revert extension code to previous version

## Support

For issues specific to this migration, check:
- [PROGRESS.md](./PROGRESS.md) for detailed migration notes
- [ckan2.11-specific.md](./ckan2.11-specific.md) for CKAN 2.11 breaking changes
