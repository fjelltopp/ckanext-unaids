"""Tests for the user edit form template."""
import re
import pytest
import ckan.plugins.toolkit as toolkit

from ckan.tests import factories

NOTIFICATIONS_INPUT = re.compile(
    r'<input[^>]*name="activity_streams_email_notifications"[^>]*>'
)
SYSADMIN_PASSWORD_INPUT = re.compile(r'<input[^>]*name="old_password"[^>]*>')


def find_input(pattern, response, description):
    match = pattern.search(response.body)
    assert match, "{} is missing from the form".format(description)
    return match.group(0)


def is_checked(input_tag):
    # Matching the bare attribute avoids counting a future data-checked.
    return re.search(r'(?<![-\w])checked(?![-\w])', input_tag) is not None


def user_edit_page(app, viewer, edited_user):
    return app.get(
        toolkit.url_for('user.edit', id=edited_user['name']),
        extra_environ={'REMOTE_USER': viewer['name']}
    )


@pytest.mark.ckan_config(
    'ckan.plugins', 'activity ytp_request unaids pages scheming_datasets')
@pytest.mark.ckan_config('ckan.activity_streams_email_notifications', True)
@pytest.mark.usefixtures('with_plugins')
class TestUserEditForm(object):
    def test_notifications_checkbox_reflects_the_edited_user(self, app):
        # Reading this from the logged-in user instead of the edited one lets a
        # sysadmin's save overwrite the other user's stored preference. Both
        # directions are asserted so a hardcoded state cannot satisfy the test.
        subscribed = factories.User(
            activity_streams_email_notifications=True)
        unsubscribed = factories.User(
            activity_streams_email_notifications=False)
        subscribed_sysadmin = factories.Sysadmin(
            activity_streams_email_notifications=True)
        unsubscribed_sysadmin = factories.Sysadmin(
            activity_streams_email_notifications=False)

        subscribed_page = user_edit_page(app, unsubscribed_sysadmin, subscribed)
        unsubscribed_page = user_edit_page(
            app, subscribed_sysadmin, unsubscribed)

        assert is_checked(find_input(
            NOTIFICATIONS_INPUT, subscribed_page, "notification checkbox"))
        assert not is_checked(find_input(
            NOTIFICATIONS_INPUT, unsubscribed_page, "notification checkbox"))

    def test_sysadmin_password_shown_only_when_editing_someone_else(self, app):
        sysadmin = factories.Sysadmin()
        other_user = factories.User()

        own_profile = user_edit_page(app, sysadmin, sysadmin)
        other_profile = user_edit_page(app, sysadmin, other_user)

        # A hidden or non-required field would leave cross-user saves unable to
        # supply the password ckan/views/user.py demands.
        password_input = find_input(
            SYSADMIN_PASSWORD_INPUT, other_profile, "sysadmin password field")
        assert 'type="password"' in password_input
        assert 'required' in password_input

        assert 'type="hidden"' in find_input(
            SYSADMIN_PASSWORD_INPUT, own_profile, "old_password input")
        assert 'field-password-old' not in own_profile.body
