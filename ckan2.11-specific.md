# CKAN 2.11 Migration Guide

This document captures breaking changes and migration requirements when upgrading CKAN extensions from 2.9/2.10 to 2.11.

## Critical Breaking Changes

### 1. IDatasetForm Parent Class Order

**BREAKING CHANGE**: The order of parent classes for IDatasetForm plugins must be reversed.

**CKAN 2.10 and earlier:**
```python
class MyPlugin(plugins.SingletonPlugin, toolkit.DefaultDatasetForm):
    plugins.implements(plugins.IDatasetForm)
```

**CKAN 2.11 and later:**
```python
class MyPlugin(toolkit.DefaultDatasetForm, plugins.SingletonPlugin):
    plugins.implements(plugins.IDatasetForm)
```

**Why this matters:**
- Python's Method Resolution Order (MRO) depends on parent class order
- Wrong order causes `create_package_schema()`, `update_package_schema()`, and `show_package_schema()` to not be called properly
- Validators defined in these methods won't be applied to datasets
- Custom fields won't be validated or saved correctly

**Symptoms of this issue:**
- Custom validators don't trigger ValidationError as expected
- Custom fields are accepted but validation logic doesn't run
- Test factories (e.g., `factories.Dataset()`) bypass custom schemas

**Fix:**
Put `DefaultDatasetForm` first in the inheritance list.

### 2. Validator Function Restrictions

**BREAKING CHANGE**: Built-in Python functions can no longer be used directly as validators.

**What changed:**
- You cannot use `str()`, `bool()`, `int()`, `unicode()` (old Python 2), or other built-in callables directly as validators
- Object constructors and built-in functions must be wrapped

**Before (CKAN 2.10):**
```python
schema['field'] = [str, int]  # This worked
```

**After (CKAN 2.11):**
```python
def str_validator(value):
    try:
        return str(value)
    except Exception as e:
        raise toolkit.Invalid(str(e))

schema['field'] = [str_validator]  # Must use wrapper
```

**Why:** CKAN 2.11 requires validators to raise `toolkit.Invalid` for validation errors, and built-in functions raise different exceptions.

### 3. Configuration Validation (Strict Mode)

**CHANGE**: CKAN 2.11 defaults to strict configuration validation mode.

**What this means:**
- CKAN will not start unless all config options are valid
- All config options must have validators defined in configuration declarations
- Invalid config values will prevent application startup

**Impact:**
- Extensions must properly declare and validate their config options
- Missing or invalid validators will cause startup failures
- More explicit error messages during development

### 4. Python 3.10 Compatibility

**REQUIREMENT**: Extensions must be Python 3.10 compatible.

**Common migration issues:**

#### collections.abc imports
```python
# Python 3.9 and earlier (still works but deprecated)
from collections import Iterable, Mapping

# Python 3.10+ (required)
from collections.abc import Iterable, Mapping
from collections import defaultdict  # Non-abstract types stay in collections
```

**Fix for external dependencies:**
If dependencies aren't Python 3.10 compatible, add post-install patches:
```yaml
# In .github/workflows/test.yaml or similar
- name: Fix Python 3.10 compatibility
  run: |
    sed -i 's/from collections import Iterable/from collections.abc import Iterable/' \
        /path/to/problematic/file.py
```

### 5. Removed/Deprecated Plugins

**REMOVED**: Several plugins were removed in CKAN 2.11:

- `recline_view` - Remove from `ckan.plugins` in config files
- Other legacy view plugins may also be deprecated/removed

**Action required:**
- Remove deprecated plugins from `test.ini`, `production.ini`, `development.ini`
- Update CI/CD configuration files
- Check CKAN 2.11 changelog for complete list

## Dependency Updates

### Required Version Bumps

When migrating to CKAN 2.11, update these common dependencies:

```txt
# Minimum versions for CKAN 2.11 compatibility
typing-extensions>=4.6.0  # Was 4.2.0 in older versions
click>=8.1.3              # Was 8.1.2
requests>=2.30.0          # Was 2.27.1
urllib3>=2.2.2            # Was 1.26.9
certifi>=2024.7.4         # Was 2021.10.8
charset-normalizer>=3.3.2 # Was 2.0.12
python-dateutil>=2.9.0    # Was 2.8.2
pluggy>=1.5.0             # Was 0.13.1 (required for pytest-cov)
```

**pytest and pluggy:**
- `pytest-cov>=6.0.0` requires `pluggy>=1.0.0`
- Old `pluggy==0.13.1` causes: `TypeError: HookimplMarker.__call__() got an unexpected keyword argument 'wrapper'`

## Testing Considerations

### Factory Behavior - CRITICAL CHANGE

**IMPORTANT**: Test factories are NOT meant for testing validation!

According to CKAN testing documentation:
> "These are not meant to be used for the actual testing, e.g. if you're writing a test for the user_create function then call call_action, don't test it via the User factory"

**Key points:**
- `factories.Dataset()`, `factories.Resource()`, etc. are for **test data setup only**
- Factories intentionally bypass validation to make test setup easier
- **DO NOT use factories to test schema validation**
- **DO use `helpers.call_action()` to test actions and validation**

### Correct Validator Testing Pattern

**WRONG** - Using factories to test validation:
```python
@pytest.mark.usefixtures("clean_db")
def test_my_validation():  # ❌ This will fail!
    with pytest.raises(toolkit.ValidationError):
        factories.Dataset(my_field='invalid_value')  # Bypasses validation!
```

**CORRECT** - Using call_action to test validation:
```python
@pytest.mark.usefixtures("clean_db")
def test_my_validation():  # ✅ This works!
    with pytest.raises(toolkit.ValidationError):
        helpers.call_action(
            'package_create',
            name='test-dataset',
            my_field='invalid_value'
        )
```

### Testing Strategy

Test validators at two levels:

**1. Unit Tests** - Test validators directly:
```python
def test_my_validator_unit():
    """Test validator function in isolation"""
    with pytest.raises(Invalid):
        validators.my_validator('invalid_value')
```

**2. Integration Tests** - Test via actions:
```python
@pytest.mark.usefixtures("clean_db")
def test_my_validator_integration():
    """Test validator through package_create action"""
    with pytest.raises(toolkit.ValidationError):
        helpers.call_action(
            'package_create',
            name='test-dataset',
            my_field='invalid_value'
        )
```

**3. Use Factories for Setup** - When you need test data:
```python
@pytest.mark.usefixtures("clean_db")
def test_some_feature():
    """Use factories to create test data for the actual test"""
    # Use factory to quickly create valid test data
    dataset = factories.Dataset(
        resources=[{
            'url': 'http://example.com',
            'format': 'CSV'
        }]
    )

    # Now test your actual feature
    result = my_feature_function(dataset['id'])
    assert result == expected_value
```

## Migration Checklist

When migrating a CKAN extension to 2.11:

- [ ] Swap IDatasetForm parent class order (DefaultDatasetForm first)
- [ ] Update `package_types()` to return explicit list (e.g., `['dataset']`) instead of `[]`
- [ ] Update `is_fallback()` to return `False` if using explicit package_types
- [ ] Check all validator functions - wrap any built-in functions
- [ ] Update dependencies to CKAN 2.11 compatible versions
- [ ] Fix Python 3.10 compatibility issues (collections.abc imports)
- [ ] Remove deprecated plugins from config files (recline_view, etc.)
- [ ] Update pluggy to >=1.5.0 if using pytest-cov
- [ ] Test with factories to ensure schemas are applied
- [ ] Update CI/CD workflows for CKAN 2.11 environment

## References

- [CKAN 2.11 Official Changelog](https://docs.ckan.org/en/2.11/changelog.html)
- [CKAN 2.11 IDatasetForm Documentation](https://docs.ckan.org/en/2.11/extensions/adding-custom-fields.html)
- [CKAN 2.9 to 2.10 Migration Tips](https://github.com/ckan/ckan/wiki/CKAN-2.9-to-2.10-migration-tips)
- [CKAN Extensions Best Practices](https://docs.ckan.org/en/2.11/extensions/best-practices.html)

## Known Issues and Workarounds

### Issue: External Dependencies Not Python 3.10 Compatible

**Example**: ckanext-authz-service has Python 3.9 code

**Workaround**: Add post-install patch in CI/CD:
```bash
# Fix collections import in ckanext-authz-service
sed -i 's/from collections import Iterable, defaultdict/from collections.abc import Iterable\nfrom collections import defaultdict/' \
    /path/to/site-packages/ckanext/authz_service/authzzie.py
```

**Long-term**: Request upstream fix or use Python 3.10 compatible fork

---

## 6. API Authentication Changes (API Keys → JWT Tokens)

**BREAKING CHANGE**: CKAN 2.11 switches from API keys to JWT-based API tokens for authentication.

### The Change

**CKAN 2.10 and earlier:**
- Used simple API key authentication
- API keys stored in `user['apikey']` field
- Created automatically with user accounts
- Sent in `Authorization` header as plain string

**CKAN 2.11:**
- Uses JWT (JSON Web Token) based authentication by default
- Tokens stored in `user['token']` field (NOT `apikey`)
- Must be explicitly created via `APIToken` factory
- Provides improved security: signatures, expiration, claims
- Legacy API keys still supported for backward compatibility

### Impact on Tests

Tests that make HTTP API requests will fail with **403 FORBIDDEN** if using old patterns:

**Error messages you might see:**
```
assert 403 == 200
Cannot decode JWT token: Not enough segments
```

### Migration Pattern

#### OLD Pattern (CKAN 2.10):
```python
def test_api_call(self, app):
    user = factories.Sysadmin()
    headers = {'Authorization': user['apikey']}  # ❌ Fails in 2.11
    
    response = app.post(
        url='/api/3/action/resource_update',
        headers=headers,
        data={'id': 'some-id'}
    )
    assert response.status_code == 200
```

#### NEW Pattern (CKAN 2.11):
```python
def test_api_call(self, app):
    user = factories.SysadminWithToken()  # ✅ Creates user with token
    headers = {'Authorization': user['token']}  # ✅ Use 'token' not 'apikey'
    
    response = app.post(
        url='/api/3/action/resource_update',
        headers=headers,
        data={'id': 'some-id'}
    )
    assert response.status_code == 200
```

### Available Factory Classes

CKAN 2.11 provides two new factory classes for testing with API tokens:

**1. UserWithToken** - Regular user with API token:
```python
user = factories.UserWithToken()
print(user['token'])  # JWT token string
print(user['password'])  # 'correct123' (default password)
```

**2. SysadminWithToken** - Sysadmin user with API token:
```python
user = factories.SysadminWithToken()
print(user['token'])  # JWT token string
print(user['sysadmin'])  # True
print(user['password'])  # 'correct123'
```

### How It Works

From CKAN core `ckan/tests/factories.py`:

```python
class SysadminWithToken(Sysadmin):
    """A factory class for creating CKAN sysadmin users
    with an associated API token.
    """
    password = "correct123"

    @factory.post_generation
    def token(obj, create, extracted, **kwargs):
        if not create:
            return
        # Creates APIToken and stores it in user dict
        api_token = APIToken(user=obj["id"])
        obj["token"] = api_token["token"]
```

**What happens:**
1. Creates sysadmin user via parent `Sysadmin` factory
2. Post-generation hook creates an `APIToken` for the user
3. Token (JWT string) stored in `obj["token"]`
4. Token can be used immediately in Authorization headers

### JWT Token Benefits

**Why CKAN switched to JWT:**
- **Security**: Tokens are cryptographically signed
- **Expiration**: Tokens can have time-based validity
- **Stateless**: No server-side session storage needed
- **Claims**: Tokens carry user identity and permissions
- **Integration**: Better compatibility with modern auth systems

### Testing Patterns

**Pattern 1: Simple authenticated request**
```python
def test_authenticated_action(self, app):
    user = factories.UserWithToken()
    response = app.post(
        '/api/3/action/package_create',
        headers={'Authorization': user['token']},
        json={'name': 'test-dataset'}
    )
    assert response.status_code == 200
```

**Pattern 2: File upload with authentication**
```python
def test_file_upload(self, app):
    user = factories.SysadminWithToken()
    files = {'upload': (io.BytesIO(b'data'), 'file.txt')}
    response = app.post(
        '/api/3/action/resource_update',
        headers={'Authorization': user['token']},
        data={'id': resource_id},
        upload_files=files
    )
    assert response.status_code == 200
```

**Pattern 3: Testing unauthorized access**
```python
def test_requires_auth(self, app):
    # Don't provide token - should get 403
    response = app.post(
        '/api/3/action/package_create',
        json={'name': 'test'}
    )
    assert response.status_code == 403
```

### Configuration

The authentication header name can be configured in `ckan.ini`:

```ini
# Default in CKAN 2.11
apitoken_header_name = Authorization

# Alternative (if you prefer X-CKAN-API-Key header)
apitoken_header_name = X-CKAN-API-Key
```

Most setups use `Authorization` as it's the HTTP standard.

### Backward Compatibility

CKAN 2.11 still supports legacy API keys for backward compatibility:
- Existing API keys continue to work
- New integrations should use JWT tokens
- Old `factories.Sysadmin()['apikey']` won't work for NEW users
- Migration to JWT recommended for new development

### Common Errors and Solutions

**Error: `KeyError: 'apikey'`**
```python
# ❌ Problem
user = factories.Sysadmin()
token = user['apikey']  # KeyError in CKAN 2.11

# ✅ Solution
user = factories.SysadminWithToken()
token = user['token']
```

**Error: `403 FORBIDDEN` with "Cannot decode JWT token"**
```python
# ❌ Problem: Using wrong field or no token
headers = {'Authorization': user['apikey']}  # Wrong field

# ✅ Solution: Use token field
headers = {'Authorization': user['token']}
```

**Error: `assert 403 == 200` in API tests**
```python
# ❌ Problem: No authentication
user = factories.Sysadmin()  # No token created

# ✅ Solution: Use factory with token
user = factories.SysadminWithToken()
```

### Migration Checklist for API Tests

When updating tests that make HTTP API calls:

- [ ] Identify all uses of `factories.User()` or `factories.Sysadmin()` in API tests
- [ ] Change to `factories.UserWithToken()` or `factories.SysadminWithToken()`
- [ ] Change `user['apikey']` to `user['token']`
- [ ] Verify Authorization header format (usually just the token string)
- [ ] Test that 403s become 200s after the fix
- [ ] Document the change with comments explaining CKAN 2.11 migration

### References

- **CKAN 2.11 API Guide**: https://docs.ckan.org/en/2.11/api/
- **CKAN 2.11 Changelog**: https://docs.ckan.org/en/2.11/changelog.html
- **CKAN Core factories.py**: https://github.com/ckan/ckan/blob/dev-v2.11/ckan/tests/factories.py
- **Auth Header Issue**: https://github.com/ckan/ckan/issues/7408
- **API Token Discussion**: https://github.com/ckan/ckan/issues/8637

### Real-World Example

From `ckanext-fork` migration (January 2025):

**Before (failing with 403):**
```python
def test_fork_resource_update_with_new_non_fork_resource_details_via_api_call(self, app, forked_data):
    user = factories.Sysadmin()  # No token
    headers = {'Authorization': user['apikey']}  # Wrong field
    
    response = app.post(url, headers=headers, data=files)
    assert response.status_code == 200  # ❌ Gets 403
```

**After (passing with 200):**
```python
def test_fork_resource_update_with_new_non_fork_resource_details_via_api_call(self, app, forked_data):
    user = factories.SysadminWithToken()  # ✅ Creates token
    headers = {'Authorization': user['token']}  # ✅ Correct field
    
    response = app.post(url, headers=headers, data=files)
    assert response.status_code == 200  # ✅ Works!
```

---

*Document created during ckanext-blob-storage migration to CKAN 2.11 (January 2025)*
*Updated with API authentication details during ckanext-fork migration (January 2025)*
