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
✅ FIXED - But revealed another issue (ReclineView removed)

---

### Issue 7: ckanext-reclineview removed in CKAN 2.11

**Error Message:**
```
ModuleNotFoundError: No module named 'ckanext.reclineview'
```

**Root Cause:**
- After fixing _identify_user_default, plugin.py tries to import ReclineViewBase
- The Recline-based view plugins were completely removed in CKAN 2.11
- ReclineViewBase from ckanext.reclineview.plugin no longer exists
- CKAN 2.11 recommends using DataTables-based views instead

**Solution Applied:**
- Removed import of ReclineViewBase from ckanext.reclineview.plugin (line 46)
- Changed UNAIDSReclineView to extend p.SingletonPlugin instead of ReclineViewBase
- Implemented IResourceView interface directly
- Added required methods:
  - view_template() - returns "datatables/datatables_view.html"
  - setup_template_variables() - sets up resource and view JSON data
- Kept existing info() and can_view() methods for compatibility

**Files Modified:**
- `ckanext/unaids/plugin.py`: Lines 46, 304-342

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

---

## Batch 2: SQLAlchemy 2.0 Compatibility

### Issue 8: SQLAlchemy 2.0 Table.exists() deprecated

**Error Message:**
```
Table object 'dataset_transfer_request' is not bound to an Engine or Connection.
Execution can not proceed without a database to execute against.
```

**Root Cause:**
- All 161 tests failing at setup in `unaids_setup` fixture
- `dataset_transfer/model.py` uses deprecated `Table.exists()` method without bind parameter
- SQLAlchemy 2.0 removed the ability to call `Table.exists()` without an engine binding
- Same issue with `Table.create()` method
- Modern SQLAlchemy uses the `inspect()` API to check table existence

**Solution Applied:**
- Added `inspect` to SQLAlchemy imports (line 1)
- Changed import from `ckan.model.meta import metadata, engine` to import the `meta` module itself (lines 5-6)
- Updated `init_tables()`: Changed `DatasetTransferRequest.__table__.create()` to `DatasetTransferRequest.__table__.create(bind=meta.engine)` with check to avoid recreating (lines 32-34)
- Updated `tables_exists()`: Changed `DatasetTransferRequest.__table__.exists()` to `DatasetTransferRequest.__table__.exists(bind=meta.engine)` (line 38)
- Using `meta.engine` ensures the engine is properly initialized by CKAN before being accessed

**Files Modified:**
- `ckanext/unaids/dataset_transfer/model.py`: Lines 1, 5-6, 32-38

**Result:**
⏳ PENDING - Waiting for test verification

---

### Issue 9: CKAN package_activity_list action removed

**Error Message:**
```
ckan.logic.NotFound: The action 'package_activity_list' is not found for chained action
```

**Root Cause:**
- After fixing SQLAlchemy issues, plugin loading fails
- Extension uses `@t.chained_action` to extend `package_activity_list`
- CKAN 2.11 removed the `package_activity_list` action entirely
- The extension added release names to activity lists via this chained action
- Tests and helpers depend on this action returning activity data

**Solution Applied:**
- Removed chained action approach (line 138 removed `@t.chained_action` decorator)
- Reimplemented `package_activity_list` as a standalone action (lines 136-169)
- New implementation:
  - Gets package activities directly from database using SQLAlchemy Session
  - Queries Activity model filtered by package object_id
  - Converts activities to dict format
  - Adds release names from dataset_version_list
  - Maintains backward compatibility with existing code
- Updated plugin.py to register the new action implementation (line 115)

**Files Modified:**
- `ckanext/unaids/actions.py`: Lines 136-169
- `ckanext/unaids/plugin.py`: Line 115

**Test Results After Fix:**
- Plugin loading now works
- 102 tests passing (up from 24)
- 18 errors remaining (down from 134)
- 41 failures
- Revealed issue with Activity.as_dict() accessing non-existent permission_labels column

**Result:**
✅ FIXED - But needs follow-up fix for Activity model

---

### Issue 10: Activity model permission_labels column missing

**Error Message:**
```
sqlalchemy.exc.ProgrammingError: column activity.permission_labels does not exist
```

**Root Cause:**
- After fixing package_activity_list, 18 errors occur when querying activities
- `Activity.as_dict()` tries to serialize all columns including `permission_labels`
- The `permission_labels` column doesn't exist in the Activity table schema
- This column might be for a newer CKAN feature not yet migrated

**Solution Applied:**
- Replaced `activity.as_dict()` with manual dictionary construction (lines 148-166)
- Only includes columns that actually exist in the Activity model:
  - id, timestamp, user_id, object_id, revision_id, activity_type, data
- Converts timestamp to ISO format for JSON serialization
- Avoids SQLAlchemy trying to access non-existent columns

**Files Modified:**
- `ckanext/unaids/actions.py`: Lines 148-166

**Result:**
⏳ PENDING - Waiting for test verification

---

### Issue 10 (Updated): Activity model permission_labels column missing

**Error Message:**
```
sqlalchemy.exc.ProgrammingError: column activity.permission_labels does not exist
```

**Root Cause:**
- Activity ORM model in CKAN 2.11 defines `permission_labels` column
- But database schema hasn't been migrated yet
- SQLAlchemy ORM queries try to SELECT all model columns including the missing one
- From PROGRESS_OLD.md: CKAN 2.11 moved activity features to ckanext.activity plugin

**Solution Applied:**
- Try to use `ckanext.activity.logic.action.package_activity_list` if available (lines 144-146)
- Fallback to raw SQL query if activity plugin not loaded (lines 147-173)
- Raw SQL only selects existing columns, avoiding ORM column mapping issues
- Added error handling for missing dataset_version_list action (lines 176-181)
- Maintains backward compatibility whether activity plugin is loaded or not

**Files Modified:**
- `ckanext/unaids/actions.py`: Lines 136-192

**Result:**
⏳ PENDING - Waiting for test verification

---

### Issue 10 (Final Fix): Activity plugin database migration required

**Error Message:**
```
sqlalchemy.exc.ProgrammingError: column activity.permission_labels does not exist
```

**Root Cause:**
- From PROGRESS_BLOB_STORAGE.md: Same issue encountered in blob-storage migration
- CKAN 2.11 moved activity to a plugin that requires database migration
- The `activity` table needs a `permission_labels` column added by migration
- Tests run `ckan db init` but not `ckan db upgrade`
- Plugin migrations must be explicitly run after db init

**Solution Applied:**
- Added `model.repo.upgrade_db()` call in conftest unaids_setup fixture (lines 12-13)
- Runs after `clean_db` to ensure all plugin migrations are applied
- This ensures the activity plugin's permission_labels column exists before tests run
- Uses CKAN's model API instead of CLI functions

**Files Modified:**
- `ckanext/unaids/tests/conftest.py`: Lines 12-13

**Result:**
⏳ PENDING - Waiting for test verification

---

### Issue 10 (Final Fix): Activity plugin permission_labels column via custom fixture

**Error Message:**
```
sqlalchemy.exc.ProgrammingError: column activity.permission_labels does not exist
```

**Root Cause:**
- From PROGRESS_FORK.md: Same issue, proper solution documented there
- CKAN 2.11 activity plugin requires `permission_labels text[]` column
- The `clean_db` fixture rebuilds database fresh for test isolation, wiping migrations
- Running `ckan db upgrade` in workflow doesn't help because `clean_db` runs after it
- Any Activity ORM query fails without this column

**Solution Applied:**
- Created `clean_db_with_migrations` fixture in conftest (lines 11-24)
- Extends `clean_db` by adding permission_labels column after database rebuild:
  ```sql
  ALTER TABLE activity ADD COLUMN IF NOT EXISTS permission_labels text[]
  ```
- Column type is `text[]` (array), not just `text`, as required by CKAN 2.11
- Changed `unaids_setup` to depend on `clean_db_with_migrations` instead of `clean_db` (line 28)
- Based on proven solution from ckanext-fork migration

**Files Modified:**
- `ckanext/unaids/tests/conftest.py`: Lines 3, 11-24, 28

**Test Results After Fix:**
- **Permission_labels errors: COMPLETELY ELIMINATED** ✅
- 102 tests passing (maintained)
- 18 errors remaining (different errors than before)
- 41 failures (maintained)
- Errors no longer related to Activity ORM/permission_labels

**Result:**
✅ FIXED - Activity plugin permission_labels column issue resolved

---

## Batch 3: Test Factory vs Action Issues

### Issue 11: factories.Dataset() doesn't create activities

**Error Message:**
```
ckan.logic.NotFound: Activity not found
```

**Root Cause:**
- 5 tests in test_actions_dataset_lock.py failing with "Activity not found"
- Tests use `factories.Dataset()` to create datasets
- Factories create database records directly without triggering actions
- Activities are only created when actual CKAN actions are called
- `dataset_version_create` action queries for activities but finds none
- Similar to CKAN 2.11 factory behavior documented in ckan2.11-specific.md

**Solution Applied:**
- Use `factories.Dataset()` to create dataset (factories are faster and cleaner)
- Call `package_patch` after factory to trigger activity creation
- **Added `activity` plugin to ckan.plugins config** - activities won't be created without it!
- Pattern from PROGRESS_FORK.md: `call_action('package_patch', context={'user': user['name']}, id=dataset['id'], notes='Trigger activity')`
- Updated both `locked_dataset` fixture and `test_version_already_created` method
- Added activity plugin to both TestDatasetLock and TestDatasetUnlock test classes

**Files Modified:**
- `ckanext/unaids/tests/test_actions_dataset_lock.py`: Lines 8-24, 27, 36-58, 61

**Result:**
⏳ PENDING - Waiting for test verification
---

### Issue 12: NameConflict with activity plugin's package_activity_list

**Error Message:**
```
ckan.logic.NameConflict: The action 'package_activity_list' is already implemented in 'unaids'
```

**Root Cause:**
- After adding `activity` plugin to test config (Issue 11), new error appeared
- Both unaids extension and activity plugin implement `package_activity_list` action
- CKAN doesn't allow two plugins to provide the same action unless one uses @chained_action
- Unaids implementation was standalone, not chained
- This causes NameConflict when activity plugin loads

**Solution Applied:**
- Changed `package_activity_list` to use `@t.chained_action` decorator (line 136)
- Now chains the activity plugin's implementation instead of replacing it
- Calls `original_action(context, data_dict)` to get activities from activity plugin
- Then adds release names as before
- Simplified implementation - no more direct database queries needed

**Files Modified:**
- `ckanext/unaids/actions.py`: Lines 136-161

**Test Results After Fix:**
- test_actions_dataset_lock TestDatasetLock: **3 tests PASSING** ✅
- test_actions_dataset_lock TestDatasetUnlock: 3 tests failing (needs same fix)
- Reduced errors in these specific tests from "Activity not found" to actual test logic

**Result:**
✅ PARTIAL SUCCESS - TestDatasetLock tests fixed, TestDatasetUnlock needs update

**Summary of Batch 3:**
- Issue 10: Activity permission_labels column → ✅ FIXED
- Issue 11: Activities not created by factories → ✅ FIXED (partial - TestDatasetLock only)
- Issue 12: NameConflict with activity plugin → ✅ FIXED

**Current Status:**
- Focus: Fix remaining 3 TestDatasetUnlock tests
- Then address other test errors related to activity plugin configuration

---

### Issue 13: Activity plugin not enabled in test.ini

**Error Message:**
```
ckan.logic.NotFound: The action 'package_activity_list' is not found for chained action
```

**Root Cause:**
- After fixing NameConflict in Issue 12 by using `@chained_action` decorator
- Chained actions require a base action to chain to
- The `activity` plugin provides the base `package_activity_list` action  
- But `activity` plugin was NOT configured in `test.ini`
- When plugins load, CKAN looks for base action to chain but finds nothing
- Similar to PROGRESS_BLOB_STORAGE.md Issue 10 - same root cause

**Analysis:**
- In CKAN 2.11, activity stream functionality moved from core to `activity` plugin
- Extension uses scheming configs → needs `scheming_datasets` plugin
- Extension uses authz_authorize action → needs `authz_service` plugin
- Extension itself needs to be loaded → needs `unaids` plugin
- Missing `ckan.plugins` line in test.ini meant no plugins were loaded

**Solution Applied:**
- Added `ckan.plugins` line to test.ini with required plugins
- Plugin list: `activity scheming_datasets authz_service unaids`
- This ensures all required plugin actions/hooks are available during tests
- Based on proven solution from PROGRESS_BLOB_STORAGE.md Issue 10

**Files Modified:**
- `test.ini`: Line 13 - Added ckan.plugins configuration

**Result:**
⏳ PENDING - Waiting for test verification

---

### Issue 14: SQLAlchemy 2.0 - UnboundExecutionError for dataset_transfer_request table

**Error Message:**
```
sqlalchemy.exc.UnboundExecutionError: Table object 'dataset_transfer_request' is not bound to an Engine or Connection
```

**Root Cause:**
- After fixing Issue 13 (activity plugin), tests now fail at plugin initialization
- Error in `plugin.py` line 93 when calling `tables_exists()`
- `DatasetTransferRequest.__table__.exists()` uses deprecated SQLAlchemy 1.x API
- SQLAlchemy 2.0+ requires explicit engine/connection binding for table operations
- The old `.exists(bind=engine)` method is deprecated and unreliable
- CKAN 2.11 uses SQLAlchemy 2.0+
- Similar issue documented in PROGRESS_OLD.md Issue 13

**Solution Applied:**
- Changed `tables_exists()` to use SQLAlchemy inspector API:
  ```python
  inspector = inspect(meta.engine)
  return DatasetTransferRequest.__tablename__ in inspector.get_table_names()
  ```
- Changed `init_tables()` to use `checkfirst=True` parameter:
  ```python
  DatasetTransferRequest.__table__.create(bind=meta.engine, checkfirst=True)
  ```
- Inspector API is the SQLAlchemy 2.0 recommended way to check table existence
- `checkfirst=True` avoids redundant table existence check

**Files Modified:**
- `ckanext/unaids/dataset_transfer/model.py`: Lines 32-38 - Updated table operations for SQLAlchemy 2.0

**Result:**
⏳ PENDING - Waiting for test verification

---

### Issue 15: meta.engine is None during plugin initialization

**Error Message:**
```
sqlalchemy.exc.NoInspectionAvailable: No inspection system is available for object of type <class 'NoneType'>
```

**Root Cause:**
- After fixing SQLAlchemy 2.0 compatibility in Issue 14, new error appeared
- `tables_exists()` is called from `plugin.py update_config()` during plugin initialization
- At that point, `meta.engine` is still `None` - database hasn't been initialized yet
- `inspect(None)` fails with NoInspectionAvailable error
- The `update_config()` hook runs very early in CKAN startup, before database connection

**Solution Applied:**
- Added check for `meta.engine is None` before inspection:
  ```python
  if meta.engine is None:
      return False
  ```
- Returns `False` when engine not ready, allowing plugin to load
- The warning message from `plugin.py` will log that tables need to be created
- Tables will be checked/created later when database is actually available

**Files Modified:**
- `ckanext/unaids/dataset_transfer/model.py`: Lines 36-38 - Added None check for meta.engine

**Result:**
⏳ PENDING - Waiting for test verification

---

### Issue 16: Missing ytp_request plugin for member_request_create chained action

**Error Message:**
```
ckan.logic.NotFound: The action 'member_request_create' is not found for chained action
```

**Root Cause:**
- After fixing Issue 15, plugin initialization proceeds further
- Now encounters `member_request_create` chained action in `custom_user_profile/actions.py`
- This action uses `@toolkit.chained_action` decorator
- The base `member_request_create` action is provided by `ytp-request` extension
- Without `ytp_request` plugin loaded, there's no base action to chain to

**Solution Applied:**
- Added `ytp_request` to plugin list in `test.ini`
- Updated plugins: `activity scheming_datasets authz_service ytp_request unaids`
- This provides the base `member_request_create` action for chaining

**Files Modified:**
- `test.ini`: Line 13 - Added ytp_request plugin

**Result:**
⏳ PENDING - Waiting for test verification

---

### Issue 17 (FINAL): Use direct import instead of chained action for package_activity_list

**Problem Evolution:**
1. `@chained_action` → "not found for chained action" (activity plugin not loaded)
2. Added activity plugin → Still "not found for chained action"  
3. Removed `@chained_action` → "already implemented in activity" (NameConflict)
4. Restored `@chained_action` → Back to "not found for chained action" (circular)

**Root Cause:**
- The activity plugin's `package_activity_list` action is NOT registered in a way that supports chaining
- Using `@chained_action` decorator doesn't work - causes circular errors
- But unaids DOES need to provide this action with release_name added for tests to pass

**Solution Applied (New Approach):**
- Removed `@chained_action` decorator completely
- Implemented as regular action that directly imports from activity plugin if available:
  ```python
  try:
      from ckanext.activity.logic.action import package_activity_list as activity_plugin_action
      activity_list = activity_plugin_action(context, data_dict)
  except ImportError:
      # Fallback to direct database query
  ```
- Registers as normal action (replaces activity plugin's action if both loaded)
- Plugin load order ensures unaids loads AFTER activity, so unaids version wins
- Adds release_name to activities from dataset_version_list

**Files Modified:**
- `ckanext/unaids/actions.py`: Lines 136-174 - Changed to direct import approach
- `ckanext/unaids/plugin.py`: Line 115 - Re-registered package_activity_list

**Result:**
⏳ PENDING - Waiting for test verification

---

### Issue 18: g.userobj AttributeError during request identification

**Error Message:**
```
AttributeError: '_Globals' object has no attribute 'userobj'
```

**Root Cause:**
- `plugin.py identify()` method accesses `toolkit.g.userobj` directly
- During early request processing in tests, `g.userobj` may not be set yet
- CKAN 2.11 Flask g object doesn't have `userobj` as a fallback attribute
- Similar issue in `after_saml2_login()` method

**Solution Applied (based on PROGRESS_RESTRICTED.md pattern):**
- Changed `toolkit.g.userobj` to `getattr(toolkit.g, 'userobj', None)`
- Updated both `identify()` and `after_saml2_login()` methods
- Safe access pattern avoids AttributeError when userobj not set

**Files Modified:**
- `ckanext/unaids/plugin.py`: Lines 277-281 - Use getattr for safe userobj access
- `ckanext/unaids/plugin.py`: Lines 286-290 - Same fix in after_saml2_login

**Result:**
⏳ PENDING - Waiting for test verification

---

### Issue 19: member_request_create chained action missing base action

**Error Message:**
```
ckan.logic.NotFound: The action 'member_request_create' is not found for chained action
```
AND after attempted fix:
```
ckan.logic.NameConflict: The action 'member_request_create' is already implemented in 'ytp_request'
```

**Root Cause:**
- `custom_user_profile/actions.py` uses `@toolkit.chained_action` for `member_request_create`
- The base action is provided by `ytp_request` plugin
- One test class (`test_helpers.py`) was missing `ytp_request` in `ckan.plugins` config
- When plugin not loaded, chained action fails at load time

**Solution Applied (proper fix - update all test configs):**
- **Keep** `@toolkit.chained_action` decorator (it's the proper CKAN pattern)
- **Keep** function signature as `(next_action, context, data_dict)`
- **Add** `ytp_request` to ALL test classes that override `ckan.plugins`
- Searched all test files: only `test_helpers.py` was missing `ytp_request`
- Updated `test_helpers.py` line 6: Added `ytp_request` to plugin list

**Files Modified:**
- `ckanext/unaids/custom_user_profile/actions.py`: Restored `@toolkit.chained_action` decorator
- `ckanext/unaids/plugin.py`: Reverted to simple action registration
- `ckanext/unaids/tests/test_helpers.py`: Line 6 - Added `ytp_request` to plugin list

**Result:**
⏳ PENDING - Waiting for test verification
