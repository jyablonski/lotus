import uuid

import pytest
from core.models import FeatureFlag


@pytest.mark.django_db
class TestFeatureFlag:
    def test_create_feature_flag(self):
        flag = FeatureFlag.objects.create(
            flag_name="test_feature",
            enabled=True,
        )
        assert flag.id is not None
        assert isinstance(flag.id, uuid.UUID)
        assert flag.flag_name == "test_feature"
        assert flag.enabled is True
        assert flag.created_at is not None
        assert flag.modified_at is not None

    def test_feature_flag_default_enabled_false(self):
        flag = FeatureFlag.objects.create(flag_name="disabled_feature")
        assert flag.enabled is False

    def test_feature_flag_unique_name(self):
        FeatureFlag.objects.create(flag_name="unique_feature", enabled=True)
        with pytest.raises(Exception):
            FeatureFlag.objects.create(flag_name="unique_feature", enabled=False)

    def test_feature_flag_str_representation_enabled(self):
        flag = FeatureFlag.objects.create(flag_name="enabled_feature", enabled=True)
        assert "✓" in str(flag)
        assert "enabled_feature" in str(flag)

    def test_feature_flag_str_representation_disabled(self):
        flag = FeatureFlag.objects.create(flag_name="disabled_feature", enabled=False)
        assert "✗" in str(flag)
        assert "disabled_feature" in str(flag)

    def test_feature_flag_ordering(self):
        FeatureFlag.objects.create(flag_name="zebra", enabled=True)
        FeatureFlag.objects.create(flag_name="alpha", enabled=True)
        FeatureFlag.objects.create(flag_name="beta", enabled=True)

        flags = list(FeatureFlag.objects.all())
        assert flags[0].flag_name == "alpha"
        assert flags[1].flag_name == "beta"
        assert flags[2].flag_name == "zebra"

    def test_feature_flag_update_modified_at(self):
        flag = FeatureFlag.objects.create(flag_name="test_feature", enabled=True)
        original_modified = flag.modified_at

        flag.enabled = False
        flag.save()

        flag.refresh_from_db()
        assert flag.modified_at > original_modified
