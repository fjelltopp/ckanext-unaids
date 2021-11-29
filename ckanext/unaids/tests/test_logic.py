import pytest
from ckan.plugins import toolkit
from ckanext.unaids import logic


@pytest.mark.ckan_config('ckan.plugins', 'unaids authz_service blob_storage')
@pytest.mark.usefixtures('with_plugins')
@pytest.mark.parametrize(
    "lfs_prefix,sha256,size,valid",
    [
        ("fjelltopp/my-dataset", "acbac3b78f9ace071ca3a79f23fc788a1b7ee9dc547becc6404dbb1f58afff79", 100, True),
        (None, None, None, True),
        ("fjelltopp/my-dataset", "acbac3b78f9ace071ca3a79f23fc788a1b7ee9dc547becc6404dbb1f58afff79", None, False),
        (None, None, 100, False),
        ("fjelltopp/my-dataset", "", 100, False),
        ("fjelltopp/my-dataset", None, 100, False),
        ("", "acbac3b78f9ace071ca3a79f23fc788a1b7ee9dc547becc6404dbb1f58afff79", 100, False),
        ("", "invalid_sha256", 100, False),
        ("", "acbac3b78f9ace071ca3a79f23fc788a1b7ee9dc547becc6404dbb1f58afff79", 100, False),
        (None, "acbac3b78f9ace071ca3a79f23fc788a1b7ee9dc547becc6404dbb1f58afff79", 100, False),
        ("fjelltopp/my-dataset", "", 100, False)
    ], ids=[
        "validates if all upload fields correct",
        "validates if no upload fields present",
        "fails if size None",
        "fails if only size present",
        "fails if sha256 empty string",
        "fails if sha256 None",
        "fails if only sha256 present",
        "fails if invalid sha256",
        "fails if lfs_prefix empty string",
        "fails if lfs_prefix None",
        "fails if only lfs_prefix present"
    ])
def test_validate_resource_upload_fields(lfs_prefix, sha256, size, valid):
    context = {}
    resource_dict = {}
    for key, val in [('sha256', sha256), ('lfs_prefix', lfs_prefix), ('size', size)]:
        if val is not None:
            resource_dict[key] = val
    if not valid:
        with pytest.raises(toolkit.ValidationError):
            logic.validate_resource_upload_fields(context, resource_dict)
    else:
        logic.validate_resource_upload_fields(context, resource_dict)
