import pytest
from unittest.mock import patch
from ckan.tests import factories
from ckan.plugins import toolkit
from markupsafe import Markup


@pytest.mark.ckan_config('ckan.plugins', 'activity ytp_request unaids scheming_datasets versions')
@pytest.mark.ckan_config('scheming.dataset_schemas', 'ckanext.unaids.tests.test_scheming_schemas:test_schema.json')
@pytest.mark.ckan_config('scheming.presets', 'ckanext.unaids:presets.json ckanext.scheming:presets.json')
@pytest.mark.usefixtures('with_plugins', 'clean_db')
class TestDatasetLockHelper(object):
    """Test dataset lock helper functions.

    CKAN 2.11 Migration Notes:
    - Added scheming config markers for test-schema dataset type
    - Added clean_db fixture to ensure clean state
    """

    @pytest.fixture(autouse=True)
    def setup_org(self):
        """Create org and user for dataset creation in CKAN 2.11."""
        self.user = factories.User()
        self.org = factories.Organization(users=[{'name': self.user['id'], 'capacity': 'admin'}])

    def test_dataset_lockable(self):
        dataset = factories.Dataset(
            type="test-schema",
            owner_org=self.org['id'],
            user=self.user
        )
        assert toolkit.h.dataset_lockable(dataset['id'])

    def test_dataset_not_lockable(self):
        dataset = factories.Dataset(owner_org=self.org['id'], user=self.user)
        assert not toolkit.h.dataset_lockable(dataset['id'])

    def test_dataset_not_found(self):
        assert not toolkit.h.dataset_lockable("bad-id")


@pytest.mark.ckan_config('ckan.plugins', 'activity ytp_request unaids')
@pytest.mark.usefixtures('with_plugins')
class TestBuildNavIcon:
    """Test build_nav_icon helper function.

    This helper was created to fix HTML encoding issues where <i> tags
    for icons were being double-encoded in navigation items.
    """

    @patch('ckan.lib.helpers.url_for')
    @patch('ckan.plugins.toolkit.get_endpoint')
    def test_icon_not_double_encoded(self, mock_endpoint, mock_url_for):
        """Test that icon HTML is not double-encoded."""
        mock_endpoint.return_value = ('user', 'read')
        mock_url_for.return_value = '/user/admin'

        result = toolkit.h.build_nav_icon('user.read', 'Datasets', id='admin', icon='sitemap')

        # Check that result is a Markup object (safe HTML)
        assert isinstance(result, Markup)

        # Check that icon HTML is present and not double-encoded
        assert '<i class="fa fa-sitemap"></i>' in str(result)
        assert '&lt;i class=' not in str(result)
        assert '&amp;lt;i class=' not in str(result)

        # Check basic structure
        assert '<li' in str(result)
        assert '<a href="/user/admin">' in str(result)
        assert 'Datasets</a>' in str(result)
        assert '</li>' in str(result)

    @patch('ckan.lib.helpers.url_for')
    @patch('ckan.plugins.toolkit.get_endpoint')
    def test_active_class_applied(self, mock_endpoint, mock_url_for):
        """Test that active class is applied to current page."""
        mock_endpoint.return_value = ('user', 'read')
        mock_url_for.return_value = '/user/admin'

        result = toolkit.h.build_nav_icon('user.read', 'Profile', id='admin', icon='user')

        # Should have active class since endpoint matches
        assert 'class="active"' in str(result)

    @patch('ckan.lib.helpers.url_for')
    @patch('ckan.plugins.toolkit.get_endpoint')
    def test_no_icon(self, mock_endpoint, mock_url_for):
        """Test navigation item without icon."""
        mock_endpoint.return_value = ('user', 'read')
        mock_url_for.return_value = '/user/admin'

        result = toolkit.h.build_nav_icon('user.read', 'Profile', id='admin')

        # Should not have icon HTML
        assert '<i class="fa' not in str(result)
        assert 'Profile</a>' in str(result)


@pytest.mark.ckan_config('ckan.plugins', 'activity ytp_request unaids')
@pytest.mark.usefixtures('with_plugins')
class TestNavLink:
    """Test nav_link helper function.

    This helper was created to fix HTML encoding issues where <i> tags
    for icons were being double-encoded in buttons and links.
    """

    @patch('ckan.lib.helpers.url_for')
    @patch('ckan.plugins.toolkit.get_endpoint')
    def test_icon_not_double_encoded(self, mock_endpoint, mock_url_for):
        """Test that icon HTML is not double-encoded."""
        mock_endpoint.return_value = ('user', 'edit')
        mock_url_for.return_value = '/user/edit/admin'

        result = toolkit.h.nav_link(
            'Manage',
            named_route='user.edit',
            id='admin',
            class_='btn btn-default',
            icon='wrench'
        )

        # Check that result is a Markup object (safe HTML)
        assert isinstance(result, Markup)

        # Check that icon HTML is present and not double-encoded
        assert '<i class="fa fa-wrench"></i>' in str(result)
        assert '&lt;i class=' not in str(result)
        assert '&amp;lt;i class=' not in str(result)

        # Check basic structure
        assert '<a href="/user/edit/admin"' in str(result)
        assert 'class="btn btn-default"' in str(result)
        assert 'Manage</a>' in str(result)

    @patch('ckan.lib.helpers.url_for')
    @patch('ckan.plugins.toolkit.get_endpoint')
    def test_with_title_attribute(self, mock_endpoint, mock_url_for):
        """Test link with title attribute."""
        mock_endpoint.return_value = ('user', 'edit')
        mock_url_for.return_value = '/user/edit/admin'

        result = toolkit.h.nav_link(
            'Settings',
            named_route='user.edit',
            id='admin',
            icon='cog',
            title='Edit user settings'
        )

        assert 'title="Edit user settings"' in str(result)
        assert '<i class="fa fa-cog"></i>' in str(result)

    @patch('ckan.lib.helpers.url_for')
    @patch('ckan.plugins.toolkit.get_endpoint')
    def test_no_icon(self, mock_endpoint, mock_url_for):
        """Test link without icon."""
        mock_endpoint.return_value = ('user', 'edit')
        mock_url_for.return_value = '/user/edit/admin'

        result = toolkit.h.nav_link(
            'Edit Profile',
            named_route='user.edit',
            id='admin',
            class_='btn btn-primary'
        )

        # Should not have icon HTML
        assert '<i class="fa' not in str(result)
        assert 'Edit Profile</a>' in str(result)
        assert 'class="btn btn-primary"' in str(result)

    @patch('ckan.lib.helpers.url_for')
    @patch('ckan.plugins.toolkit.get_endpoint')
    def test_condition_false_returns_empty(self, mock_endpoint, mock_url_for):
        """Test that condition=False returns empty string."""
        mock_endpoint.return_value = ('user', 'edit')
        mock_url_for.return_value = '/user/edit/admin'

        result = toolkit.h.nav_link(
            'Hidden Link',
            named_route='user.edit',
            id='admin',
            condition=False
        )

        assert result == ''

    @patch('ckan.lib.helpers.url_for')
    @patch('ckan.plugins.toolkit.get_endpoint')
    def test_multiple_css_classes(self, mock_endpoint, mock_url_for):
        """Test link with multiple CSS classes."""
        mock_endpoint.return_value = ('user', 'edit')
        mock_url_for.return_value = '/user/edit/admin'

        result = toolkit.h.nav_link(
            'Button',
            named_route='user.edit',
            id='admin',
            class_='btn btn-default btn-sm',
            icon='pencil'
        )

        assert 'class="btn btn-default btn-sm"' in str(result)
        assert '<i class="fa fa-pencil"></i>' in str(result)


@pytest.mark.ckan_config('ckan.plugins', 'activity ytp_request unaids')
@pytest.mark.usefixtures('with_plugins')
class TestHelpersSecurity:
    """Security tests for helper functions to prevent XSS vulnerabilities."""

    @patch('ckan.lib.helpers.url_for')
    @patch('ckan.plugins.toolkit.get_endpoint')
    def test_build_nav_icon_escapes_malicious_icon(self, mock_endpoint, mock_url_for):
        """Test that malicious icon input is escaped to prevent XSS."""
        mock_endpoint.return_value = ('user', 'read')
        mock_url_for.return_value = '/user/admin'

        # Try to inject XSS via icon parameter
        malicious_icon = '"></i><script>alert("XSS")</script><i class="'
        result = toolkit.h.build_nav_icon('user.read', 'Test', id='admin', icon=malicious_icon)

        # Malicious content should be escaped
        result_str = str(result)
        assert '<script>' not in result_str  # Script tags should be escaped
        assert '&lt;script&gt;' in result_str  # Should contain escaped version
        assert '&quot;&gt;' in result_str  # Quotes and brackets should be escaped

    @patch('ckan.lib.helpers.url_for')
    @patch('ckan.plugins.toolkit.get_endpoint')
    def test_build_nav_icon_escapes_malicious_title(self, mock_endpoint, mock_url_for):
        """Test that malicious title input is escaped to prevent XSS."""
        mock_endpoint.return_value = ('user', 'read')
        mock_url_for.return_value = '/user/admin'

        # Try to inject XSS via title parameter
        malicious_title = 'Test<script>alert("XSS")</script>'
        result = toolkit.h.build_nav_icon('user.read', malicious_title, id='admin', icon='user')

        # Malicious content should be escaped
        result_str = str(result)
        assert '<script>' not in result_str
        assert '&lt;script&gt;' in result_str

    @patch('ckan.lib.helpers.url_for')
    @patch('ckan.plugins.toolkit.get_endpoint')
    def test_nav_link_escapes_malicious_icon(self, mock_endpoint, mock_url_for):
        """Test that malicious icon input is escaped to prevent XSS."""
        mock_endpoint.return_value = ('user', 'edit')
        mock_url_for.return_value = '/user/edit/admin'

        # Try to inject XSS via icon parameter
        malicious_icon = '"></i><script>alert("XSS")</script><i class="'
        result = toolkit.h.nav_link(
            'Test',
            named_route='user.edit',
            id='admin',
            icon=malicious_icon
        )

        # Malicious content should be escaped
        result_str = str(result)
        assert '<script>' not in result_str
        assert '&lt;script&gt;' in result_str

    @patch('ckan.lib.helpers.url_for')
    @patch('ckan.plugins.toolkit.get_endpoint')
    def test_nav_link_escapes_malicious_text(self, mock_endpoint, mock_url_for):
        """Test that malicious text input is escaped to prevent XSS."""
        mock_endpoint.return_value = ('user', 'edit')
        mock_url_for.return_value = '/user/edit/admin'

        # Try to inject XSS via text parameter
        malicious_text = 'Test<script>alert("XSS")</script>'
        result = toolkit.h.nav_link(
            malicious_text,
            named_route='user.edit',
            id='admin',
            class_='btn btn-default'
        )

        # Malicious content should be escaped
        result_str = str(result)
        assert '<script>' not in result_str
        assert '&lt;script&gt;' in result_str

    @patch('ckan.lib.helpers.url_for')
    @patch('ckan.plugins.toolkit.get_endpoint')
    def test_nav_link_escapes_malicious_class(self, mock_endpoint, mock_url_for):
        """Test that malicious class input is escaped to prevent XSS."""
        mock_endpoint.return_value = ('user', 'edit')
        mock_url_for.return_value = '/user/edit/admin'

        # Try to inject XSS via class parameter
        malicious_class = 'btn" onload="alert(\'XSS\')" data-evil="'
        result = toolkit.h.nav_link(
            'Test',
            named_route='user.edit',
            id='admin',
            class_=malicious_class
        )

        # Malicious content should be escaped - quotes should be escaped
        result_str = str(result)
        # Quotes should be escaped, preventing the injection from breaking out of the attribute
        assert '&quot;' in result_str  # Quotes should be escaped
        # The escaped content should not break out of the class attribute
        assert 'class="btn&quot;' in result_str  # Escaped quote prevents attribute breakout

    @patch('ckan.lib.helpers.url_for')
    @patch('ckan.plugins.toolkit.get_endpoint')
    def test_nav_link_escapes_malicious_title_attr(self, mock_endpoint, mock_url_for):
        """Test that malicious title attribute is escaped to prevent XSS."""
        mock_endpoint.return_value = ('user', 'edit')
        mock_url_for.return_value = '/user/edit/admin'

        # Try to inject XSS via title parameter
        malicious_title = 'Test" onmouseover="alert(\'XSS\')" data-evil="'
        result = toolkit.h.nav_link(
            'Test',
            named_route='user.edit',
            id='admin',
            title=malicious_title
        )

        # Malicious content should be escaped - quotes should be escaped
        result_str = str(result)
        # Quotes should be escaped, preventing the injection from breaking out of the attribute
        assert '&quot;' in result_str  # Quotes should be escaped
        # The escaped content should not break out of the title attribute
        assert 'title="Test&quot;' in result_str  # Escaped quote prevents attribute breakout
