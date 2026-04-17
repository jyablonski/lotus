"""SQL queries used by export assets."""

SELECT_FEATURE_FLAGS = "SELECT * FROM feature_flags"

SELECT_USER_JOURNAL_SUMMARY = "SELECT * FROM gold.user_journal_summary"

SELECT_STAKEHOLDER_PROMPT_BY_APPLICATION = """
SELECT sp.id, g.name AS stakeholder_group, sp.application, sp.prompt
FROM stakeholder_prompts sp
JOIN auth_group g ON g.id = sp.stakeholder_group_id
WHERE sp.application = %s
LIMIT 1
"""

INSERT_STAKEHOLDER_PROMPT_RESPONSE = """
INSERT INTO stakeholder_prompt_responses
    (stakeholder_prompt_id, model, response)
VALUES (%s, %s, %s)
"""
