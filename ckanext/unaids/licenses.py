
from ckan.common import _
from ckan.model.license import DefaultLicense


class LicenseCreativeCommonsIntergovernmentalOrgs(DefaultLicense):
    id = "cc-by-igo"
    is_okd_compliant = False
    url = "http://creativecommons.org/licenses/by/3.0/igo/legalcode"

    @property
    def title(self):
        return _(
            "Creative Commons Attribution for Intergovernmental Organisations"
        )
