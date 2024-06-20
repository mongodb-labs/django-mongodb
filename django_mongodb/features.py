from django.db.backends.base.features import BaseDatabaseFeatures
from django.utils.functional import cached_property


class DatabaseFeatures(BaseDatabaseFeatures):
    greatest_least_ignores_nulls = True
    has_json_object_function = False
    supports_date_lookup_using_string = False
    supports_foreign_keys = False
    supports_ignore_conflicts = False
    # Not implemented: https://github.com/mongodb-labs/django-mongodb/issues/8
    supports_json_field = False
    # BSON Date type doesn't support microsecond precision.
    supports_microsecond_precision = False
    # MongoDB stores datetimes in UTC.
    supports_timezones = False
    # Not implemented: https://github.com/mongodb-labs/django-mongodb/issues/7
    supports_transactions = False
    uses_savepoints = False

    _django_test_expected_failures = {
        # Database defaults not supported: bson.errors.InvalidDocument:
        # cannot encode object: <django.db.models.expressions.DatabaseDefault
        "basic.tests.ModelInstanceCreationTests.test_save_primary_with_db_default",
        # 'NulledTransform' object has no attribute 'as_mql'.
        "lookup.tests.LookupTests.test_exact_none_transform",
        # "Save with update_fields did not affect any rows."
        "basic.tests.SelectOnSaveTests.test_select_on_save_lying_update",
        # Slicing with QuerySet.count() doesn't work.
        "lookup.tests.LookupTests.test_count",
        # Lookup in order_by() not supported:
        # argument of type '<database function>' is not iterable
        "db_functions.comparison.test_coalesce.CoalesceTests.test_ordering",
        "db_functions.tests.FunctionTests.test_nested_function_ordering",
        "db_functions.text.test_length.LengthTests.test_ordering",
        "db_functions.text.test_strindex.StrIndexTests.test_order_by",
        "lookup.tests.LookupQueryingTests.test_lookup_in_order_by",
        # annotate() after values() doesn't raise NotSupportedError.
        "lookup.tests.LookupTests.test_exact_query_rhs_with_selected_columns",
        # tuple index out of range in process_rhs()
        "lookup.tests.LookupTests.test_exact_sliced_queryset_limit_one",
        "lookup.tests.LookupTests.test_exact_sliced_queryset_limit_one_offset",
        # Regex lookup doesn't work on non-string fields.
        "lookup.tests.LookupTests.test_regex_non_string",
        # Substr not implemented.
        "lookup.tests.LookupTests.test_pattern_lookups_with_substr",
        # Querying ObjectID with string doesn't work.
        "lookup.tests.LookupTests.test_lookup_int_as_str",
        # MongoDB gives the wrong result of log(number, base) when base is a
        # fractional Decimal: https://jira.mongodb.org/browse/SERVER-91223
        "db_functions.math.test_log.LogTests.test_decimal",
        # MongoDB gives ROUND(365, -1)=360 instead of 370 like other databases.
        "db_functions.math.test_round.RoundTests.test_integer_with_negative_precision",
        # Truncating in another timezone doesn't work becauase MongoDB converts
        # the result back to UTC.
        "db_functions.datetime.test_extract_trunc.DateFunctionWithTimeZoneTests.test_trunc_func_with_timezone",
        "db_functions.datetime.test_extract_trunc.DateFunctionWithTimeZoneTests.test_trunc_timezone_applied_before_truncation",
        # pk__in=queryset doesn't work because subqueries aren't a thing in
        # MongoDB.
        "annotations.tests.NonAggregateAnnotationTestCase.test_annotation_and_alias_filter_in_subquery",
        # Length of null considered zero rather than null.
        "db_functions.text.test_length.LengthTests.test_basic",
    }
    # $bitAnd, #bitOr, and $bitXor are new in MongoDB 6.3.
    _django_test_expected_failures_bitwise = {
        "expressions.tests.ExpressionOperatorTests.test_lefthand_bitwise_and",
        "expressions.tests.ExpressionOperatorTests.test_lefthand_bitwise_or",
        "expressions.tests.ExpressionOperatorTests.test_lefthand_bitwise_xor",
        "expressions.tests.ExpressionOperatorTests.test_lefthand_bitwise_xor_null",
        "expressions.tests.ExpressionOperatorTests.test_lefthand_bitwise_xor_right_null",
        "expressions.tests.ExpressionOperatorTests.test_lefthand_transformed_field_bitwise_or",
    }

    @cached_property
    def django_test_expected_failures(self):
        expected_failures = super().django_test_expected_failures
        expected_failures.update(self._django_test_expected_failures)
        if not self.is_mongodb_6_3:
            expected_failures.update(self._django_test_expected_failures_bitwise)
        return expected_failures

    django_test_skips = {
        "Insert expressions aren't supported.": {
            "bulk_create.tests.BulkCreateTests.test_bulk_insert_now",
            "bulk_create.tests.BulkCreateTests.test_bulk_insert_expressions",
            # PI()
            "db_functions.math.test_round.RoundTests.test_decimal_with_precision",
            "db_functions.math.test_round.RoundTests.test_float_with_precision",
        },
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
            "annotations.tests.AliasTests.test_update_with_alias",
            "annotations.tests.NonAggregateAnnotationTestCase.test_update_with_annotation",
            "db_functions.comparison.test_least.LeastTests.test_update",
            "db_functions.comparison.test_greatest.GreatestTests.test_update",
            "db_functions.text.test_left.LeftTests.test_basic",
            "db_functions.text.test_lower.LowerTests.test_basic",
            "db_functions.text.test_replace.ReplaceTests.test_update",
            "db_functions.text.test_substr.SubstrTests.test_basic",
            "db_functions.text.test_upper.UpperTests.test_basic",
            "model_fields.test_integerfield.PositiveIntegerFieldTests.test_negative_values",
            "timezones.tests.NewDatabaseTests.test_update_with_timedelta",
            "update.tests.AdvancedTests.test_update_annotated_queryset",
            "update.tests.AdvancedTests.test_update_negated_f",
            "update.tests.AdvancedTests.test_update_negated_f_conditional_annotation",
            "update.tests.AdvancedTests.test_update_transformed_field",
        },
        "AutoField not supported.": {
            "bulk_create.tests.BulkCreateTests.test_bulk_insert_nullable_fields",
            "lookup.tests.LookupTests.test_in_ignore_none_with_unhashable_items",
            "model_fields.test_autofield.AutoFieldTests",
            "model_fields.test_autofield.BigAutoFieldTests",
            "model_fields.test_autofield.SmallAutoFieldTests",
        },
        "QuerySet.select_related() not supported.": {
            "annotations.tests.AliasTests.test_joined_alias_annotation",
            "annotations.tests.NonAggregateAnnotationTestCase.test_joined_annotation",
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
            "db_functions.comparison.test_cast.CastTests.test_cast_to_integer_foreign_key",
            "model_fields.test_foreignkey.ForeignKeyTests.test_to_python",
        },
        # https://github.com/mongodb-labs/django-mongodb/issues/12
        "QuerySet.aggregate() not supported.": {
            "annotations.tests.AliasTests.test_filter_alias_agg_with_double_f",
            "annotations.tests.NonAggregateAnnotationTestCase.test_aggregate_over_annotation",
            "annotations.tests.NonAggregateAnnotationTestCase.test_aggregate_over_full_expression_annotation",
            "annotations.tests.NonAggregateAnnotationTestCase.test_annotation_exists_aggregate_values_chaining",
            "annotations.tests.NonAggregateAnnotationTestCase.test_annotation_in_f_grouped_by_annotation",
            "annotations.tests.NonAggregateAnnotationTestCase.test_annotation_subquery_and_aggregate_values_chaining",
            "annotations.tests.NonAggregateAnnotationTestCase.test_filter_agg_with_double_f",
            "lookup.tests.LookupQueryingTests.test_aggregate_combined_lookup",
            "from_db_value.tests.FromDBValueTest.test_aggregation",
            "timezones.tests.LegacyDatabaseTests.test_query_aggregation",
            "timezones.tests.NewDatabaseTests.test_query_aggregation",
        },
        "QuerySet.annotate() has some limitations.": {
            # Exists not supported.
            "annotations.tests.NonAggregateAnnotationTestCase.test_annotation_exists_none_query",
            "lookup.tests.LookupTests.test_exact_exists",
            "lookup.tests.LookupTests.test_nested_outerref_lhs",
            "lookup.tests.LookupQueryingTests.test_filter_exists_lhs",
            # annotate() with combined expressions doesn't work:
            # 'WhereNode' object has no attribute 'field'
            "lookup.tests.LookupQueryingTests.test_combined_annotated_lookups_in_filter",
            "lookup.tests.LookupQueryingTests.test_combined_annotated_lookups_in_filter_false",
            "lookup.tests.LookupQueryingTests.test_combined_lookups",
            # Case not supported.
            "lookup.tests.LookupQueryingTests.test_conditional_expression",
            # Subquery not supported.
            "annotations.tests.NonAggregateAnnotationTestCase.test_empty_queryset_annotation",
            "db_functions.comparison.test_coalesce.CoalesceTests.test_empty_queryset",
            "db_functions.datetime.test_extract_trunc.DateFunctionTests.test_extract_outerref",
            "db_functions.datetime.test_extract_trunc.DateFunctionTests.test_trunc_subquery_with_parameters",
            "lookup.tests.LookupQueryingTests.test_filter_subquery_lhs",
            # Invalid $project :: caused by :: Unknown expression $count,
            "annotations.tests.NonAggregateAnnotationTestCase.test_combined_expression_annotation_with_aggregation",
            "annotations.tests.NonAggregateAnnotationTestCase.test_combined_f_expression_annotation_with_aggregation",
            "annotations.tests.NonAggregateAnnotationTestCase.test_full_expression_annotation_with_aggregation",
            "annotations.tests.NonAggregateAnnotationTestCase.test_grouping_by_q_expression_annotation",
            "annotations.tests.NonAggregateAnnotationTestCase.test_q_expression_annotation_with_aggregation",
            # Func not implemented.
            "annotations.tests.NonAggregateAnnotationTestCase.test_custom_functions",
            "annotations.tests.NonAggregateAnnotationTestCase.test_custom_functions_can_ref_other_functions",
            # BaseDatabaseOperations may require a format_for_duration_arithmetic().
            "annotations.tests.NonAggregateAnnotationTestCase.test_mixed_type_annotation_date_interval",
            # FieldDoesNotExist with ordering.
            "annotations.tests.AliasTests.test_order_by_alias",
            "annotations.tests.NonAggregateAnnotationTestCase.test_order_by_aggregate",
            "annotations.tests.NonAggregateAnnotationTestCase.test_order_by_annotation",
            "expressions.tests.NegatedExpressionTests.test_filter",
            # annotate().filter().count() gives incorrect results.
            "db_functions.datetime.test_extract_trunc.DateFunctionTests.test_extract_year_exact_lookup",
        },
        "Count doesn't work in QuerySet.annotate()": {
            "annotations.tests.AliasTests.test_alias_annotate_with_aggregation",
            "annotations.tests.AliasTests.test_order_by_alias_aggregate",
            "annotations.tests.NonAggregateAnnotationTestCase.test_annotate_exists",
            "annotations.tests.NonAggregateAnnotationTestCase.test_annotate_with_aggregation",
            "db_functions.comparison.test_cast.CastTests.test_cast_from_db_datetime_to_date_group_by",
        },
        "QuerySet.dates() is not supported on MongoDB.": {
            "annotations.tests.AliasTests.test_dates_alias",
            "dates.tests.DatesTests.test_dates_trunc_datetime_fields",
            "dates.tests.DatesTests.test_related_model_traverse",
        },
        "QuerySet.datetimes() is not supported on MongoDB.": {
            "annotations.tests.AliasTests.test_datetimes_alias",
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
            "annotations.tests.NonAggregateAnnotationTestCase.test_column_field_ordering",
            "annotations.tests.NonAggregateAnnotationTestCase.test_column_field_ordering_with_deferred",
            "basic.tests.ModelTest.test_extra_method_select_argument_with_dashes",
            "basic.tests.ModelTest.test_extra_method_select_argument_with_dashes_and_values",
            "defer.tests.DeferTests.test_defer_extra",
            "lookup.tests.LookupTests.test_values",
            "lookup.tests.LookupTests.test_values_list",
        },
        "Queries with multiple tables are not supported.": {
            "annotations.tests.AliasTests.test_alias_default_alias_expression",
            "annotations.tests.NonAggregateAnnotationTestCase.test_annotation_aggregate_with_m2o",
            "annotations.tests.NonAggregateAnnotationTestCase.test_annotation_and_alias_filter_related_in_subquery",
            "annotations.tests.NonAggregateAnnotationTestCase.test_annotation_filter_with_subquery",
            "annotations.tests.NonAggregateAnnotationTestCase.test_annotation_reverse_m2m",
            "annotations.tests.NonAggregateAnnotationTestCase.test_joined_transformed_annotation",
            "annotations.tests.NonAggregateAnnotationTestCase.test_mti_annotations",
            "annotations.tests.NonAggregateAnnotationTestCase.test_values_with_pk_annotation",
            "annotations.tests.NonAggregateAnnotationTestCase.test_annotation_subquery_outerref_transform",
            "annotations.tests.NonAggregateAnnotationTestCase.test_annotation_with_m2m",
            "annotations.tests.NonAggregateAnnotationTestCase.test_chaining_annotation_filter_with_m2m",
            "db_functions.comparison.test_least.LeastTests.test_related_field",
            "db_functions.comparison.test_greatest.GreatestTests.test_related_field",
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
            "lookup.test_decimalfield.DecimalFieldLookupTests",
            "lookup.tests.LookupQueryingTests.test_multivalued_join_reuse",
            "lookup.tests.LookupTests.test_filter_by_reverse_related_field_transform",
            "lookup.tests.LookupTests.test_lookup_collision",
            "lookup.tests.LookupTests.test_lookup_rhs",
            "lookup.tests.LookupTests.test_isnull_non_boolean_value",
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
        "Test inspects query for SQL": {
            "lookup.tests.LookupTests.test_in_ignore_none",
            "lookup.tests.LookupTests.test_textfield_exact_null",
        },
        "Test executes raw SQL.": {
            "annotations.tests.NonAggregateAnnotationTestCase.test_raw_sql_with_inherited_field",
            "timezones.tests.LegacyDatabaseTests.test_cursor_execute_accepts_naive_datetime",
            "timezones.tests.LegacyDatabaseTests.test_cursor_execute_returns_naive_datetime",
            "timezones.tests.LegacyDatabaseTests.test_raw_sql",
            "timezones.tests.NewDatabaseTests.test_cursor_execute_accepts_naive_datetime",
            "timezones.tests.NewDatabaseTests.test_cursor_execute_returns_naive_datetime",
            "timezones.tests.NewDatabaseTests.test_cursor_explicit_time_zone",
            "timezones.tests.NewDatabaseTests.test_raw_sql",
        },
        "Bilateral transform not implemented.": {
            "db_functions.tests.FunctionTests.test_func_transform_bilateral",
            "db_functions.tests.FunctionTests.test_func_transform_bilateral_multivalue",
        },
        "MongoDB does not support this database function.": {
            "db_functions.datetime.test_now.NowTests",
            "db_functions.math.test_sign.SignTests",
            "db_functions.text.test_chr.ChrTests",
            "db_functions.text.test_md5.MD5Tests",
            "db_functions.text.test_ord.OrdTests",
            "db_functions.text.test_pad.PadTests",
            "db_functions.text.test_repeat.RepeatTests",
            "db_functions.text.test_reverse.ReverseTests",
            "db_functions.text.test_right.RightTests",
            "db_functions.text.test_sha1.SHA1Tests",
            "db_functions.text.test_sha224.SHA224Tests",
            "db_functions.text.test_sha256.SHA256Tests",
            "db_functions.text.test_sha384.SHA384Tests",
            "db_functions.text.test_sha512.SHA512Tests",
        },
        "ExtractQuarter database function not supported.": {
            "db_functions.datetime.test_extract_trunc.DateFunctionTests.test_extract_quarter_func",
            "db_functions.datetime.test_extract_trunc.DateFunctionTests.test_extract_quarter_func_boundaries",
        },
        "TruncDate database function not supported.": {
            "db_functions.datetime.test_extract_trunc.DateFunctionTests.test_trunc_date_func",
            "db_functions.datetime.test_extract_trunc.DateFunctionTests.test_trunc_date_none",
            "db_functions.datetime.test_extract_trunc.DateFunctionTests.test_trunc_lookup_name_sql_injection",
            "model_fields.test_datetimefield.DateTimeFieldTests.test_lookup_date_with_use_tz",
            "model_fields.test_datetimefield.DateTimeFieldTests.test_lookup_date_without_use_tz",
            "timezones.tests.NewDatabaseTests.test_query_convert_timezones",
        },
        "TruncTime database function not supported.": {
            "db_functions.datetime.test_extract_trunc.DateFunctionTests.test_trunc_time_comparison",
            "db_functions.datetime.test_extract_trunc.DateFunctionTests.test_trunc_time_func",
            "db_functions.datetime.test_extract_trunc.DateFunctionTests.test_trunc_time_none",
        },
        "MongoDB can't annotate ($project) a function like PI().": {
            "db_functions.math.test_pi.PiTests.test",
        },
        "Can't cast from date to datetime without MongoDB interpreting the new value in UTC.": {
            "db_functions.comparison.test_cast.CastTests.test_cast_from_db_date_to_datetime",
            "db_functions.comparison.test_cast.CastTests.test_cast_from_db_datetime_to_time",
        },
        "Casting Python literals doesn't work.": {
            "db_functions.comparison.test_cast.CastTests.test_cast_from_python",
            "db_functions.comparison.test_cast.CastTests.test_cast_from_python_to_date",
            "db_functions.comparison.test_cast.CastTests.test_cast_from_python_to_datetime",
            "db_functions.comparison.test_cast.CastTests.test_cast_to_duration",
        },
    }

    @cached_property
    def is_mongodb_6_3(self):
        return self.connection.get_database_version() >= (6, 3)
