from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0005_runtimeconfig"),
    ]

    operations = [
        migrations.DeleteModel(
            name="FeatureFlag",
        ),
    ]
