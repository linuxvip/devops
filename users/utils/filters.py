# -*- coding: utf-8 -*-

"""
@Remark: 自定义过滤器
"""
import operator
from collections import OrderedDict
from functools import reduce

from django import forms
from django.db import models
from django.db.models import Q, F
from django.db.models.constants import LOOKUP_SEP
from django_filters import utils
from django_filters.conf import settings
from django_filters.constants import ALL_FIELDS
from django_filters.filters import CharFilter, BooleanFilter
from django_filters.filterset import FilterSet, FilterSetMetaclass
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.utils import get_model_field
from rest_framework.filters import BaseFilterBackend


class CustomDjangoFilterBackend(DjangoFilterBackend):
    lookup_prefixes = {
        "^": "istartswith",
        "=": "iexact",
        "@": "search",
        "$": "iregex",
        "~": "icontains",
    }
    filter_fields = "__all__"

    def construct_search(self, field_name, lookup_expr=None):
        lookup = self.lookup_prefixes.get(field_name[0])
        if lookup:
            field_name = field_name[1:]
        else:
            lookup = lookup_expr
        if lookup:
            if field_name.endswith(lookup):
                return field_name
            return LOOKUP_SEP.join([field_name, lookup])
        return field_name

    def find_filter_lookups(self, orm_lookups, search_term_key):
        for lookup in orm_lookups:
            # if lookup.find(search_term_key) >= 0:
            new_lookup = LOOKUP_SEP.join(lookup.split(LOOKUP_SEP)[:-1]) if len(lookup.split(LOOKUP_SEP)) > 1 else lookup
            # 修复条件搜索错误 bug
            if new_lookup == search_term_key:
                return lookup
        return None

    def get_filterset_class(self, view, queryset=None):
        """
        Return the `FilterSet` class used to filter the queryset.
        """
        filterset_class = getattr(view, "filterset_class", None)
        filterset_fields = getattr(view, "filterset_fields", None)

        # TODO: remove assertion in 2.1
        if filterset_class is None and hasattr(view, "filter_class"):
            utils.deprecate(
                "`%s.filter_class` attribute should be renamed `filterset_class`." % view.__class__.__name__
            )
            filterset_class = getattr(view, "filter_class", None)

        # TODO: remove assertion in 2.1
        if filterset_fields is None and hasattr(view, "filter_fields"):
            utils.deprecate(
                "`%s.filter_fields` attribute should be renamed `filterset_fields`." % view.__class__.__name__
            )
            self.filter_fields = getattr(view, "filter_fields", None)
            if isinstance(self.filter_fields, (list, tuple)):
                filterset_fields = [
                    field[1:] if field[0] in self.lookup_prefixes.keys() else field for field in self.filter_fields
                ]
            else:
                filterset_fields = self.filter_fields

        if filterset_class:
            filterset_model = filterset_class._meta.model

            # FilterSets do not need to specify a Meta class
            if filterset_model and queryset is not None:
                assert issubclass(
                    queryset.model, filterset_model
                ), "FilterSet model %s does not match queryset model %s" % (
                    filterset_model,
                    queryset.model,
                )

            return filterset_class

        if filterset_fields and queryset is not None:
            MetaBase = getattr(self.filterset_base, "Meta", object)

            class AutoFilterSet(self.filterset_base):
                @classmethod
                def get_all_model_fields(cls, model):
                    opts = model._meta

                    return [
                        f.name
                        for f in sorted(opts.fields + opts.many_to_many)
                        if (f.name == "id")
                        or not isinstance(f, models.AutoField)
                        and not (getattr(f.remote_field, "parent_link", False))
                    ]

                @classmethod
                def get_fields(cls):
                    """
                    Resolve the 'fields' argument that should be used for generating filters on the
                    filterset. This is 'Meta.fields' sans the fields in 'Meta.exclude'.
                    """
                    model = cls._meta.model
                    fields = cls._meta.fields
                    exclude = cls._meta.exclude

                    assert not (fields is None and exclude is None), (
                        "Setting 'Meta.model' without either 'Meta.fields' or 'Meta.exclude' "
                        "has been deprecated since 0.15.0 and is now disallowed. Add an explicit "
                        "'Meta.fields' or 'Meta.exclude' to the %s class." % cls.__name__
                    )

                    # Setting exclude with no fields implies all other fields.
                    if exclude is not None and fields is None:
                        fields = ALL_FIELDS

                    # Resolve ALL_FIELDS into all fields for the filterset's model.
                    if fields == ALL_FIELDS:
                        fields = cls.get_all_model_fields(model)

                    # Remove excluded fields
                    exclude = exclude or []
                    if not isinstance(fields, dict):
                        fields = [(f, [settings.DEFAULT_LOOKUP_EXPR]) for f in fields if f not in exclude]
                    else:
                        fields = [(f, lookups) for f, lookups in fields.items() if f not in exclude]

                    return OrderedDict(fields)

                @classmethod
                def get_filters(cls):
                    """
                    Get all filters for the filterset. This is the combination of declared and
                    generated filters.
                    """

                    # No model specified - skip filter generation
                    if not cls._meta.model:
                        return cls.declared_filters.copy()

                    # Determine the filters that should be included on the filterset.
                    filters = OrderedDict()
                    fields = cls.get_fields()
                    undefined = []

                    for field_name, lookups in fields.items():
                        field = get_model_field(cls._meta.model, field_name)
                        from django.db import models
                        from timezone_field import TimeZoneField

                        # 不进行 过滤的model 类
                        if isinstance(field, (models.JSONField, TimeZoneField)):
                            continue
                        # warn if the field doesn't exist.
                        if field is None:
                            undefined.append(field_name)
                        # 更新默认字符串搜索为模糊搜索
                        if (
                            isinstance(field, (models.CharField))
                            and filterset_fields == "__all__"
                            and lookups == ["exact"]
                        ):
                            lookups = ["icontains"]
                        for lookup_expr in lookups:
                            filter_name = cls.get_filter_name(field_name, lookup_expr)

                            # If the filter is explicitly declared on the class, skip generation
                            if filter_name in cls.declared_filters:
                                filters[filter_name] = cls.declared_filters[filter_name]
                                continue

                            if field is not None:
                                filters[filter_name] = cls.filter_for_field(field, field_name, lookup_expr)

                    # Allow Meta.fields to contain declared filters *only* when a list/tuple
                    if isinstance(cls._meta.fields, (list, tuple)):
                        undefined = [f for f in undefined if f not in cls.declared_filters]

                    if undefined:
                        raise TypeError(
                            "'Meta.fields' must not contain non-model field names: %s" % ", ".join(undefined)
                        )

                    # Add in declared filters. This is necessary since we don't enforce adding
                    # declared filters to the 'Meta.fields' option
                    filters.update(cls.declared_filters)
                    return filters

                class Meta(MetaBase):
                    model = queryset.model
                    fields = filterset_fields

            return AutoFilterSet

        return None

    def filter_queryset(self, request, queryset, view):
        filterset = self.get_filterset(request, queryset, view)
        if filterset is None:
            return queryset
        if filterset.__class__.__name__ == "AutoFilterSet":
            queryset = filterset.queryset
            filter_fields = filterset.filters if self.filter_fields == "__all__" else self.filter_fields
            orm_lookup_dict = dict(
                zip(
                    [field for field in filter_fields],
                    [filterset.filters[lookup].lookup_expr for lookup in filterset.filters.keys()],
                )
            )
            orm_lookups = [
                self.construct_search(lookup, lookup_expr) for lookup, lookup_expr in orm_lookup_dict.items()
            ]
            # print(orm_lookups)
            conditions = []
            queries = []
            for search_term_key in filterset.data.keys():
                orm_lookup = self.find_filter_lookups(orm_lookups, search_term_key)
                if not orm_lookup or filterset.data.get(search_term_key) == '':
                    continue
                filterset_data_len = len(filterset.data.getlist(search_term_key))
                if filterset_data_len == 1:
                    query = Q(**{orm_lookup: filterset.data[search_term_key]})
                    queries.append(query)
                elif filterset_data_len == 2:
                    orm_lookup += '__range'
                    query = Q(**{orm_lookup: filterset.data.getlist(search_term_key)})
                    queries.append(query)
            if len(queries) > 0:
                conditions.append(reduce(operator.and_, queries))
                queryset = queryset.filter(reduce(operator.and_, conditions))
                return queryset
            else:
                return queryset

        if not filterset.is_valid() and self.raise_exception:
            raise utils.translate_validation(filterset.errors)
        return filterset.qs


# ####################### 懒加载FilterSet ####################### #

import time


def calculate_execution_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Function {func.__name__} took {execution_time:.6f} seconds to execute.", flush=True)
        return result

    return wrapper



def next_layer_data(qs_filter, qs_node):
    parent_nodes = set(qs_node.values_list("id", flat=True))
    if set(qs_filter) == set(qs_node):
        return parent_nodes
    # qs_filter内所有父级id     去重
    parent_ids = set()
    for node in qs_filter:
        while node.parent:
            if node.id in parent_nodes:
                parent_ids.add(node.id)
                break
            if node.parent.id in parent_nodes:
                parent_ids.add(node.parent.id)
                break
            node = node.parent
    # print(f"过滤查询集           ==>         {qs_filter}", flush=True)
    # print(f"待渲染节点的id        ==>         {parent_nodes=}", flush=True)
    # print(f"过滤查询集的父节点id   ==>         {parent_ids=}", flush=True)
    return parent_ids


def construct_data(qs_filter, qs_node, is_parent):
    filter_node_ids = set(qs_filter.values_list("id", flat=True))
    render_node_ids = set(qs_node.values_list("id", flat=True))

    hidden_node_ids = set()
    for node in qs_filter:
        while node.parent:
            if node.parent in qs_filter:
                hidden_node_ids.add(node.id)
            node = node.parent
    on_show = filter_node_ids.difference(hidden_node_ids)
    on_expand = hidden_node_ids & render_node_ids
    # print(f"完整查询结果 {filter_node_ids}")
    # print(f"待展示的节点(未过滤) {render_node_ids}")
    # print(f"查询结果中的子节点 {hidden_node_ids}")
    # print(f"查询后首先渲染的父节点 {on_show}")
    # print(f"展开父节点时要渲染的节点 {on_expand}")
    return on_expand if is_parent else on_show


class FilterSetOptions:
    def __init__(self, options=None):
        self.model = getattr(options, "model", None)
        self.fields = getattr(options, "fields", None)
        self.exclude = getattr(options, "exclude", None)

        # CharField默认模糊查询
        self.filter_overrides = getattr(
            options,
            "filter_overrides",
            {
                models.CharField: {
                    "filter_class": CharFilter,
                    "extra": lambda f: {
                        "lookup_expr": "icontains",
                    },
                },
                models.BooleanField: {
                    "filter_class": BooleanFilter,
                    "extra": lambda f: {
                        "widget": forms.RadioSelect,
                    },
                },
            },
        )

        self.form = getattr(options, "form", forms.Form)


class LazyLoadFilterSetMetaclass(FilterSetMetaclass):
    def __new__(cls, name, bases, attrs):
        attrs["declared_filters"] = cls.get_declared_filters(bases, attrs)

        new_class = super().__new__(cls, name, bases, attrs)
        new_class._meta = FilterSetOptions(getattr(new_class, "Meta", None))
        new_class.base_filters = new_class.get_filters()

        return new_class


class LazyLoadFilter(FilterSet, metaclass=LazyLoadFilterSetMetaclass):
    @property
    # @calculate_execution_time
    def qs(self):
        queryset = self.queryset
        # print(self.form.cleaned_data, flush=True)
        filter_params = [k for k, v in self.form.cleaned_data.items() if v in [None, ""]]
        for field in filter_params:
            self.form.cleaned_data.pop(field)
        is_parent = self.form.cleaned_data.pop("parent", None) is not None
        # print(queryset, flush=True)
        if self.form.cleaned_data:
            self.queryset = queryset.model.objects.all()

            # 从根节点开始
            # node_ids = next_layer_data(super().qs, queryset)

            # 按匹配结果显示
            node_ids = construct_data(super().qs, queryset, is_parent)

            return queryset.model.objects.filter(id__in=node_ids)
        return super().qs
