"""Admin tests for StakeholderPrompt group-scoped access control.

Covers:
- Admin-role users see every prompt regardless of group.
- Group members only see prompts in their own group.
- Group members cannot view/change prompts in other groups.
- The stakeholder_group dropdown is filtered to the user's groups.
- Users without any allowed group have no access.
"""

from core.admin import admin_site
from core.models import (
    StakeholderPrompt,
    StakeholderPromptResponse,
    User as LotusUser,
)
from django.contrib.auth.models import (
    Group,
    User as DjangoUser,
)
from django.core.cache import cache
from django.urls import reverse
import pytest


def _make_user(email: str, username: str, groups: list[str], role: str = "Consumer"):
    """Create a Django user + matching LotusUser, in the given groups."""
    django_user = DjangoUser.objects.create_user(
        username=username, email=email, password="testpass123"
    )
    for name in groups:
        g, _ = Group.objects.get_or_create(name=name)
        django_user.groups.add(g)
    django_user.save()
    LotusUser.objects.get_or_create(email=email, defaults={"role": role, "timezone": "UTC"})
    return django_user


@pytest.mark.django_db
class TestStakeholderPromptAdminRegistration:
    def test_stakeholder_prompt_registered(self):
        assert StakeholderPrompt in admin_site._registry

    def test_stakeholder_prompt_response_registered(self):
        assert StakeholderPromptResponse in admin_site._registry


@pytest.mark.django_db
class TestStakeholderPromptAdminAdminRole:
    """Admin-role users see every prompt regardless of owning group."""

    def test_admin_sees_all_prompts(self, admin_client):
        cache.clear()
        sales, _ = Group.objects.get_or_create(name="sales")
        product, _ = Group.objects.get_or_create(name="product")
        StakeholderPrompt.objects.create(
            stakeholder_group=sales, application="sales_app", prompt="s"
        )
        StakeholderPrompt.objects.create(
            stakeholder_group=product, application="product_app", prompt="p"
        )

        url = reverse("lotus_admin:core_stakeholderprompt_changelist")
        response = admin_client.get(url)
        body = response.content.decode()
        assert response.status_code == 200
        assert "sales_app" in body
        assert "product_app" in body


@pytest.mark.django_db
class TestStakeholderPromptAdminGroupScoping:
    """Non-admin group members only see prompts in their own group."""

    def test_sales_member_sees_only_sales_prompts(self, client):
        cache.clear()
        sales, _ = Group.objects.get_or_create(name="sales")
        product, _ = Group.objects.get_or_create(name="product")
        StakeholderPrompt.objects.create(
            stakeholder_group=sales, application="sales_app", prompt="s"
        )
        StakeholderPrompt.objects.create(
            stakeholder_group=product, application="product_app", prompt="p"
        )

        user = _make_user("sales@test.com", "sales_user", ["sales"])
        client.force_login(user)

        url = reverse("lotus_admin:core_stakeholderprompt_changelist")
        response = client.get(url)
        body = response.content.decode()
        assert response.status_code == 200
        assert "sales_app" in body
        assert "product_app" not in body

    def test_product_member_cannot_view_sales_prompt_detail(self, client):
        cache.clear()
        sales, _ = Group.objects.get_or_create(name="sales")
        Group.objects.get_or_create(name="product")
        sales_prompt = StakeholderPrompt.objects.create(
            stakeholder_group=sales, application="sales_app", prompt="s"
        )

        user = _make_user("p@test.com", "product_user", ["product"])
        client.force_login(user)

        url = reverse("lotus_admin:core_stakeholderprompt_change", args=[sales_prompt.pk])
        response = client.get(url)
        # Django admin returns 302 to index when user lacks change permission
        assert response.status_code in (302, 403, 404)

    def test_group_dropdown_filtered_to_own_groups(self, client):
        cache.clear()
        Group.objects.get_or_create(name="sales")
        Group.objects.get_or_create(name="product")

        user = _make_user("s@test.com", "only_sales", ["sales"])
        client.force_login(user)

        url = reverse("lotus_admin:core_stakeholderprompt_add")
        response = client.get(url)
        assert response.status_code == 200
        body = response.content.decode()
        # The <select> for stakeholder_group should include 'sales' but not
        # 'product'. We search for the plaintext option labels in the rendered
        # form.
        assert ">sales<" in body
        assert ">product<" not in body


@pytest.mark.django_db
class TestStakeholderPromptAdminNoAccess:
    """Users not in any allowed group and without Admin role have no access."""

    def test_ml_ops_user_has_no_module_permission(self, client):
        cache.clear()
        # ml_ops is an allowed admin group (can log in) but NOT an allowed
        # stakeholder-prompt group, so the module should be hidden.
        user = _make_user("ml@test.com", "ml_ops_user", ["ml_ops"])
        client.force_login(user)

        url = reverse("lotus_admin:core_stakeholderprompt_changelist")
        response = client.get(url)
        assert response.status_code in (302, 403)
