import copy
import ckan.plugins.toolkit as t

# Custom user profile fields
CUSTOM_FIELDS = [
    {"name": "job_title", "default": None},
    {"name": "affiliation", "default": None},
]


def get_user_obj(context):
    if "user_obj" in context:
        user_obj = context["user_obj"]
    elif "model" in context and "user" in context:
        user_obj = context['model'].User.get(context['user'])

    if not user_obj:
        raise t.ObjectNotFound("No user object could be found")

    return user_obj


def init_plugin_extras(plugin_extras):
    out_dict = copy.deepcopy(plugin_extras)
    if not out_dict:
        out_dict = {}
    if "unaids" not in out_dict:
        out_dict["unaids"] = {}
    return out_dict


def add_to_plugin_extras(plugin_extras, data_dict):
    out_dict = copy.deepcopy(plugin_extras)
    for field in CUSTOM_FIELDS:
        out_dict["unaids"][field["name"]] = data_dict.get(field["name"], field["default"])
    return out_dict


def format_plugin_extras(plugin_extras):
    if not plugin_extras:
        plugin_extras = {}
    out_dict = {}
    for field in CUSTOM_FIELDS:
        out_dict[field["name"]] = plugin_extras.get(field["name"], field["default"])
    return out_dict
