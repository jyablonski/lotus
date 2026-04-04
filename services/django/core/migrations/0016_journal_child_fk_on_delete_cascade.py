# Aligns journal child FKs with Django models (ON DELETE CASCADE).
# Some DBs were created without CASCADE on the FK; deleting a journal then failed
# with FK violations on journal_topics.

from django.db import migrations


def _drop_fks_to_journals(apps, schema_editor) -> None:
    # Avoid any "%" in SQL: Django/psycopg2 treat "%" as bind placeholders and raise
    # IndexError when none are supplied. Build ALTER via concatenation in PL/pgSQL.
    schema_editor.execute(
        r"""
        DO $$
        DECLARE
            r RECORD;
        BEGIN
            FOR r IN
                SELECT c.conname, quote_ident(n.nspname) || '.' || quote_ident(t.relname) AS tbl
                FROM pg_constraint c
                JOIN pg_class t ON c.conrelid = t.oid
                JOIN pg_namespace n ON t.relnamespace = n.oid
                JOIN pg_class ref ON c.confrelid = ref.oid
                JOIN pg_namespace refn ON ref.relnamespace = refn.oid
                WHERE c.contype = 'f'
                  AND n.nspname = 'source'
                  AND t.relname IN (
                      'journal_topics',
                      'journal_embeddings',
                      'journal_sentiments',
                      'journal_details'
                  )
                  AND refn.nspname = 'source'
                  AND ref.relname = 'journals'
            LOOP
                EXECUTE 'ALTER TABLE ' || r.tbl || ' DROP CONSTRAINT ' || quote_ident(r.conname);
            END LOOP;
        END $$;
        """
    )


def _add_cascade_fks(apps, schema_editor) -> None:
    for stmt in (
        """
        ALTER TABLE source.journal_topics
            ADD CONSTRAINT journal_topics_journal_id_fk_journals_cascade
            FOREIGN KEY (journal_id) REFERENCES source.journals(id) ON DELETE CASCADE
        """,
        """
        ALTER TABLE source.journal_embeddings
            ADD CONSTRAINT journal_embeddings_journal_id_fk_journals_cascade
            FOREIGN KEY (journal_id) REFERENCES source.journals(id) ON DELETE CASCADE
        """,
        """
        ALTER TABLE source.journal_sentiments
            ADD CONSTRAINT journal_sentiments_journal_id_fk_journals_cascade
            FOREIGN KEY (journal_id) REFERENCES source.journals(id) ON DELETE CASCADE
        """,
        """
        ALTER TABLE source.journal_details
            ADD CONSTRAINT journal_details_journal_id_fk_journals_cascade
            FOREIGN KEY (journal_id) REFERENCES source.journals(id) ON DELETE CASCADE
        """,
    ):
        schema_editor.execute(stmt)


def _drop_cascade_fks(apps, schema_editor) -> None:
    for stmt in (
        "ALTER TABLE source.journal_topics DROP CONSTRAINT IF EXISTS journal_topics_journal_id_fk_journals_cascade",
        "ALTER TABLE source.journal_embeddings DROP CONSTRAINT IF EXISTS journal_embeddings_journal_id_fk_journals_cascade",
        "ALTER TABLE source.journal_sentiments DROP CONSTRAINT IF EXISTS journal_sentiments_journal_id_fk_journals_cascade",
        "ALTER TABLE source.journal_details DROP CONSTRAINT IF EXISTS journal_details_journal_id_fk_journals_cascade",
    ):
        schema_editor.execute(stmt)


def _add_no_action_fks(apps, schema_editor) -> None:
    for stmt in (
        """
        ALTER TABLE source.journal_topics
            ADD CONSTRAINT journal_topics_journal_id_fk_journals_noaction
            FOREIGN KEY (journal_id) REFERENCES source.journals(id) ON DELETE NO ACTION
        """,
        """
        ALTER TABLE source.journal_embeddings
            ADD CONSTRAINT journal_embeddings_journal_id_fk_journals_noaction
            FOREIGN KEY (journal_id) REFERENCES source.journals(id) ON DELETE NO ACTION
        """,
        """
        ALTER TABLE source.journal_sentiments
            ADD CONSTRAINT journal_sentiments_journal_id_fk_journals_noaction
            FOREIGN KEY (journal_id) REFERENCES source.journals(id) ON DELETE NO ACTION
        """,
        """
        ALTER TABLE source.journal_details
            ADD CONSTRAINT journal_details_journal_id_fk_journals_noaction
            FOREIGN KEY (journal_id) REFERENCES source.journals(id) ON DELETE NO ACTION
        """,
    ):
        schema_editor.execute(stmt)


def forward(apps, schema_editor) -> None:
    _drop_fks_to_journals(apps, schema_editor)
    _add_cascade_fks(apps, schema_editor)


def reverse(apps, schema_editor) -> None:
    _drop_cascade_fks(apps, schema_editor)
    _add_no_action_fks(apps, schema_editor)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0015_seed_dev_data"),
    ]

    operations = [
        migrations.RunPython(forward, reverse),
    ]
