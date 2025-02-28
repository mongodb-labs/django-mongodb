# Based on https://github.com/encode/django-rest-framework/blob/0e1c7d3613905a8f9db69abb82f883e22e967119/tests/test_filters.py

from collections import OrderedDict
from importlib import reload as reload_module


from django.db import models
from django.db.models import CharField, Transform
from django.test import TestCase
from django.test.utils import override_settings

from rest_framework.exceptions import ValidationError
from rest_framework import filters, generics, serializers
from rest_framework.test import APIRequestFactory

factory = APIRequestFactory()


class SearchFilterModel(models.Model):
    title = models.CharField(max_length=20)
    text = models.CharField(max_length=100)


class SearchFilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchFilterModel
        fields = '__all__'


class SearchFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Sequence of title/text is:
        #
        # z   abc
        # zz  bcd
        # zzz cde
        # ...
        searchfilters = OrderedDict()
        for idx in range(10):
            title = 'z' * (idx + 1)
            text = (
                chr(idx + ord('a')) +
                chr(idx + ord('b')) +
                chr(idx + ord('c'))
            )
            searchfilter = SearchFilterModel(title=title, text=text)
            searchfilter.save()
            searchfilters[idx] = searchfilter


        idx += 1
        searchfilter = SearchFilterModel(title='A title', text='The long text')
        searchfilter.save()
        searchfilters[idx] = searchfilter

        idx += 1
        searchfilter = SearchFilterModel(title='The title', text='The "text')
        searchfilter.save()
        searchfilters[idx] = searchfilter

        cls.searchfilters = searchfilters

    def test_search(self):
        class SearchListView(generics.ListAPIView):
            queryset = SearchFilterModel.objects.all()
            serializer_class = SearchFilterSerializer
            filter_backends = (filters.SearchFilter,)
            search_fields = ('title', 'text')

        view = SearchListView.as_view()
        request = factory.get('/', {'search': 'b'})
        response = view(request)
        assert response.data == [
            {'id': self.searchfilters.get(0).id, 'title': 'z', 'text': 'abc'},
            {'id': self.searchfilters.get(1).id, 'title': 'zz', 'text': 'bcd'}
        ]

    def test_search_returns_same_queryset_if_no_search_fields_or_terms_provided(self):
        class SearchListView(generics.ListAPIView):
            queryset = SearchFilterModel.objects.all()
            serializer_class = SearchFilterSerializer
            filter_backends = (filters.SearchFilter,)

        view = SearchListView.as_view()
        request = factory.get('/')
        response = view(request)
        expected = SearchFilterSerializer(SearchFilterModel.objects.all(),
                                          many=True).data
        assert response.data == expected

    def test_exact_search(self):
        class SearchListView(generics.ListAPIView):
            queryset = SearchFilterModel.objects.all()
            serializer_class = SearchFilterSerializer
            filter_backends = (filters.SearchFilter,)
            search_fields = ('=title', 'text')

        view = SearchListView.as_view()
        request = factory.get('/', {'search': 'zzz'})
        response = view(request)
        assert response.data == [
            {'id': self.searchfilters.get(2).id, 'title': 'zzz', 'text': 'cde'}
        ]

    def test_startswith_search(self):
        class SearchListView(generics.ListAPIView):
            queryset = SearchFilterModel.objects.all()
            serializer_class = SearchFilterSerializer
            filter_backends = (filters.SearchFilter,)
            search_fields = ('title', '^text')

        view = SearchListView.as_view()
        request = factory.get('/', {'search': 'b'})
        response = view(request)
        assert response.data == [
            {'id': self.searchfilters.get(1).id, 'title': 'zz', 'text': 'bcd'}
        ]

    def test_regexp_search(self):
        class SearchListView(generics.ListAPIView):
            queryset = SearchFilterModel.objects.all()
            serializer_class = SearchFilterSerializer
            filter_backends = (filters.SearchFilter,)
            search_fields = ('$title', '$text')

        view = SearchListView.as_view()
        request = factory.get('/', {'search': 'z{2} ^b'})
        response = view(request)
        assert response.data == [
            {'id': self.searchfilters.get(1).id, 'title': 'zz', 'text': 'bcd'}
        ]

    def test_search_with_nonstandard_search_param(self):
        with override_settings(REST_FRAMEWORK={'SEARCH_PARAM': 'query'}):
            reload_module(filters)

            class SearchListView(generics.ListAPIView):
                queryset = SearchFilterModel.objects.all()
                serializer_class = SearchFilterSerializer
                filter_backends = (filters.SearchFilter,)
                search_fields = ('title', 'text')

            view = SearchListView.as_view()
            request = factory.get('/', {'query': 'b'})
            response = view(request)
            assert response.data == [
                {'id': self.searchfilters.get(0).id, 'title': 'z', 'text': 'abc'},
                {'id': self.searchfilters.get(1).id, 'title': 'zz', 'text': 'bcd'}
            ]

        reload_module(filters)

    def test_search_with_filter_subclass(self):
        class CustomSearchFilter(filters.SearchFilter):
            # Filter that dynamically changes search fields
            def get_search_fields(self, view, request):
                if request.query_params.get('title_only'):
                    return ('$title',)
                return super().get_search_fields(view, request)

        class SearchListView(generics.ListAPIView):
            queryset = SearchFilterModel.objects.all()
            serializer_class = SearchFilterSerializer
            filter_backends = (CustomSearchFilter,)
            search_fields = ('$title', '$text')

        view = SearchListView.as_view()
        request = factory.get('/', {'search': r'^\w{3}$'})
        response = view(request)
        assert len(response.data) == 10

        request = factory.get('/', {'search': r'^\w{3}$', 'title_only': 'true'})
        response = view(request)
        assert response.data == [
            {'id': self.searchfilters.get(2).id, 'title': 'zzz', 'text': 'cde'}
        ]

    def test_search_field_with_null_characters(self):
        view = generics.GenericAPIView()
        request = factory.get('/?search=\0as%00d\x00f')
        request = view.initialize_request(request)

        with self.assertRaises(ValidationError):
            filters.SearchFilter().get_search_terms(request)

    def test_search_field_with_custom_lookup(self):
        class SearchListView(generics.ListAPIView):
            queryset = SearchFilterModel.objects.all()
            serializer_class = SearchFilterSerializer
            filter_backends = (filters.SearchFilter,)
            search_fields = ('text__iendswith',)
        view = SearchListView.as_view()
        request = factory.get('/', {'search': 'c'})
        response = view(request)
        assert response.data == [
            {'id': self.searchfilters.get(0).id, 'title': 'z', 'text': 'abc'},
        ]

    def test_search_field_with_additional_transforms(self):
        from django.test.utils import register_lookup

        class SearchListView(generics.ListAPIView):
            queryset = SearchFilterModel.objects.all()
            serializer_class = SearchFilterSerializer
            filter_backends = (filters.SearchFilter,)
            search_fields = ('text__trim', )

        view = SearchListView.as_view()

        # an example custom transform, that trims `a` from the string.
        class TrimA(Transform):
            function = 'TRIM'
            lookup_name = 'trim'

            def as_sql(self, compiler, connection):
                sql, params = compiler.compile(self.lhs)
                return "trim(%s, 'a')" % sql, params

        with register_lookup(CharField, TrimA):
            # Search including `a`
            request = factory.get('/', {'search': 'abc'})

            response = view(request)
            assert response.data == []

            # Search excluding `a`
            request = factory.get('/', {'search': 'bc'})
            response = view(request)
            assert response.data == [
                {'id': 1, 'title': 'z', 'text': 'abc'},
                {'id': 2, 'title': 'zz', 'text': 'bcd'},
            ]

    def test_search_field_with_multiple_words(self):
        class SearchListView(generics.ListAPIView):
            queryset = SearchFilterModel.objects.all()
            serializer_class = SearchFilterSerializer
            filter_backends = (filters.SearchFilter,)
            search_fields = ('title', 'text')

        search_query = 'foo bar,baz'
        view = SearchListView()
        request = factory.get('/', {'search': search_query})
        request = view.initialize_request(request)

        rendered_search_field = filters.SearchFilter().to_html(
            request=request, queryset=view.queryset, view=view
        )
        assert search_query in rendered_search_field

    def test_search_field_with_escapes(self):
        class SearchListView(generics.ListAPIView):
            queryset = SearchFilterModel.objects.all()
            serializer_class = SearchFilterSerializer
            filter_backends = (filters.SearchFilter,)
            search_fields = ('title', 'text',)
        view = SearchListView.as_view()
        request = factory.get('/', {'search': '"\\\"text"'})
        response = view(request)
        assert response.data == [
            {'id': self.searchfilters.get(11).id, 'title': 'The title', 'text': 'The "text'},
        ]

    def test_search_field_with_quotes(self):
        class SearchListView(generics.ListAPIView):
            queryset = SearchFilterModel.objects.all()
            serializer_class = SearchFilterSerializer
            filter_backends = (filters.SearchFilter,)
            search_fields = ('title', 'text',)
        view = SearchListView.as_view()
        request = factory.get('/', {'search': '"long text"'})
        response = view(request)
        assert response.data == [
            {'id': self.searchfilters.get(10).id, 'title': 'A title', 'text': 'The long text'},
        ]
