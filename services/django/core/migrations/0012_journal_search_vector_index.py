# GIN index for tsvector keyword search, created concurrently to avoid locking.

from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations


class Migration(migrations.Migration):
    # AddIndexConcurrently / RemoveIndexConcurrently cannot run inside a transaction.
    atomic = False

    dependencies = [
        ("core", "0011_add_journal_search_vector"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="journal",
            index=GinIndex(
                fields=["search_vector"],
                name="idx_journals_search_vector",
            ),
        ),
    ]
