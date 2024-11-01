#!/usr/bin/env python
import os
import pathlib
import sys

test_apps = [
    "admin_filters",
    "aggregation",
    "aggregation_regress",
    "annotations",
    "auth_tests.test_models.UserManagerTestCase",
    "backends",
    "basic",
    "bulk_create",
    "custom_pk",
    "dates",
    "datetimes",
    "db_functions",
    "dbshell_",
    "defer",
    "defer_regress",
    "delete",
    "delete_regress",
    "empty",
    "expressions",
    "expressions_case",
    "force_insert_update",
    "from_db_value",
    "generic_relations",
    "generic_relations_regress",
    "introspection",
    "known_related_objects",
    "lookup",
    "m2m_and_m2o",
    "m2m_intermediary",
    "m2m_multiple",
    "m2m_recursive",
    "m2m_regress",
    "m2m_signals",
    "m2m_through",
    "m2m_through_regress",
    "m2o_recursive",
    "many_to_many",
    "many_to_one",
    "many_to_one_null",
    "migrations",
    "model_fields",
    "model_fields_",
    "model_forms",
    "model_formsets",
    "model_inheritance_regress",
    "mutually_referential",
    "nested_foreign_keys",
    "null_fk",
    "null_fk_ordering",
    "null_queries",
    "one_to_one",
    "or_lookups",
    "ordering",
    "queries",
    "queries_",
    "schema",
    "select_related",
    "select_related_onetoone",
    "select_related_regress",
    "sessions_tests",
    "timezones",
    "update",
    "xor_lookups",
]
runtests = pathlib.Path(__file__).parent.resolve() / "runtests.py"
run_tests_cmd = f"python3 {runtests} %s --settings mongodb_settings -v 2"

shouldFail = False
for app_name in test_apps:
    res = os.system(run_tests_cmd % app_name)  # noqa: S605
    if res != 0:
        shouldFail = True
sys.exit(1 if shouldFail else 0)
