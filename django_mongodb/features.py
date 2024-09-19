from django.db.backends.base.features import BaseDatabaseFeatures
from django.utils.functional import cached_property


class DatabaseFeatures(BaseDatabaseFeatures):
    allow_sliced_subqueries_with_in = False
    allows_multiple_constraints_on_same_fields = False
    can_create_inline_fk = False
    can_introspect_foreign_keys = False
    greatest_least_ignores_nulls = True
    has_json_object_function = False
    has_native_json_field = True
    supports_collation_on_charfield = False
    supports_column_check_constraints = False
    supports_date_lookup_using_string = False
    supports_explaining_query_execution = True
    supports_expression_defaults = False
    supports_expression_indexes = False
    supports_foreign_keys = False
    supports_ignore_conflicts = False
    supports_json_field_contains = False
    # BSON Date type doesn't support microsecond precision.
    supports_microsecond_precision = False
    supports_paramstyle_pyformat = False
    supports_select_difference = False
    supports_select_intersection = False
    supports_sequence_reset = False
    supports_slicing_ordering_in_compound = True
    supports_table_check_constraints = False
    supports_temporal_subtraction = True
    # MongoDB stores datetimes in UTC.
    supports_timezones = False
    # Not implemented: https://github.com/mongodb-labs/django-mongodb/issues/7
    supports_transactions = False
    supports_unspecified_pk = True
    uses_savepoints = False

    _django_test_expected_failures = {
        # 'NulledTransform' object has no attribute 'as_mql'.
        "lookup.tests.LookupTests.test_exact_none_transform",
        # "Save with update_fields did not affect any rows."
        "basic.tests.SelectOnSaveTests.test_select_on_save_lying_update",
        # BaseExpression.convert_value() crashes with Decimal128.
        "aggregation.tests.AggregateTestCase.test_combine_different_types",
        "annotations.tests.NonAggregateAnnotationTestCase.test_combined_f_expression_annotation_with_aggregation",
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
        # range lookup includes incorrect values.
        "expressions.tests.IterableLookupInnerExpressionsTests.test_expressions_in_lookups_join_choice",
        # Unexpected alias_refcount in alias_map.
        "queries.tests.Queries1Tests.test_order_by_tables",
        # The $sum aggregation returns 0 instead of None for null.
        "aggregation.test_filter_argument.FilteredAggregateTests.test_plain_annotate",
        "aggregation.tests.AggregateTestCase.test_aggregation_default_passed_another_aggregate",
        "aggregation.tests.AggregateTestCase.test_annotation_expressions",
        "aggregation.tests.AggregateTestCase.test_reverse_fkey_annotate",
        "aggregation_regress.tests.AggregationTests.test_annotation_disjunction",
        "aggregation_regress.tests.AggregationTests.test_decimal_aggregate_annotation_filter",
        # QuerySet.extra(select=...) should raise NotSupportedError instead of:
        # 'RawSQL' object has no attribute 'as_mql'.
        "aggregation_regress.tests.AggregationTests.test_annotate_with_extra",
        "aggregation_regress.tests.AggregationTests.test_annotation",
        "aggregation_regress.tests.AggregationTests.test_more_more3",
        "aggregation_regress.tests.AggregationTests.test_more_more_more3",
        # QuerySet.extra(where=...) should raise NotSupportedError instead of:
        # 'ExtraWhere' object has no attribute 'as_mql'.
        "many_to_one.tests.ManyToOneTests.test_selects",
        # Incorrect JOIN with GenericRelation gives incorrect results.
        "aggregation_regress.tests.AggregationTests.test_aggregation_with_generic_reverse_relation",
        # subclasses of BaseDatabaseWrapper may require an is_usable() method
        "backends.tests.BackendTestCase.test_is_usable_after_database_disconnects",
        # Connection creation doesn't follow the usual Django API.
        "backends.tests.ThreadTests.test_pass_connection_between_threads",
        "backends.tests.ThreadTests.test_closing_non_shared_connections",
        "backends.tests.ThreadTests.test_default_connection_thread_local",
        # AddField
        "schema.tests.SchemaTests.test_add_indexed_charfield",
        "schema.tests.SchemaTests.test_add_unique_charfield",
        # Add/RemoveIndex
        "migrations.test_operations.OperationTests.test_add_index",
        "migrations.test_operations.OperationTests.test_alter_field_with_index",
        "migrations.test_operations.OperationTests.test_remove_index",
        "migrations.test_operations.OperationTests.test_rename_index",
        "migrations.test_operations.OperationTests.test_rename_index_unknown_unnamed_index",
        "migrations.test_operations.OperationTests.test_rename_index_unnamed_index",
        "schema.tests.SchemaTests.test_add_remove_index",
        "schema.tests.SchemaTests.test_composed_desc_index_with_fk",
        "schema.tests.SchemaTests.test_composed_index_with_fk",
        "schema.tests.SchemaTests.test_create_index_together",
        "schema.tests.SchemaTests.test_order_index",
        "schema.tests.SchemaTests.test_text_field_with_db_index",
        # AlterField
        "schema.tests.SchemaTests.test_alter_field_add_index_to_integerfield",
        "schema.tests.SchemaTests.test_alter_field_default_dropped",
        "schema.tests.SchemaTests.test_alter_field_fk_keeps_index",
        "schema.tests.SchemaTests.test_alter_field_fk_to_o2o",
        "schema.tests.SchemaTests.test_alter_field_o2o_keeps_unique",
        "schema.tests.SchemaTests.test_alter_field_o2o_to_fk",
        "schema.tests.SchemaTests.test_alter_int_pk_to_int_unique",
        "schema.tests.SchemaTests.test_alter_not_unique_field_to_primary_key",
        "schema.tests.SchemaTests.test_alter_null_to_not_null",
        "schema.tests.SchemaTests.test_alter_primary_key_the_same_name",
        # AlterField (db_index)
        "schema.tests.SchemaTests.test_alter_renames_index",
        "schema.tests.SchemaTests.test_indexes",
        "schema.tests.SchemaTests.test_remove_constraints_capital_letters",
        "schema.tests.SchemaTests.test_remove_db_index_doesnt_remove_custom_indexes",
        # AlterField (unique)
        "schema.tests.SchemaTests.test_unique",
        "schema.tests.SchemaTests.test_unique_and_reverse_m2m",
        # alter_index_together
        "migrations.test_operations.OperationTests.test_alter_index_together",
        "schema.tests.SchemaTests.test_index_together",
        # alter_unique_together
        "migrations.test_operations.OperationTests.test_alter_unique_together",
        "schema.tests.SchemaTests.test_unique_together",
        # add/remove_constraint
        "introspection.tests.IntrospectionTests.test_get_constraints",
        "migrations.test_operations.OperationTests.test_add_partial_unique_constraint",
        "migrations.test_operations.OperationTests.test_create_model_with_partial_unique_constraint",
        "migrations.test_operations.OperationTests.test_remove_partial_unique_constraint",
        "schema.tests.SchemaTests.test_composed_constraint_with_fk",
        "schema.tests.SchemaTests.test_remove_ignored_unique_constraint_not_create_fk_index",
        "schema.tests.SchemaTests.test_unique_constraint",
        # subclasses of BaseDatabaseIntrospection may require a get_constraints() method
        "migrations.test_operations.OperationTests.test_add_func_unique_constraint",
        "migrations.test_operations.OperationTests.test_remove_func_unique_constraint",
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
        "Database defaults aren't supported by MongoDB.": {
            # bson.errors.InvalidDocument: cannot encode object:
            # <django.db.models.expressions.DatabaseDefault
            "basic.tests.ModelInstanceCreationTests.test_save_primary_with_db_default",
            "migrations.test_operations.OperationTests.test_add_field_both_defaults",
            "migrations.test_operations.OperationTests.test_add_field_database_default",
            "migrations.test_operations.OperationTests.test_add_field_database_default_special_char_escaping",
            "migrations.test_operations.OperationTests.test_alter_field_add_database_default",
            "migrations.test_operations.OperationTests.test_alter_field_change_blank_nullable_database_default_to_not_null",
            "migrations.test_operations.OperationTests.test_alter_field_change_default_to_database_default",
            "migrations.test_operations.OperationTests.test_alter_field_change_nullable_to_database_default_not_null",
            "migrations.test_operations.OperationTests.test_alter_field_change_nullable_to_decimal_database_default_not_null",
            "schema.tests.SchemaTests.test_db_default_output_field_resolving",
            "schema.tests.SchemaTests.test_rename_keep_db_default",
        },
        "Insert expressions aren't supported.": {
            "bulk_create.tests.BulkCreateTests.test_bulk_insert_now",
            "bulk_create.tests.BulkCreateTests.test_bulk_insert_expressions",
            "expressions.tests.BasicExpressionsTests.test_new_object_create",
            "expressions.tests.BasicExpressionsTests.test_new_object_save",
            "expressions.tests.BasicExpressionsTests.test_object_create_with_aggregate",
            "expressions.tests.BasicExpressionsTests.test_object_create_with_f_expression_in_subquery",
            "expressions.tests.BasicExpressionsTests.test_object_update_unsaved_objects",
            # PI()
            "db_functions.math.test_round.RoundTests.test_decimal_with_precision",
            "db_functions.math.test_round.RoundTests.test_float_with_precision",
        },
        "MongoDB doesn't rename an index when a field is renamed.": {
            "migrations.test_operations.OperationTests.test_rename_field_index_together",
            "migrations.test_operations.OperationTests.test_rename_field_unique_together",
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
        "QuerySet.prefetch_related() is not supported on MongoDB.": {
            "backends.base.test_creation.TestDeserializeDbFromString.test_serialize_db_to_string_base_manager_with_prefetch_related",
            "m2m_through_regress.test_multitable.MultiTableTests.test_m2m_prefetch_proxied",
            "m2m_through_regress.test_multitable.MultiTableTests.test_m2m_prefetch_reverse_proxied",
            "many_to_many.tests.ManyToManyTests.test_add_after_prefetch",
            "many_to_many.tests.ManyToManyTests.test_add_then_remove_after_prefetch",
            "many_to_many.tests.ManyToManyTests.test_clear_after_prefetch",
            "many_to_many.tests.ManyToManyTests.test_create_after_prefetch",
            "many_to_many.tests.ManyToManyTests.test_remove_after_prefetch",
            "many_to_many.tests.ManyToManyTests.test_set_after_prefetch",
            "model_forms.tests.OtherModelFormTests.test_prefetch_related_queryset",
        },
        "AutoField not supported.": {
            "bulk_create.tests.BulkCreateTests.test_bulk_insert_nullable_fields",
            "custom_pk.tests.CustomPKTests.test_auto_field_subclass_create",
            "introspection.tests.IntrospectionTests.test_sequence_list",
            "lookup.tests.LookupTests.test_filter_by_reverse_related_field_transform",
            "lookup.tests.LookupTests.test_in_ignore_none_with_unhashable_items",
            "m2m_through_regress.tests.ThroughLoadDataTestCase.test_sequence_creation",
            "many_to_many.tests.ManyToManyTests.test_add_remove_invalid_type",
            "migrations.test_operations.OperationTests.test_autofield__bigautofield_foreignfield_growth",
            "migrations.test_operations.OperationTests.test_model_with_bigautofield",
            "migrations.test_operations.OperationTests.test_smallfield_autofield_foreignfield_growth",
            "migrations.test_operations.OperationTests.test_smallfield_bigautofield_foreignfield_growth",
            "model_fields.test_autofield.AutoFieldTests",
            "model_fields.test_autofield.BigAutoFieldTests",
            "model_fields.test_autofield.SmallAutoFieldTests",
            "queries.tests.TestInvalidValuesRelation.test_invalid_values",
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
        "MongoDB does not enforce PositiveIntegerField constraint.": {
            "model_fields.test_integerfield.PositiveIntegerFieldTests.test_negative_values",
        },
        "Test assumes integer primary key.": {
            "db_functions.comparison.test_cast.CastTests.test_cast_to_integer_foreign_key",
            "model_fields.test_foreignkey.ForeignKeyTests.test_to_python",
            "queries.test_qs_combinators.QuerySetSetOperationTests.test_order_raises_on_non_selected_column",
        },
        "Exists is not supported on MongoDB.": {
            "aggregation.test_filter_argument.FilteredAggregateTests.test_filtered_aggregate_on_exists",
            "aggregation.test_filter_argument.FilteredAggregateTests.test_filtered_aggregate_ref_multiple_subquery_annotation",
            "aggregation.tests.AggregateTestCase.test_aggregation_exists_multivalued_outeref",
            "aggregation.tests.AggregateTestCase.test_group_by_exists_annotation",
            "aggregation.tests.AggregateTestCase.test_exists_none_with_aggregate",
            "aggregation.tests.AggregateTestCase.test_exists_extra_where_with_aggregate",
            "annotations.tests.NonAggregateAnnotationTestCase.test_annotation_exists_aggregate_values_chaining",
            "annotations.tests.NonAggregateAnnotationTestCase.test_annotation_exists_none_query",
            "aggregation_regress.tests.AggregationTests.test_annotate_and_join",
            "delete_regress.tests.DeleteTests.test_self_reference_with_through_m2m_at_second_level",
            "expressions.tests.BasicExpressionsTests.test_annotation_with_deeply_nested_outerref",
            "expressions.tests.BasicExpressionsTests.test_boolean_expression_combined",
            "expressions.tests.BasicExpressionsTests.test_boolean_expression_combined_with_empty_Q",
            "expressions.tests.BasicExpressionsTests.test_boolean_expression_in_Q",
            "expressions.tests.BasicExpressionsTests.test_case_in_filter_if_boolean_output_field",
            "expressions.tests.BasicExpressionsTests.test_exists_in_filter",
            "expressions.tests.BasicExpressionsTests.test_order_by_exists",
            "expressions.tests.BasicExpressionsTests.test_subquery",
            "expressions.tests.ExistsTests.test_filter_by_empty_exists",
            "expressions.tests.ExistsTests.test_negated_empty_exists",
            "expressions.tests.ExistsTests.test_optimizations",
            "expressions.tests.ExistsTests.test_select_negated_empty_exists",
            "lookup.tests.LookupTests.test_exact_exists",
            "lookup.tests.LookupTests.test_nested_outerref_lhs",
            "lookup.tests.LookupQueryingTests.test_filter_exists_lhs",
            "model_forms.tests.LimitChoicesToTests.test_fields_for_model_applies_limit_choices_to",
            "model_forms.tests.LimitChoicesToTests.test_limit_choices_to_callable_for_fk_rel",
            "model_forms.tests.LimitChoicesToTests.test_limit_choices_to_callable_for_m2m_rel",
            "model_forms.tests.LimitChoicesToTests.test_limit_choices_to_m2m_through",
            "model_forms.tests.LimitChoicesToTests.test_limit_choices_to_no_duplicates",
            "null_queries.tests.NullQueriesTests.test_reverse_relations",
            "queries.test_qs_combinators.QuerySetSetOperationTests.test_union_with_values_list_on_annotated_and_unannotated",
            "queries.tests.ExcludeTest17600.test_exclude_plain",
            "queries.tests.ExcludeTest17600.test_exclude_with_q_is_equal_to_plain_exclude_variation",
            "queries.tests.ExcludeTest17600.test_exclude_with_q_object_no_distinct",
            "queries.tests.ExcludeTests.test_exclude_multivalued_exists",
            "queries.tests.ExcludeTests.test_exclude_reverse_fk_field_ref",
            "queries.tests.ExcludeTests.test_exclude_with_circular_fk_relation",
            "queries.tests.ExcludeTests.test_subquery_exclude_outerref",
            "queries.tests.ExcludeTests.test_to_field",
            "queries.tests.ForeignKeyToBaseExcludeTests.test_ticket_21787",
            "queries.tests.JoinReuseTest.test_inverted_q_across_relations",
            "queries.tests.ManyToManyExcludeTest.test_exclude_many_to_many",
            "queries.tests.ManyToManyExcludeTest.test_ticket_12823",
            "queries.tests.Queries1Tests.test_double_exclude",
            "queries.tests.Queries1Tests.test_exclude",
            "queries.tests.Queries1Tests.test_exclude_in",
            "queries.tests.Queries1Tests.test_excluded_intermediary_m2m_table_joined",
            "queries.tests.Queries1Tests.test_nested_exclude",
            "queries.tests.Queries4Tests.test_join_reuse_order",
            "queries.tests.Queries4Tests.test_ticket24525",
            "queries.tests.Queries6Tests.test_tickets_8921_9188",
            "queries.tests.Queries6Tests.test_xor_subquery",
            "queries.tests.QuerySetBitwiseOperationTests.test_subquery_aliases",
            "queries.tests.TestTicket24605.test_ticket_24605",
            "queries.tests.Ticket20101Tests.test_ticket_20101",
            "queries.tests.Ticket20788Tests.test_ticket_20788",
            "queries.tests.Ticket22429Tests.test_ticket_22429",
        },
        "Subquery is not supported on MongoDB.": {
            "aggregation.test_filter_argument.FilteredAggregateTests.test_filtered_aggregate_ref_subquery_annotation",
            "aggregation.tests.AggregateAnnotationPruningTests.test_referenced_composed_subquery_requires_wrapping",
            "aggregation.tests.AggregateAnnotationPruningTests.test_referenced_subquery_requires_wrapping",
            "aggregation.tests.AggregateTestCase.test_aggregation_nested_subquery_outerref",
            "aggregation.tests.AggregateTestCase.test_aggregation_subquery_annotation",
            "aggregation.tests.AggregateTestCase.test_aggregation_subquery_annotation_multivalued",
            "aggregation.tests.AggregateTestCase.test_aggregation_subquery_annotation_related_field",
            "aggregation.tests.AggregateTestCase.test_aggregation_subquery_annotation_values",
            "aggregation.tests.AggregateTestCase.test_aggregation_subquery_annotation_values_collision",
            "annotations.tests.NonAggregateAnnotationTestCase.test_annotation_filter_with_subquery",
            "annotations.tests.NonAggregateAnnotationTestCase.test_annotation_subquery_and_aggregate_values_chaining",
            "annotations.tests.NonAggregateAnnotationTestCase.test_annotation_subquery_outerref_transform",
            "annotations.tests.NonAggregateAnnotationTestCase.test_empty_queryset_annotation",
            "db_functions.datetime.test_extract_trunc.DateFunctionTests.test_extract_outerref",
            "db_functions.datetime.test_extract_trunc.DateFunctionTests.test_trunc_subquery_with_parameters",
            "expressions.tests.BasicExpressionsTests.test_aggregate_subquery_annotation",
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
            "queries.test_qs_combinators.QuerySetSetOperationTests.test_union_in_subquery",
            "queries.test_qs_combinators.QuerySetSetOperationTests.test_union_in_subquery_related_outerref",
        },
        "Using a QuerySet in annotate() is not supported on MongoDB.": {
            "aggregation.test_filter_argument.FilteredAggregateTests.test_filtered_reused_subquery",
            "aggregation.tests.AggregateTestCase.test_filter_in_subquery_or_aggregation",
            "aggregation.tests.AggregateTestCase.test_group_by_subquery_annotation",
            "aggregation.tests.AggregateTestCase.test_group_by_reference_subquery",
            "annotations.tests.NonAggregateAnnotationTestCase.test_annotation_and_alias_filter_in_subquery",
            "annotations.tests.NonAggregateAnnotationTestCase.test_annotation_and_alias_filter_related_in_subquery",
            "annotations.tests.NonAggregateAnnotationTestCase.test_empty_expression_annotation",
            "aggregation_regress.tests.AggregationTests.test_aggregates_in_where_clause",
            "aggregation_regress.tests.AggregationTests.test_aggregates_in_where_clause_pre_eval",
            "aggregation_regress.tests.AggregationTests.test_f_expression_annotation",
            "aggregation_regress.tests.AggregationTests.test_having_subquery_select",
            "aggregation_regress.tests.AggregationTests.test_more_more4",
            "aggregation_regress.tests.AggregationTests.test_more_more_more5",
            "aggregation_regress.tests.AggregationTests.test_negated_aggregation",
            "db_functions.comparison.test_coalesce.CoalesceTests.test_empty_queryset",
            "expressions.tests.FTimeDeltaTests.test_date_subquery_subtraction",
            "expressions.tests.FTimeDeltaTests.test_datetime_subquery_subtraction",
            "expressions.tests.FTimeDeltaTests.test_time_subquery_subtraction",
            "expressions_case.tests.CaseExpressionTests.test_annotate_with_in_clause",
            "expressions_case.tests.CaseExpressionTests.test_in_subquery",
            "lookup.tests.LookupTests.test_exact_query_rhs_with_selected_columns",
            "lookup.tests.LookupTests.test_exact_sliced_queryset_limit_one",
            "lookup.tests.LookupTests.test_exact_sliced_queryset_limit_one_offset",
            "lookup.tests.LookupTests.test_in_different_database",
            "many_to_many.tests.ManyToManyTests.test_assign",
            "many_to_many.tests.ManyToManyTests.test_assign_ids",
            "many_to_many.tests.ManyToManyTests.test_clear",
            "many_to_many.tests.ManyToManyTests.test_remove",
            "many_to_many.tests.ManyToManyTests.test_reverse_assign_with_queryset",
            "many_to_many.tests.ManyToManyTests.test_set",
            "many_to_many.tests.ManyToManyTests.test_set_existing_different_type",
            "many_to_one.tests.ManyToOneTests.test_get_prefetch_queryset_reverse_warning",
            "model_fields.test_jsonfield.TestQuerying.test_usage_in_subquery",
            "one_to_one.tests.OneToOneTests.test_get_prefetch_queryset_warning",
            "one_to_one.tests.OneToOneTests.test_rel_pk_subquery",
            "queries.test_qs_combinators.QuerySetSetOperationTests.test_union_in_with_ordering",
            "queries.tests.CloneTests.test_evaluated_queryset_as_argument",
            "queries.tests.DoubleInSubqueryTests.test_double_subquery_in",
            "queries.tests.EmptyQuerySetTests.test_values_subquery",
            "queries.tests.ExcludeTests.test_exclude_subquery",
            "queries.tests.NullInExcludeTest.test_null_in_exclude_qs",
            "queries.tests.Queries1Tests.test_ticket9985",
            "queries.tests.Queries1Tests.test_ticket9997",
            "queries.tests.Queries1Tests.test_ticket10742",
            "queries.tests.Queries4Tests.test_ticket10181",
            "queries.tests.Queries5Tests.test_queryset_reuse",
            "queries.tests.QuerySetBitwiseOperationTests.test_conflicting_aliases_during_combine",
            "queries.tests.RelabelCloneTest.test_ticket_19964",
            "queries.tests.RelatedLookupTypeTests.test_correct_lookup",
            "queries.tests.RelatedLookupTypeTests.test_values_queryset_lookup",
            "queries.tests.Ticket23605Tests.test_ticket_23605",
            "queries.tests.ToFieldTests.test_in_subquery",
            "queries.tests.ToFieldTests.test_nested_in_subquery",
            "queries.tests.ValuesSubqueryTests.test_values_in_subquery",
            "queries.tests.WeirdQuerysetSlicingTests.test_empty_sliced_subquery",
            "queries.tests.WeirdQuerysetSlicingTests.test_empty_sliced_subquery_exclude",
        },
        "Cannot use QuerySet.delete() when querying across multiple collections on MongoDB.": {
            "delete.tests.FastDeleteTests.test_fast_delete_aggregation",
            "delete.tests.FastDeleteTests.test_fast_delete_empty_no_update_can_self_select",
            "delete.tests.FastDeleteTests.test_fast_delete_full_match",
            "delete.tests.FastDeleteTests.test_fast_delete_joined_qs",
            "delete_regress.tests.DeleteTests.test_meta_ordered_delete",
            "delete_regress.tests.Ticket19102Tests.test_ticket_19102_annotate",
            "delete_regress.tests.Ticket19102Tests.test_ticket_19102_defer",
            "delete_regress.tests.Ticket19102Tests.test_ticket_19102_select_related",
            "one_to_one.tests.OneToOneTests.test_o2o_primary_key_delete",
        },
        "Cannot use QuerySet.update() when querying across multiple collections on MongoDB.": {
            "expressions.tests.BasicExpressionsTests.test_filter_with_join",
            "queries.tests.Queries4Tests.test_ticket7095",
            "queries.tests.Queries5Tests.test_ticket9848",
            "update.tests.AdvancedTests.test_update_annotated_multi_table_queryset",
            "update.tests.AdvancedTests.test_update_ordered_by_m2m_annotation",
            "update.tests.AdvancedTests.test_update_ordered_by_m2m_annotation_desc",
        },
        "QuerySet.dates() is not supported on MongoDB.": {
            "aggregation.tests.AggregateTestCase.test_dates_with_aggregation",
            "annotations.tests.AliasTests.test_dates_alias",
            "aggregation_regress.tests.AggregationTests.test_more_more_more2",
            "backends.tests.DateQuotingTest.test_django_date_trunc",
            "dates.tests.DatesTests.test_dates_trunc_datetime_fields",
            "dates.tests.DatesTests.test_related_model_traverse",
            "many_to_one.tests.ManyToOneTests.test_select_related",
        },
        "QuerySet.datetimes() is not supported on MongoDB.": {
            "annotations.tests.AliasTests.test_datetimes_alias",
            "datetimes.tests.DateTimesTests.test_21432",
            "datetimes.tests.DateTimesTests.test_datetimes_has_lazy_iterator",
            "datetimes.tests.DateTimesTests.test_datetimes_returns_available_dates_for_given_scope_and_given_field",
            "datetimes.tests.DateTimesTests.test_related_model_traverse",
            "queries.tests.Queries1Tests.test_ticket7155",
            "queries.tests.Queries1Tests.test_tickets_7087_12242",
            "timezones.tests.LegacyDatabaseTests.test_query_datetimes",
            "timezones.tests.NewDatabaseTests.test_query_datetimes",
            "timezones.tests.NewDatabaseTests.test_query_datetimes_in_other_timezone",
        },
        "QuerySet.distinct() is not supported.": {
            "aggregation.tests.AggregateTestCase.test_sum_distinct_aggregate",
            "aggregation_regress.tests.AggregationTests.test_annotate_distinct_aggregate",
            "aggregation_regress.tests.AggregationTests.test_conditional_aggregate_on_complex_condition",
            "aggregation_regress.tests.AggregationTests.test_distinct_conditional_aggregate",
            "lookup.tests.LookupTests.test_lookup_collision_distinct",
            "many_to_many.tests.ManyToManyTests.test_reverse_selects",
            "many_to_many.tests.ManyToManyTests.test_selects",
            "many_to_one.tests.ManyToOneTests.test_reverse_selects",
            "ordering.tests.OrderingTests.test_orders_nulls_first_on_filtered_subquery",
            "queries.tests.ExcludeTest17600.test_exclude_plain_distinct",
            "queries.tests.ExcludeTest17600.test_exclude_with_q_is_equal_to_plain_exclude",
            "queries.tests.ExcludeTest17600.test_exclude_with_q_object_distinct",
            "queries.tests.ExcludeTests.test_exclude_m2m_through",
            "queries.tests.ExistsSql.test_distinct_exists",
            "queries.tests.ExistsSql.test_sliced_distinct_exists",
            "queries.tests.ExistsSql.test_ticket_18414",
            "queries.tests.Queries1Tests.test_ticket4464",
            "queries.tests.Queries1Tests.test_ticket7096",
            "queries.tests.Queries1Tests.test_ticket7791",
            "queries.tests.Queries1Tests.test_tickets_1878_2939",
            "queries.tests.Queries1Tests.test_tickets_5321_7070",
            "queries.tests.Queries1Tests.test_tickets_5324_6704",
            "queries.tests.Queries1Tests.test_tickets_6180_6203",
            "queries.tests.Queries6Tests.test_distinct_ordered_sliced_subquery_aggregation",
            "update.tests.AdvancedTests.test_update_all",
        },
        "QuerySet.extra() is not supported.": {
            "annotations.tests.NonAggregateAnnotationTestCase.test_column_field_ordering",
            "annotations.tests.NonAggregateAnnotationTestCase.test_column_field_ordering_with_deferred",
            "basic.tests.ModelTest.test_extra_method_select_argument_with_dashes",
            "basic.tests.ModelTest.test_extra_method_select_argument_with_dashes_and_values",
            "defer.tests.DeferTests.test_defer_extra",
            "delete_regress.tests.Ticket19102Tests.test_ticket_19102_extra",
            "lookup.tests.LookupTests.test_values",
            "lookup.tests.LookupTests.test_values_list",
            "ordering.tests.OrderingTests.test_extra_ordering",
            "ordering.tests.OrderingTests.test_extra_ordering_quoting",
            "ordering.tests.OrderingTests.test_extra_ordering_with_table_name",
            "queries.test_qs_combinators.QuerySetSetOperationTests.test_union_multiple_models_with_values_list_and_order_by_extra_select",
            "queries.test_qs_combinators.QuerySetSetOperationTests.test_union_with_extra_and_values_list",
            "queries.tests.EscapingTests.test_ticket_7302",
            "queries.tests.Queries5Tests.test_extra_select_literal_percent_s",
            "queries.tests.Queries5Tests.test_ticket7256",
            "queries.tests.ValuesQuerysetTests.test_extra_multiple_select_params_values_order_by",
            "queries.tests.ValuesQuerysetTests.test_extra_select_params_values_order_in_extra",
            "queries.tests.ValuesQuerysetTests.test_extra_values",
            "queries.tests.ValuesQuerysetTests.test_extra_values_list",
            "queries.tests.ValuesQuerysetTests.test_extra_values_order_multiple",
            "queries.tests.ValuesQuerysetTests.test_extra_values_order_twice",
            "queries.tests.ValuesQuerysetTests.test_flat_extra_values_list",
            "queries.tests.ValuesQuerysetTests.test_named_values_list_with_fields",
            "queries.tests.ValuesQuerysetTests.test_named_values_list_without_fields",
            "select_related.tests.SelectRelatedTests.test_select_related_with_extra",
        },
        "Test inspects query for SQL": {
            "aggregation.tests.AggregateAnnotationPruningTests.test_non_aggregate_annotation_pruned",
            "aggregation.tests.AggregateAnnotationPruningTests.test_unreferenced_aggregate_annotation_pruned",
            "aggregation.tests.AggregateAnnotationPruningTests.test_unused_aliased_aggregate_pruned",
            "aggregation.tests.AggregateAnnotationPruningTests.test_referenced_aggregate_annotation_kept",
            "aggregation.tests.AggregateTestCase.test_count_star",
            "delete.tests.DeletionTests.test_only_referenced_fields_selected",
            "lookup.tests.LookupTests.test_in_ignore_none",
            "lookup.tests.LookupTests.test_textfield_exact_null",
            "queries.tests.ExistsSql.test_exists",
            "queries.tests.Queries6Tests.test_col_alias_quoted",
            "schema.tests.SchemaTests.test_rename_column_renames_deferred_sql_references",
            "schema.tests.SchemaTests.test_rename_table_renames_deferred_sql_references",
        },
        "Test executes raw SQL.": {
            "aggregation.tests.AggregateTestCase.test_coalesced_empty_result_set",
            "annotations.tests.NonAggregateAnnotationTestCase.test_raw_sql_with_inherited_field",
            "backends.base.test_base.ExecuteWrapperTests",
            "backends.tests.BackendTestCase.test_cursor_contextmanager",
            "backends.tests.BackendTestCase.test_cursor_executemany",
            "backends.tests.BackendTestCase.test_cursor_executemany_with_empty_params_list",
            "backends.tests.BackendTestCase.test_cursor_executemany_with_iterator",
            "backends.tests.BackendTestCase.test_duplicate_table_error",
            "backends.tests.BackendTestCase.test_queries",
            "backends.tests.BackendTestCase.test_queries_bare_where",
            "backends.tests.BackendTestCase.test_queries_limit",
            "backends.tests.BackendTestCase.test_queries_logger",
            "backends.tests.BackendTestCase.test_unicode_fetches",
            "backends.tests.EscapingChecks",
            "backends.test_utils.CursorWrapperTests",
            "delete_regress.tests.DeleteLockingTest.test_concurrent_delete",
            "expressions.tests.BasicExpressionsTests.test_annotate_values_filter",
            "expressions.tests.BasicExpressionsTests.test_filtering_on_rawsql_that_is_boolean",
            "expressions.tests.BasicExpressionsTests.test_order_by_multiline_sql",
            "migrations.test_operations.OperationTests.test_run_sql",
            "migrations.test_operations.OperationTests.test_run_sql_params",
            "migrations.test_operations.OperationTests.test_separate_database_and_state",
            "model_fields.test_jsonfield.TestQuerying.test_key_sql_injection_escape",
            "model_fields.test_jsonfield.TestQuerying.test_key_transform_raw_expression",
            "model_fields.test_jsonfield.TestQuerying.test_nested_key_transform_raw_expression",
            "queries.tests.Queries1Tests.test_order_by_rawsql",
            "schema.test_logging.SchemaLoggerTests.test_extra_args",
            "timezones.tests.LegacyDatabaseTests.test_cursor_execute_accepts_naive_datetime",
            "timezones.tests.LegacyDatabaseTests.test_cursor_execute_returns_naive_datetime",
            "timezones.tests.LegacyDatabaseTests.test_raw_sql",
            "timezones.tests.NewDatabaseTests.test_cursor_execute_accepts_naive_datetime",
            "timezones.tests.NewDatabaseTests.test_cursor_execute_returns_naive_datetime",
            "timezones.tests.NewDatabaseTests.test_cursor_explicit_time_zone",
            "timezones.tests.NewDatabaseTests.test_raw_sql",
        },
        "Custom aggregations/functions with SQL don't work on MongoDB.": {
            "aggregation.tests.AggregateTestCase.test_add_implementation",
            "aggregation.tests.AggregateTestCase.test_multi_arg_aggregate",
            "aggregation.tests.AggregateTestCase.test_empty_result_optimization",
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
            "aggregation.tests.AggregateTestCase.test_aggregation_default_using_date_from_database",
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
            "aggregation.tests.AggregateTestCase.test_aggregation_default_using_decimal_from_database",
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
        "DatabaseIntrospection.get_table_description() not supported.": {
            "introspection.tests.IntrospectionTests.test_bigautofield",
            "introspection.tests.IntrospectionTests.test_get_table_description_col_lengths",
            "introspection.tests.IntrospectionTests.test_get_table_description_names",
            "introspection.tests.IntrospectionTests.test_get_table_description_nullable",
            "introspection.tests.IntrospectionTests.test_get_table_description_types",
            "introspection.tests.IntrospectionTests.test_smallautofield",
        },
        "DatabaseIntrospection.get_constraints() not implemented.": {
            "introspection.tests.IntrospectionTests.test_get_constraints",
            "introspection.tests.IntrospectionTests.test_get_constraints_index_types",
            "introspection.tests.IntrospectionTests.test_get_constraints_indexes_orders",
            "introspection.tests.IntrospectionTests.test_get_constraints_unique_indexes_orders",
            "introspection.tests.IntrospectionTests.test_get_primary_key_column",
        },
        "MongoDB can't introspect primary key.": {
            "schema.tests.SchemaTests.test_primary_key",
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
        "Queries without a collection aren't supported on MongoDB.": {
            "queries.test_q.QCheckTests",
            "queries.test_query.TestQueryNoModel",
        },
        "MongoDB doesn't use CursorDebugWrapper.": {
            "backends.tests.LastExecutedQueryTest.test_last_executed_query",
            "backends.tests.LastExecutedQueryTest.test_last_executed_query_with_duplicate_params",
            "backends.tests.LastExecutedQueryTest.test_query_encoding",
        },
        "Test not applicable for MongoDB's SQLCompiler.": {
            "queries.test_iterator.QuerySetIteratorTests",
        },
        "Support for views not implemented.": {
            "introspection.tests.IntrospectionTests.test_table_names_with_views",
        },
        "Connection health checks not implemented.": {
            "backends.base.test_base.ConnectionHealthChecksTests",
        },
        "transaction.atomic() is not supported.": {
            "backends.base.test_base.DatabaseWrapperLoggingTests",
            "migrations.test_operations.OperationTests.test_run_python_atomic",
        },
    }

    @cached_property
    def is_mongodb_6_3(self):
        return self.connection.get_database_version() >= (6, 3)
