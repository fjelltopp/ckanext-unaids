# Migration Progress: ckanext-unaids to CKAN 2.11 + Python 3.10

## Overview
Migrating ckanext-unaids from CKAN 2.9/2.10 to CKAN 2.11 with Python 3.10 support.

Branch: `toavina/ckan-211-python310-migration`

Test Environment: Docker-based (docker-compose.test.yml)
Test Command: `./run-docker-tests.sh`

---

## Initial Status

**Test Results Before Migration:**
- Collection errors: 6
- Errors in:
  - test_auth_logic.py (Flask _request_ctx_stack)
  - test_blueprints.py (numpy/pandas incompatibility)
  - test_dataset_releases.py (nose framework)
  - test_dataset_transfer.py (mock module)
  - test_plugin.py (mock module)
  - test_validators.py (mock module)

---

## Batch 1: Import and Dependency Fixes

### Issue 1: Flask _request_ctx_stack removed in Flask 2.2+

**Error Message:**
```
ImportError: cannot import name '_request_ctx_stack' from 'flask'
```

**Root Cause:**
- Flask 2.2+ removed the deprecated `_request_ctx_stack` API
- Code was using `_request_ctx_stack.top.current_user` to store user data in request context
- CKAN 2.11 uses Flask 2.2+

**Solution Applied:**
- Removed `_request_ctx_stack` from Flask imports (line 8)
- Changed `_request_ctx_stack.top.current_user = payload` to `g.current_user = payload` (line 97)
- Flask's `g` object is the recommended way for request-scoped storage in Flask 2.2+

**Files Modified:**
- `ckanext/unaids/auth_logic.py`: Lines 8, 97

**Test Results After Fix:**
- Collection errors: 5 (down from 6)
- test_auth_logic.py: ✅ FIXED - No longer has import error
- Coverage improved: auth_logic.py 6% → 28%

**Result:**
✅ FIXED

---

## Current Status

**Remaining Collection Errors: 3**
1. test_dataset_transfer.py - mock module missing
2. test_plugin.py - mock module missing
3. test_validators.py - mock module missing

**Next Issue:**
Issue 5: mock module deprecated (Python 3)

---

### Issue 5: Deprecated mock module (Python 3)

**Error Message:**
```
ModuleNotFoundError: No module named 'mock'
```

**Root Cause:**
- Three test files using standalone `mock` package
- In Python 3.3+, mock is built-in as `unittest.mock`
- Standalone mock package is obsolete and not installed

**Solution Applied:**
- Replaced `import mock` with `from unittest import mock`
- Replaced `from mock import X` with `from unittest.mock import X`
- All mock functionality is identical, just different import path

**Files Modified:**
- `ckanext/unaids/tests/test_dataset_transfer.py`: Line 6
- `ckanext/unaids/tests/test_plugin.py`: Line 3
- `ckanext/unaids/tests/test_validators.py`: Line 15

**Test Results After Fix:**
- Collection errors: 1 (down from 3)
- test_dataset_transfer.py: ✅ FIXED
- test_validators.py: ✅ FIXED
- Coverage improved: test_dataset_transfer.py 5% → 23%, test_validators.py 21% → 51%
- Total collected tests increased: 121 → 148 (27 new tests)
- Overall coverage: 26% → 28%

**Result:**
✅ FIXED - But revealed another issue (_identify_user_default import in plugin.py)

---

### Issue 6: CKAN _identify_user_default removed from ckan.views

**Error Message:**
```
ImportError: cannot import name '_identify_user_default' from 'ckan.views'
```

**Root Cause:**
- After fixing mock imports, test_plugin.py now imports plugin.py
- plugin.py imports `_identify_user_default` from `ckan.views`
- CKAN 2.11 removed `_identify_user_default` from ckan.views module
- This was a private method for user identification
- CKAN 2.11 middleware now handles user identification automatically

**Solution Applied:**
- Removed `from ckan.views import _identify_user_default` import (line 16)
- Removed `initialize_g_userobj_using_private_core_ckan_method()` helper function (lines 65-66)
- Removed call to helper function in `identify()` method (line 282)
- Added comment explaining CKAN 2.11 middleware populates g.userobj automatically

**Files Modified:**
- `ckanext/unaids/plugin.py`: Lines 16, 65-66, 277-278

**Result:**
⏳ PENDING - Waiting for test verification

---

### Issue 3: nose framework deprecated

**Error Message:**
```
ModuleNotFoundError: No module named 'nose'
```

**Root Cause:**
- test_dataset_releases.py uses deprecated nose testing framework
- Imports: `from nose.tools import assert_equals, assert_in, assert_not_in`
- CKAN 2.11 uses pytest instead of nose
- nose has been unmaintained since 2015

**Solution Applied:**
- Removed `from nose.tools import assert_equals, assert_in, assert_not_in` import
- Replaced all nose assertions with pytest equivalents:
  - `assert_equals(a, b)` → `assert a == b` (2 occurrences)
  - `assert_in(item, container)` → `assert item in container` (22 occurrences)
  - `assert_not_in(item, container)` → `assert item not in container` (3 occurrences)

**Files Modified:**
- `ckanext/unaids/tests/test_dataset_releases.py`: Lines 13, 36-37, 73, 84, 96, 107, 119-120, 132, 160, 173, 198, 217, 223-224, 229-230, 237, 244, 250, 273-275, 285-286, 296-298

**Result:**
✅ FIXED - But revealed another issue (before_request import)

---

### Issue 4: CKAN before_request removed from ckan.views.user

**Error Message:**
```
ImportError: cannot import name 'before_request' from 'ckan.views.user'
```

**Root Cause:**
- After fixing nose framework, test_dataset_releases.py now imports blueprints
- user_info_blueprint.py imports `before_request` from `ckan.views.user`
- CKAN 2.11 removed `before_request` function from ckan.views.user module
- User identification is now handled automatically by CKAN middleware

**Solution Applied:**
- Removed `from ckan.views.user import before_request` import (line 6)
- Removed `user_info_blueprint.before_request(before_request)` call (line 18)
- Added comment explaining CKAN 2.11 middleware handles user identification

**Files Modified:**
- `ckanext/unaids/blueprints/user_info_blueprint.py`: Lines 6, 17-18

**Test Results After Fix:**
- Collection errors: 3 (down from 4)
- test_dataset_releases.py: ✅ FIXED - Now loading properly
- Coverage improved: test_dataset_releases.py 4% → 26%
- Coverage improved: blueprints/__init__.py 30% → 100%
- Total collected tests increased: 103 → 121 (18 new tests from test_dataset_releases.py)

**Result:**
✅ FIXED

---

### Issue 2: numpy/pandas binary incompatibility

**Error Message:**
```
ValueError: numpy.dtype size changed, may indicate binary incompatibility. Expected 96 from C header, got 88 from PyObject
```

**Root Cause:**
- pandas 2.0.3 was compiled against numpy<2.0
- Docker container has numpy 2.x installed
- Binary ABI mismatch between pandas build and current numpy version

**Solution Applied:**
- Updated pandas from 2.0.3 to 2.2.0 in requirements.txt
- pandas 2.2.0 supports numpy 2.x and was built against it

**Files Modified:**
- `requirements.txt`: Line 6 - Updated pandas version

**Test Results After Fix:**
- Collection errors: 4 (down from 5)
- test_blueprints.py: ✅ FIXED - No longer has numpy/pandas error
- Coverage improved: test_blueprints.py 9% → 49%
- Total collected tests increased: 96 → 103 (test_blueprints.py now loading)

**Result:**
✅ FIXED
