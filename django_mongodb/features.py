from django.db.backends.base.features import BaseDatabaseFeatures


class DatabaseFeatures(BaseDatabaseFeatures):
    supports_foreign_keys = False
    # Not implemented: https://github.com/mongodb-labs/django-mongodb/issues/8
    supports_json_field = False
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
        "timezones.tests.LegacyDatabaseTests.test_query_datetime_lookups",
        "timezones.tests.NewDatabaseTests.test_query_convert_timezones",
        "timezones.tests.NewDatabaseTests.test_query_datetime_lookups",
        "timezones.tests.NewDatabaseTests.test_query_datetime_lookups_in_other_timezone",
        # "Save with update_fields did not affect any rows."
        "basic.tests.SelectOnSaveTests.test_select_on_save_lying_update",
        # QuerySet.extra() not supported.
        "basic.tests.ModelTest.test_extra_method_select_argument_with_dashes",
        "basic.tests.ModelTest.test_extra_method_select_argument_with_dashes_and_values",
        # QuerySet.aggregate() not supported: https://github.com/mongodb-labs/django-mongodb/issues/12
        "from_db_value.tests.FromDBValueTest.test_aggregation",
        "timezones.tests.LegacyDatabaseTests.test_query_aggregation",
        "timezones.tests.NewDatabaseTests.test_query_aggregation",
        # filtering on large decimalfield, see https://code.djangoproject.com/ticket/34590
        # for some background.
        "model_fields.test_decimalfield.DecimalFieldTests.test_lookup_decimal_larger_than_max_digits",
        "model_fields.test_decimalfield.DecimalFieldTests.test_lookup_really_big_value",
        # 'TruncDate' object has no attribute 'alias'
        "model_fields.test_datetimefield.DateTimeFieldTests.test_lookup_date_with_use_tz",
        "model_fields.test_datetimefield.DateTimeFieldTests.test_lookup_date_without_use_tz",
        # Empty queryset ORed (|) with another gives empty results.
        "or_lookups.tests.OrLookupsTests.test_empty_in",
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
            "timezones.tests.NewDatabaseTests.test_update_with_timedelta",
            "update.tests.AdvancedTests.test_update_annotated_queryset",
            "update.tests.AdvancedTests.test_update_negated_f",
            "update.tests.AdvancedTests.test_update_negated_f_conditional_annotation",
            "update.tests.AdvancedTests.test_update_transformed_field",
        },
        "AutoField not supported.": {
            "model_fields.test_autofield.AutoFieldTests",
            "model_fields.test_autofield.BigAutoFieldTests",
            "model_fields.test_autofield.SmallAutoFieldTests",
        },
        "QuerySet.select_related() not supported.": {
            "defer.tests.DeferTests.test_defer_foreign_keys_are_deferred_and_not_traversed",
            "defer.tests.DeferTests.test_defer_with_select_related",
            "defer.tests.DeferTests.test_only_with_select_related",
            "defer.tests.TestDefer2.test_defer_proxy",
            "defer_regress.tests.DeferRegressionTest.test_basic",
            "defer_regress.tests.DeferRegressionTest.test_common_model_different_mask",
            "model_fields.test_booleanfield.BooleanFieldTests.test_select_related",
            "model_fields.test_foreignkey.ForeignKeyTests.test_empty_string_fk",
            "defer_regress.tests.DeferRegressionTest.test_defer_annotate_select_related",
            "defer_regress.tests.DeferRegressionTest.test_defer_with_select_related",
            "defer_regress.tests.DeferRegressionTest.test_only_with_select_related",
            "defer_regress.tests.DeferRegressionTest.test_proxy_model_defer_with_select_related",
            "defer_regress.tests.DeferRegressionTest.test_reverse_one_to_one_relations",
            "defer_regress.tests.DeferRegressionTest.test_ticket_23270",
        },
        "MongoDB does not enforce UNIQUE constraints.": {
            "auth_tests.test_basic.BasicTestCase.test_unicode_username",
            "auth_tests.test_migrations.ProxyModelWithSameAppLabelTests.test_migrate_with_existing_target_permission",
            "constraints.tests.UniqueConstraintTests.test_database_constraint",
            "contenttypes_tests.test_operations.ContentTypeOperationsTests.test_content_type_rename_conflict",
            "contenttypes_tests.test_operations.ContentTypeOperationsTests.test_existing_content_type_rename",
            "custom_pk.tests.CustomPKTests.test_unique_pk",
            "force_insert_update.tests.ForceInsertInheritanceTests.test_force_insert_with_existing_grandparent",
            "get_or_create.tests.GetOrCreateTestsWithManualPKs.test_create_with_duplicate_primary_key",
            "get_or_create.tests.GetOrCreateTestsWithManualPKs.test_savepoint_rollback",
            "get_or_create.tests.GetOrCreateThroughManyToMany.test_something",
            "get_or_create.tests.UpdateOrCreateTests.test_manual_primary_key_test",
            "get_or_create.tests.UpdateOrCreateTestsWithManualPKs.test_create_with_duplicate_primary_key",
            "model_fields.test_filefield.FileFieldTests.test_unique_when_same_filename",
            "one_to_one.tests.OneToOneTests.test_multiple_o2o",
            "queries.test_bulk_update.BulkUpdateTests.test_database_routing_batch_atomicity",
        },
        "Test assumes integer primary key.": {
            "model_fields.test_foreignkey.ForeignKeyTests.test_to_python",
        },
        "QuerySet.dates() is not supported on MongoDB.": {
            "dates.tests.DatesTests.test_dates_trunc_datetime_fields",
            "dates.tests.DatesTests.test_related_model_traverse",
        },
        "QuerySet.datetimes() is not supported on MongoDB.": {
            "datetimes.tests.DateTimesTests.test_21432",
            "datetimes.tests.DateTimesTests.test_datetimes_has_lazy_iterator",
            "datetimes.tests.DateTimesTests.test_datetimes_returns_available_dates_for_given_scope_and_given_field",
            "datetimes.tests.DateTimesTests.test_related_model_traverse",
            "timezones.tests.LegacyDatabaseTests.test_query_datetimes",
            "timezones.tests.NewDatabaseTests.test_query_datetimes",
            "timezones.tests.NewDatabaseTests.test_query_datetimes_in_other_timezone",
        },
        "QuerySet.distinct() is not supported.": {
            "update.tests.AdvancedTests.test_update_all",
        },
        "QuerySet.extra() is not supported.": {
            "basic.tests.ModelTest.test_extra_method_select_argument_with_dashes",
            "basic.tests.ModelTest.test_extra_method_select_argument_with_dashes_and_values",
            "defer.tests.DeferTests.test_defer_extra",
        },
        "Queries with multiple tables are not supported.": {
            "defer.tests.BigChildDeferTests.test_defer_baseclass_when_subclass_has_added_field",
            "defer.tests.BigChildDeferTests.test_defer_subclass",
            "defer.tests.BigChildDeferTests.test_defer_subclass_both",
            "defer.tests.BigChildDeferTests.test_only_baseclass_when_subclass_has_added_field",
            "defer.tests.BigChildDeferTests.test_only_subclass",
            "defer.tests.DeferTests.test_defer_baseclass_when_subclass_has_no_added_fields",
            "defer.tests.DeferTests.test_defer_of_overridden_scalar",
            "defer.tests.DeferTests.test_only_baseclass_when_subclass_has_no_added_fields",
            "defer.tests.TestDefer2.test_defer_inheritance_pk_chaining",
            "defer_regress.tests.DeferRegressionTest.test_ticket_16409",
            "model_fields.test_manytomanyfield.ManyToManyFieldDBTests.test_value_from_object_instance_with_pk",
            "model_fields.test_uuid.TestAsPrimaryKey.test_two_level_foreign_keys",
            "timezones.tests.LegacyDatabaseTests.test_query_annotation",
            "timezones.tests.NewDatabaseTests.test_query_annotation",
            "update.tests.AdvancedTests.test_update_annotated_multi_table_queryset",
            "update.tests.AdvancedTests.test_update_fk",
            "update.tests.AdvancedTests.test_update_ordered_by_inline_m2m_annotation",
            "update.tests.AdvancedTests.test_update_ordered_by_m2m_annotation",
            "update.tests.AdvancedTests.test_update_ordered_by_m2m_annotation_desc",
            "update.tests.SimpleTest.test_empty_update_with_inheritance",
            "update.tests.SimpleTest.test_foreign_key_update_with_id",
            "update.tests.SimpleTest.test_nonempty_update_with_inheritance",
        },
        "Test executes raw SQL.": {
            "timezones.tests.LegacyDatabaseTests.test_cursor_execute_accepts_naive_datetime",
            "timezones.tests.LegacyDatabaseTests.test_cursor_execute_returns_naive_datetime",
            "timezones.tests.LegacyDatabaseTests.test_raw_sql",
            "timezones.tests.NewDatabaseTests.test_cursor_execute_accepts_aware_datetime",
            "timezones.tests.NewDatabaseTests.test_cursor_execute_returns_aware_datetime",
            "timezones.tests.NewDatabaseTests.test_cursor_explicit_time_zone",
            "timezones.tests.NewDatabaseTests.test_raw_sql",
        },
        "BSON Date type doesn't support microsecond precision.": {
            "basic.tests.ModelRefreshTests.test_refresh_unsaved",
            "basic.tests.ModelTest.test_microsecond_precision",
            "timezones.tests.LegacyDatabaseTests.test_auto_now_and_auto_now_add",
            "timezones.tests.LegacyDatabaseTests.test_aware_datetime_in_local_timezone_with_microsecond",
            "timezones.tests.LegacyDatabaseTests.test_naive_datetime_with_microsecond",
            "timezones.tests.NewDatabaseTests.test_aware_datetime_in_local_timezone_with_microsecond",
            "timezones.tests.NewDatabaseTests.test_naive_datetime_with_microsecond",
        },
    }
