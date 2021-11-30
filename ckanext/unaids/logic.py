from ckan.plugins import toolkit


def validate_resource_upload_fields(context, resource_dict):
    upload_has_sha256 = "sha256" in resource_dict
    upload_has_lfs_prefix = "lfs_prefix" in resource_dict
    upload_has_size = "size" in resource_dict
    valid_blob_storage_upload = (upload_has_sha256 == upload_has_lfs_prefix == upload_has_size)
    no_upload_fields_present = not any([upload_has_sha256, upload_has_lfs_prefix, upload_has_size])
    if not valid_blob_storage_upload:
        raise toolkit.ValidationError(
            ["Invalid blob storage upload fields. sha256, size and lfs_prefix needs to be provided."])
    elif no_upload_fields_present:
        return None
    else:
        sha256 = resource_dict.get("sha256")
        lfs_prefix = resource_dict.get("lfs_prefix")
        try:
            toolkit.get_validator('valid_sha256')(sha256)
            toolkit.get_validator('valid_lfs_prefix')(lfs_prefix)
        except toolkit.Invalid as err:
            raise toolkit.ValidationError([err.error])
