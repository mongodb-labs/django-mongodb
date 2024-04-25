from django.db.backends.base.features import BaseDatabaseFeatures


class DatabaseFeatures(BaseDatabaseFeatures):
    supports_foreign_keys = False
    # Not implemented: https://github.com/mongodb-labs/django-mongodb/issues/7
    supports_transactions = False
    uses_savepoints = False

    django_test_expected_failures = {
        "basic.tests.ModelInstanceCreationTests.test_save_parent_primary_with_default",
        "basic.tests.ModelInstanceCreationTests.test_save_primary_with_db_default",
        "basic.tests.ModelInstanceCreationTests.test_save_primary_with_default",
        # Date lookups aren't implemented: https://github.com/mongodb-labs/django-mongodb/issues/9
        # (e.g. 'ExtractMonth' object has no attribute 'alias')
        "basic.tests.ModelLookupTest.test_does_not_exist",
        "basic.tests.ModelLookupTest.test_equal_lookup",
        "basic.tests.ModelLookupTest.test_rich_lookup",
        "basic.tests.ModelLookupTest.test_too_many",
        "basic.tests.ModelTest.test_year_lookup_edge_case",
        # "Save with update_fields did not affect any rows."
        "basic.tests.SelectOnSaveTests.test_select_on_save_lying_update",
        # QuerySet.extra() not supported.
        "basic.tests.ModelTest.test_extra_method_select_argument_with_dashes",
        "basic.tests.ModelTest.test_extra_method_select_argument_with_dashes_and_values",
        # QuerySet.aggregate() not supported: https://github.com/mongodb-labs/django-mongodb/issues/12
        "from_db_value.tests.FromDBValueTest.test_aggregation",
        # filtering on large decimalfield, see https://code.djangoproject.com/ticket/34590
        # for some background.
        "model_fields.test_decimalfield.DecimalFieldTests.test_lookup_decimal_larger_than_max_digits",
        "model_fields.test_decimalfield.DecimalFieldTests.test_lookup_really_big_value",
        # 'TruncDate' object has no attribute 'alias'
        "model_fields.test_datetimefield.DateTimeFieldTests.test_lookup_date_with_use_tz",
        "model_fields.test_datetimefield.DateTimeFieldTests.test_lookup_date_without_use_tz",
        # Empty queryset ORed (|) with another gives empty results.
        "or_lookups.tests.OrLookupsTests.test_empty_in",
        # Joins not supported.
        "model_fields.test_uuid.TestAsPrimaryKey.test_two_level_foreign_keys",
    }

    django_test_skips = {
        "Pattern lookups on UUIDField are not supported.": {
            "model_fields.test_uuid.TestQuerying.test_contains",
            "model_fields.test_uuid.TestQuerying.test_endswith",
            "model_fields.test_uuid.TestQuerying.test_filter_with_expr",
            "model_fields.test_uuid.TestQuerying.test_icontains",
            "model_fields.test_uuid.TestQuerying.test_iendswith",
            "model_fields.test_uuid.TestQuerying.test_iexact",
            "model_fields.test_uuid.TestQuerying.test_istartswith",
            "model_fields.test_uuid.TestQuerying.test_startswith",
        },
        "QuerySet.update() with expression not supported.": {
            "model_fields.test_integerfield.PositiveIntegerFieldTests.test_negative_values",
        },
    }
