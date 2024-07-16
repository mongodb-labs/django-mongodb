from django.db.backends.base.features import BaseDatabaseFeatures
from django.utils.functional import cached_property


class DatabaseFeatures(BaseDatabaseFeatures):
    greatest_least_ignores_nulls = True
    has_json_object_function = False
    has_native_json_field = True
    supports_date_lookup_using_string = False
    supports_foreign_keys = False
    supports_ignore_conflicts = False
    supports_json_field_contains = False
    # BSON Date type doesn't support microsecond precision.
    supports_microsecond_precision = False
    supports_temporal_subtraction = True
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
        # Lookup in order_by() not supported:
        # argument of type '<database function>' is not iterable
        "db_functions.comparison.test_coalesce.CoalesceTests.test_ordering",
        "db_functions.tests.FunctionTests.test_nested_function_ordering",
        "db_functions.text.test_length.LengthTests.test_ordering",
        "db_functions.text.test_strindex.StrIndexTests.test_order_by",
        "expressions.tests.BasicExpressionsTests.test_order_by_exists",
        "expressions.tests.BasicExpressionsTests.test_order_by_multiline_sql",
        "expressions_case.tests.CaseExpressionTests.test_order_by_conditional_explicit",
        "lookup.tests.LookupQueryingTests.test_lookup_in_order_by",
        "ordering.tests.OrderingTests.test_default_ordering",
        "ordering.tests.OrderingTests.test_default_ordering_by_f_expression",
        "ordering.tests.OrderingTests.test_default_ordering_does_not_affect_group_by",
        "ordering.tests.OrderingTests.test_order_by_constant_value",
        "ordering.tests.OrderingTests.test_order_by_expr_query_reuse",
        "ordering.tests.OrderingTests.test_order_by_expression_ref",
        "ordering.tests.OrderingTests.test_order_by_f_expression",
        "ordering.tests.OrderingTests.test_order_by_f_expression_duplicates",
        "ordering.tests.OrderingTests.test_order_by_fk_attname",
        "ordering.tests.OrderingTests.test_order_by_nulls_first",
        "ordering.tests.OrderingTests.test_order_by_nulls_last",
        "ordering.tests.OrderingTests.test_ordering_select_related_collision",
        "ordering.tests.OrderingTests.test_order_by_self_referential_fk",
        "ordering.tests.OrderingTests.test_orders_nulls_first_on_filtered_subquery",
        "ordering.tests.OrderingTests.test_related_ordering_duplicate_table_reference",
        "ordering.tests.OrderingTests.test_reverse_ordering_pure",
        "ordering.tests.OrderingTests.test_reverse_meta_ordering_pure",
        "ordering.tests.OrderingTests.test_reversed_ordering",
        "update.tests.AdvancedTests.test_update_ordered_by_inline_m2m_annotation",
        "update.tests.AdvancedTests.test_update_ordered_by_m2m_annotation",
        "update.tests.AdvancedTests.test_update_ordered_by_m2m_annotation_desc",
        # 'ManyToOneRel' object has no attribute 'column'
        "m2m_through.tests.M2mThroughTests.test_order_by_relational_field_through_model",
        # pymongo: ValueError: update cannot be empty
        "update.tests.SimpleTest.test_empty_update_with_inheritance",
        "update.tests.SimpleTest.test_nonempty_update_with_inheritance",
        # Pattern lookups that use regexMatch don't work on JSONField:
        # Unsupported conversion from array to string in $convert
        "model_fields.test_jsonfield.TestQuerying.test_icontains",
        # MongoDB gives the wrong result of log(number, base) when base is a
        # fractional Decimal: https://jira.mongodb.org/browse/SERVER-91223
        "db_functions.math.test_log.LogTests.test_decimal",
        # MongoDB gives ROUND(365, -1)=360 instead of 370 like other databases.
        "db_functions.math.test_round.RoundTests.test_integer_with_negative_precision",
        # Truncating in another timezone doesn't work becauase MongoDB converts
        # the result back to UTC.
        "db_functions.datetime.test_extract_trunc.DateFunctionWithTimeZoneTests.test_trunc_func_with_timezone",
        "db_functions.datetime.test_extract_trunc.DateFunctionWithTimeZoneTests.test_trunc_timezone_applied_before_truncation",
        # Length of null considered zero rather than null.
        "db_functions.text.test_length.LengthTests.test_basic",
        # Key transforms are incorrectly treated as joins:
        # Ordering can't span tables on MongoDB (value_custom__a).
        "model_fields.test_jsonfield.TestQuerying.test_order_grouping_custom_decoder",
        "model_fields.test_jsonfield.TestQuerying.test_ordering_by_transform",
        "model_fields.test_jsonfield.TestQuerying.test_ordering_grouping_by_key_transform",
        # DecimalField lookup with F expression crashes:
        # decimal.InvalidOperation: [<class 'decimal.ConversionSyntax'>]
        "lookup.tests.LookupTests.test_lookup_rhs",
        # Wrong results in queries with multiple tables.
        "annotations.tests.NonAggregateAnnotationTestCase.test_annotation_aggregate_with_m2o",
        "annotations.tests.NonAggregateAnnotationTestCase.test_annotation_reverse_m2m",
        "annotations.tests.NonAggregateAnnotationTestCase.test_annotation_with_m2m",
        "annotations.tests.NonAggregateAnnotationTestCase.test_chaining_annotation_filter_with_m2m",
        "annotations.tests.NonAggregateAnnotationTestCase.test_mti_annotations",
        "lookup.tests.LookupTests.test_lookup_collision",
        "expressions.test_queryset_values.ValuesExpressionsTests.test_values_list_expression",
        "expressions.test_queryset_values.ValuesExpressionsTests.test_values_list_expression_flat",
        "expressions.tests.IterableLookupInnerExpressionsTests.test_expressions_in_lookups_join_choice",
        "expressions_case.tests.CaseExpressionTests.test_join_promotion",
        "expressions_case.tests.CaseExpressionTests.test_join_promotion_multiple_annotations",
        "ordering.tests.OrderingTests.test_order_by_grandparent_fk_with_expression_in_default_ordering",
        "ordering.tests.OrderingTests.test_order_by_parent_fk_with_expression_in_default_ordering",
        "ordering.tests.OrderingTests.test_order_by_ptr_field_with_default_ordering_by_expression",
        # alias().order_by() doesn't work.
        "annotations.tests.AliasTests.test_order_by_alias",
        "annotations.tests.AliasTests.test_order_by_alias_aggregate",
        # annotate() + values_list() + order_by() loses annotated value.
        "expressions_case.tests.CaseExpressionTests.test_annotate_values_not_in_order_by",
        # Querying the reverse side of a foreign key for None returns no
        # results: https://github.com/mongodb-labs/django-mongodb/issues/76
        "one_to_one.tests.OneToOneTests.test_filter_one_to_one_relations",
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
            "expressions.tests.BasicExpressionsTests.test_new_object_create",
            "expressions.tests.BasicExpressionsTests.test_new_object_save",
            "expressions.tests.BasicExpressionsTests.test_object_create_with_aggregate",
            "expressions.tests.BasicExpressionsTests.test_object_create_with_f_expression_in_subquery",
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
            "expressions.tests.BasicExpressionsTests.test_arithmetic",
            "expressions.tests.BasicExpressionsTests.test_filter_with_join",
            "expressions.tests.BasicExpressionsTests.test_object_update",
            "expressions.tests.BasicExpressionsTests.test_object_update_unsaved_objects",
            "expressions.tests.BasicExpressionsTests.test_order_of_operations",
            "expressions.tests.BasicExpressionsTests.test_parenthesis_priority",
            "expressions.tests.BasicExpressionsTests.test_update",
            "expressions.tests.BasicExpressionsTests.test_update_with_fk",
            "expressions.tests.BasicExpressionsTests.test_update_with_none",
            "expressions.tests.ExpressionsNumericTests.test_decimal_expression",
            "expressions.tests.ExpressionsNumericTests.test_increment_value",
            "expressions.tests.FTimeDeltaTests.test_delta_update",
            "expressions.tests.FTimeDeltaTests.test_negative_timedelta_update",
            "expressions.tests.ValueTests.test_update_TimeField_using_Value",
            "expressions.tests.ValueTests.test_update_UUIDField_using_Value",
            "expressions_case.tests.CaseDocumentationExamples.test_conditional_update_example",
            "expressions_case.tests.CaseExpressionTests.test_update",
            "expressions_case.tests.CaseExpressionTests.test_update_big_integer",
            "expressions_case.tests.CaseExpressionTests.test_update_binary",
            "expressions_case.tests.CaseExpressionTests.test_update_boolean",
            "expressions_case.tests.CaseExpressionTests.test_update_date",
            "expressions_case.tests.CaseExpressionTests.test_update_date_time",
            "expressions_case.tests.CaseExpressionTests.test_update_decimal",
            "expressions_case.tests.CaseExpressionTests.test_update_duration",
            "expressions_case.tests.CaseExpressionTests.test_update_email",
            "expressions_case.tests.CaseExpressionTests.test_update_file",
            "expressions_case.tests.CaseExpressionTests.test_update_file_path",
            "expressions_case.tests.CaseExpressionTests.test_update_fk",
            "expressions_case.tests.CaseExpressionTests.test_update_float",
            "expressions_case.tests.CaseExpressionTests.test_update_generic_ip_address",
            "expressions_case.tests.CaseExpressionTests.test_update_image",
            "expressions_case.tests.CaseExpressionTests.test_update_null_boolean",
            "expressions_case.tests.CaseExpressionTests.test_update_positive_big_integer",
            "expressions_case.tests.CaseExpressionTests.test_update_positive_integer",
            "expressions_case.tests.CaseExpressionTests.test_update_positive_small_integer",
            "expressions_case.tests.CaseExpressionTests.test_update_slug",
            "expressions_case.tests.CaseExpressionTests.test_update_small_integer",
            "expressions_case.tests.CaseExpressionTests.test_update_string",
            "expressions_case.tests.CaseExpressionTests.test_update_text",
            "expressions_case.tests.CaseExpressionTests.test_update_time",
            "expressions_case.tests.CaseExpressionTests.test_update_url",
            "expressions_case.tests.CaseExpressionTests.test_update_uuid",
            "expressions_case.tests.CaseExpressionTests.test_update_with_expression_as_condition",
            "expressions_case.tests.CaseExpressionTests.test_update_with_expression_as_value",
            "expressions_case.tests.CaseExpressionTests.test_update_without_default",
            "model_fields.test_integerfield.PositiveIntegerFieldTests.test_negative_values",
            "timezones.tests.NewDatabaseTests.test_update_with_timedelta",
            "update.tests.AdvancedTests.test_update_annotated_queryset",
            "update.tests.AdvancedTests.test_update_negated_f",
            "update.tests.AdvancedTests.test_update_negated_f_conditional_annotation",
            "update.tests.AdvancedTests.test_update_transformed_field",
        },
        "AutoField not supported.": {
            "bulk_create.tests.BulkCreateTests.test_bulk_insert_nullable_fields",
            "lookup.tests.LookupTests.test_filter_by_reverse_related_field_transform",
            "lookup.tests.LookupTests.test_in_ignore_none_with_unhashable_items",
            "model_fields.test_autofield.AutoFieldTests",
            "model_fields.test_autofield.BigAutoFieldTests",
            "model_fields.test_autofield.SmallAutoFieldTests",
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
            "annotations.tests.AliasTests.test_alias_default_alias_expression",
            "annotations.tests.AliasTests.test_filter_alias_agg_with_double_f",
            "annotations.tests.NonAggregateAnnotationTestCase.test_aggregate_over_annotation",
            "annotations.tests.NonAggregateAnnotationTestCase.test_aggregate_over_full_expression_annotation",
            "annotations.tests.NonAggregateAnnotationTestCase.test_annotation_exists_aggregate_values_chaining",
            "annotations.tests.NonAggregateAnnotationTestCase.test_annotation_in_f_grouped_by_annotation",
            "annotations.tests.NonAggregateAnnotationTestCase.test_annotation_subquery_and_aggregate_values_chaining",
            "annotations.tests.NonAggregateAnnotationTestCase.test_filter_agg_with_double_f",
            "annotations.tests.NonAggregateAnnotationTestCase.test_values_with_pk_annotation",
            "expressions.test_queryset_values.ValuesExpressionsTests.test_chained_values_with_expression",
            "expressions.test_queryset_values.ValuesExpressionsTests.test_values_expression_group_by",
            "expressions.tests.BasicExpressionsTests.test_annotate_values_aggregate",
            "expressions_case.tests.CaseExpressionTests.test_aggregate",
            "expressions_case.tests.CaseExpressionTests.test_aggregate_with_expression_as_condition",
            "expressions_case.tests.CaseExpressionTests.test_aggregate_with_expression_as_value",
            "expressions_case.tests.CaseExpressionTests.test_aggregation_empty_cases",
            "expressions_case.tests.CaseExpressionTests.test_annotate_with_aggregation_in_condition",
            "expressions_case.tests.CaseExpressionTests.test_annotate_with_aggregation_in_predicate",
            "expressions_case.tests.CaseExpressionTests.test_annotate_with_aggregation_in_value",
            "expressions_case.tests.CaseExpressionTests.test_annotate_with_in_clause",
            "expressions_case.tests.CaseExpressionTests.test_filter_with_aggregation_in_condition",
            "expressions_case.tests.CaseExpressionTests.test_filter_with_aggregation_in_predicate",
            "expressions_case.tests.CaseExpressionTests.test_filter_with_aggregation_in_value",
            "expressions_case.tests.CaseExpressionTests.test_m2m_exclude",
            "expressions_case.tests.CaseExpressionTests.test_m2m_reuse",
            "lookup.test_decimalfield.DecimalFieldLookupTests",
            "lookup.tests.LookupQueryingTests.test_aggregate_combined_lookup",
            "from_db_value.tests.FromDBValueTest.test_aggregation",
            "timezones.tests.LegacyDatabaseTests.test_query_aggregation",
            "timezones.tests.LegacyDatabaseTests.test_query_annotation",
            "timezones.tests.NewDatabaseTests.test_query_aggregation",
            "timezones.tests.NewDatabaseTests.test_query_annotation",
        },
        "Exists is not supported on MongoDB.": {
            "annotations.tests.NonAggregateAnnotationTestCase.test_annotation_exists_none_query",
            "expressions.tests.BasicExpressionsTests.test_annotation_with_deeply_nested_outerref",
            "expressions.tests.BasicExpressionsTests.test_boolean_expression_combined",
            "expressions.tests.BasicExpressionsTests.test_boolean_expression_combined_with_empty_Q",
            "expressions.tests.BasicExpressionsTests.test_boolean_expression_in_Q",
            "expressions.tests.BasicExpressionsTests.test_case_in_filter_if_boolean_output_field",
            "expressions.tests.BasicExpressionsTests.test_exists_in_filter",
            "expressions.tests.BasicExpressionsTests.test_subquery",
            "expressions.tests.ExistsTests.test_filter_by_empty_exists",
            "expressions.tests.ExistsTests.test_negated_empty_exists",
            "expressions.tests.ExistsTests.test_optimizations",
            "expressions.tests.ExistsTests.test_select_negated_empty_exists",
            "lookup.tests.LookupTests.test_exact_exists",
            "lookup.tests.LookupTests.test_nested_outerref_lhs",
            "lookup.tests.LookupQueryingTests.test_filter_exists_lhs",
        },
        "Subquery is not supported on MongoDB.": {
            "annotations.tests.NonAggregateAnnotationTestCase.test_annotation_filter_with_subquery",
            "annotations.tests.NonAggregateAnnotationTestCase.test_annotation_subquery_outerref_transform",
            "annotations.tests.NonAggregateAnnotationTestCase.test_empty_queryset_annotation",
            "db_functions.datetime.test_extract_trunc.DateFunctionTests.test_extract_outerref",
            "db_functions.datetime.test_extract_trunc.DateFunctionTests.test_trunc_subquery_with_parameters",
            "expressions.tests.BasicExpressionsTests.test_annotation_with_nested_outerref",
            "expressions.tests.BasicExpressionsTests.test_annotation_with_outerref",
            "expressions.tests.BasicExpressionsTests.test_annotations_within_subquery",
            "expressions.tests.BasicExpressionsTests.test_in_subquery",
            "expressions.tests.BasicExpressionsTests.test_nested_outerref_with_function",
            "expressions.tests.BasicExpressionsTests.test_nested_subquery",
            "expressions.tests.BasicExpressionsTests.test_nested_subquery_join_outer_ref",
            "expressions.tests.BasicExpressionsTests.test_nested_subquery_outer_ref_2",
            "expressions.tests.BasicExpressionsTests.test_nested_subquery_outer_ref_with_autofield",
            "expressions.tests.BasicExpressionsTests.test_outerref_mixed_case_table_name",
            "expressions.tests.BasicExpressionsTests.test_outerref_with_operator",
            "expressions.tests.BasicExpressionsTests.test_subquery_filter_by_aggregate",
            "expressions.tests.BasicExpressionsTests.test_subquery_filter_by_lazy",
            "expressions.tests.BasicExpressionsTests.test_subquery_group_by_outerref_in_filter",
            "expressions.tests.BasicExpressionsTests.test_subquery_in_filter",
            "expressions.tests.BasicExpressionsTests.test_subquery_references_joined_table_twice",
            "expressions.tests.BasicExpressionsTests.test_uuid_pk_subquery",
            "lookup.tests.LookupQueryingTests.test_filter_subquery_lhs",
            "model_fields.test_jsonfield.TestQuerying.test_nested_key_transform_on_subquery",
            "model_fields.test_jsonfield.TestQuerying.test_obj_subquery_lookup",
        },
        "Using a QuerySet in annotate() is not supported on MongoDB.": {
            "annotations.tests.NonAggregateAnnotationTestCase.test_annotation_and_alias_filter_in_subquery",
            "annotations.tests.NonAggregateAnnotationTestCase.test_annotation_and_alias_filter_related_in_subquery",
            "annotations.tests.NonAggregateAnnotationTestCase.test_empty_expression_annotation",
            "db_functions.comparison.test_coalesce.CoalesceTests.test_empty_queryset",
            "expressions.tests.FTimeDeltaTests.test_date_subquery_subtraction",
            "expressions.tests.FTimeDeltaTests.test_datetime_subquery_subtraction",
            "expressions.tests.FTimeDeltaTests.test_time_subquery_subtraction",
            "expressions_case.tests.CaseExpressionTests.test_in_subquery",
            "lookup.tests.LookupTests.test_exact_query_rhs_with_selected_columns",
            "lookup.tests.LookupTests.test_exact_sliced_queryset_limit_one",
            "lookup.tests.LookupTests.test_exact_sliced_queryset_limit_one_offset",
            "lookup.tests.LookupTests.test_in_different_database",
            "model_fields.test_jsonfield.TestQuerying.test_usage_in_subquery",
            "one_to_one.tests.OneToOneTests.test_get_prefetch_queryset_warning",
            "one_to_one.tests.OneToOneTests.test_rel_pk_subquery",
        },
        # Invalid $project :: caused by :: Unknown expression $count
        # https://github.com/mongodb-labs/django-mongodb/issues/79
        "Count() in QuerySet.annotate() crashes.": {
            "annotations.tests.AliasTests.test_alias_annotate_with_aggregation",
            "annotations.tests.NonAggregateAnnotationTestCase.test_annotate_exists",
            "annotations.tests.NonAggregateAnnotationTestCase.test_annotate_with_aggregation",
            "annotations.tests.NonAggregateAnnotationTestCase.test_combined_expression_annotation_with_aggregation",
            "annotations.tests.NonAggregateAnnotationTestCase.test_combined_f_expression_annotation_with_aggregation",
            "annotations.tests.NonAggregateAnnotationTestCase.test_full_expression_annotation_with_aggregation",
            "annotations.tests.NonAggregateAnnotationTestCase.test_grouping_by_q_expression_annotation",
            "annotations.tests.NonAggregateAnnotationTestCase.test_order_by_aggregate",
            "annotations.tests.NonAggregateAnnotationTestCase.test_q_expression_annotation_with_aggregation",
            "db_functions.comparison.test_cast.CastTests.test_cast_from_db_datetime_to_date_group_by",
            "defer_regress.tests.DeferRegressionTest.test_basic",
            "defer_regress.tests.DeferRegressionTest.test_defer_annotate_select_related",
            "defer_regress.tests.DeferRegressionTest.test_ticket_16409",
            "expressions.tests.BasicExpressionsTests.test_aggregate_subquery_annotation",
            "expressions.tests.FieldTransformTests.test_month_aggregation",
            "expressions_case.tests.CaseDocumentationExamples.test_conditional_aggregation_example",
            "model_fields.test_jsonfield.TestQuerying.test_ordering_grouping_by_count",
        },
        "Cannot use QuerySet.delete() when querying across multiple collections on MongoDB.": {
            "one_to_one.tests.OneToOneTests.test_o2o_primary_key_delete",
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
            "ordering.tests.OrderingTests.test_extra_ordering",
            "ordering.tests.OrderingTests.test_extra_ordering_quoting",
            "ordering.tests.OrderingTests.test_extra_ordering_with_table_name",
            "select_related.tests.SelectRelatedTests.test_select_related_with_extra",
        },
        "QuerySet.update() crash: Unrecognized expression '$count'": {
            "update.tests.AdvancedTests.test_update_annotated_multi_table_queryset",
        },
        "Test inspects query for SQL": {
            "lookup.tests.LookupTests.test_in_ignore_none",
            "lookup.tests.LookupTests.test_textfield_exact_null",
        },
        "Test executes raw SQL.": {
            "annotations.tests.NonAggregateAnnotationTestCase.test_raw_sql_with_inherited_field",
            "expressions.tests.BasicExpressionsTests.test_annotate_values_filter",
            "expressions.tests.BasicExpressionsTests.test_filtering_on_rawsql_that_is_boolean",
            "model_fields.test_jsonfield.TestQuerying.test_key_sql_injection_escape",
            "model_fields.test_jsonfield.TestQuerying.test_key_transform_raw_expression",
            "model_fields.test_jsonfield.TestQuerying.test_nested_key_transform_raw_expression",
            "timezones.tests.LegacyDatabaseTests.test_cursor_execute_accepts_naive_datetime",
            "timezones.tests.LegacyDatabaseTests.test_cursor_execute_returns_naive_datetime",
            "timezones.tests.LegacyDatabaseTests.test_raw_sql",
            "timezones.tests.NewDatabaseTests.test_cursor_execute_accepts_naive_datetime",
            "timezones.tests.NewDatabaseTests.test_cursor_execute_returns_naive_datetime",
            "timezones.tests.NewDatabaseTests.test_cursor_explicit_time_zone",
            "timezones.tests.NewDatabaseTests.test_raw_sql",
        },
        "Custom functions with SQL don't work on MongoDB.": {
            "annotations.tests.NonAggregateAnnotationTestCase.test_custom_functions",
            "annotations.tests.NonAggregateAnnotationTestCase.test_custom_functions_can_ref_other_functions",
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
            "expressions.tests.FieldTransformTests.test_multiple_transforms_in_values",
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
        "Known issue querying JSONField.": {
            # An ExpressionWrapper annotation with KeyTransform followed by
            # .filter(expr__isnull=False) doesn't use KeyTransformIsNull as it
            # needs to.
            "model_fields.test_jsonfield.TestQuerying.test_expression_wrapper_key_transform",
            # There is no way to distinguish between a JSON "null" (represented
            # by Value(None, JSONField())) and a SQL null (queried using the
            # isnull lookup). Both of these queries return both nulls.
            "model_fields.test_jsonfield.TestSaveLoad.test_json_null_different_from_sql_null",
            # Some queries with Q objects, e.g. Q(value__foo="bar"), don't work
            # properly, particularly with QuerySet.exclude().
            "model_fields.test_jsonfield.TestQuerying.test_lookup_exclude",
            "model_fields.test_jsonfield.TestQuerying.test_lookup_exclude_nonexistent_key",
            # Queries like like QuerySet.filter(value__j=None) incorrectly
            # returns objects where the key doesn't exist.
            "model_fields.test_jsonfield.TestQuerying.test_none_key",
            "model_fields.test_jsonfield.TestQuerying.test_none_key_exclude",
        },
        "Randomized ordering isn't supported by MongoDB.": {
            "ordering.tests.OrderingTests.test_random_ordering",
        },
    }

    @cached_property
    def is_mongodb_6_3(self):
        return self.connection.get_database_version() >= (6, 3)
