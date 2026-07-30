"""Tests for the user edit form template."""
import re
import pytest
import ckan.plugins.toolkit as toolkit

from ckan.tests import factories

NOTIFICATIONS_INPUT = re.compile(
    r'<input[^>]*name="activity_streams_email_notifications"[^>]*>'
)


def notifications_checkbox(response):
    match = NOTIFICATIONS_INPUT.search(response.body)
    assert match, "notification checkbox is missing from the form"
    return match.group(0)


@pytest.mark.ckan_config(
    'ckan.plugins', 'activity ytp_request unaids pages scheming_datasets')
@pytest.mark.ckan_config('ckan.activity_streams_email_notifications', True)
@pytest.mark.usefixtures('with_plugins')
class TestUserEditForm(object):
    def test_notifications_checkbox_reflects_the_edited_user(self, app):
        # Reading this from the logged-in user instead of the edited one lets a
        # sysadmin's save overwrite the other user's stored preference.
        sysadmin = factories.Sysadmin(
            activity_streams_email_notifications=False)
        subscribed_user = factories.User(
            activity_streams_email_notifications=True)

        response = app.get(
            toolkit.url_for('user.edit', id=subscribed_user['name']),
            extra_environ={'REMOTE_USER': sysadmin['name']}
        )

        assert 'checked' in notifications_checkbox(response)

    def test_sysadmin_password_shown_only_when_editing_someone_else(self, app):
        sysadmin = factories.Sysadmin()
        other_user = factories.User()
        environ = {'REMOTE_USER': sysadmin['name']}

        own_profile = app.get(
            toolkit.url_for('user.edit', id=sysadmin['name']),
            extra_environ=environ
        )
        other_profile = app.get(
            toolkit.url_for('user.edit', id=other_user['name']),
            extra_environ=environ
        )

        assert 'field-password-old' not in own_profile.body
        assert 'field-password-old' in other_profile.body
