"""
Adding support for different setting of actions in ViewSets

ViewSet that gets settings from dictionaries with keys equal action names:
    * Serializers dictionary: `serializer_classes`
    * FilterSet dictionary: `filterset_classes` (when using customized Filter Backend)
    * Ordering fields dictionary: `ordering_fields_set` (when using customized Ordering Filter)
    * Default ordering dictionary: `ordering_set` (when using customized Ordering Filter)

View GenericMultipleSettingsViewSet for detail description.

Based on django-rest-framework implementation of ViewSet and ordering filter
"""

from django.utils import six
from rest_framework import viewsets, mixins
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response


class ViewConfigurationError(Exception):
    pass


class MultipleSettingsOrderingFilter(OrderingFilter):
    """
    Ordering filter supporting different ordering_fields for different actions

    Views, using this backend must declare dictionaries ordering_fields_set and ordering_set with keys equals
    action names instead of ordering_fields and ordering parameter. If this dictionaries is not provided or not
    containing value for current action backends defaults to standard behaviour of OrderingFilter class.
    """

    def get_valid_fields(self, queryset, view, context={}):
        try:
            valid_fields_set = getattr(view, 'ordering_fields_set', self.ordering_fields)
            valid_fields = valid_fields_set[view.action]

            if valid_fields == '__all__':
                # View explicitly allows filtering on any model field
                valid_fields = [
                    (field.name, field.verbose_name) for field in queryset.model._meta.fields
                ]
                valid_fields += [
                    (key, key.title().split('__'))
                    for key in queryset.query.annotations
                ]
            else:
                valid_fields = [
                    (item, item) if isinstance(item, six.string_types) else item
                    for item in valid_fields
                ]

            return valid_fields
        except (AttributeError, KeyError, TypeError):
            return super().get_valid_fields(queryset, view, context)

    def get_default_ordering(self, view):
        try:
            ordering_set = getattr(view, 'ordering_set', None)
            ordering = ordering_set[view.action]
            if isinstance(ordering, six.string_types):
                return tuple(ordering)
            return ordering
        except (AttributeError, KeyError, TypeError):
            return super().get_default_ordering(view)


class GenericMultipleSettingsViewSet(viewsets.GenericViewSet):
    """
    Customized GenericViewSet which uses different settings for different actions.

    Usage:
    This ViewSet does not contain any actions, so before you using it you should inherit this class adding mixins
    with desired actions (e.g. mixins.RetrieveModelMixin, mixins.ListModelMixin to add `retrieve` and `list` actions)

    Instead of parametrize entire viewset with serializer, filterset, ordering_fields and ordering, you should give this
    parameters to each action. To do so, declare next dictionaries with keys equal action names.

    ViewSet settings:
        * Serializers dictionary: `serializer_classes`. If this attribute

    If you wish to use different filtersets for different actions as well (which seems logical), your ViewSet
    should use `drf_multiple_settings.filter_backends.django_filters.FilterBackend` which gives you access to this
    dictionary:
        * FilterSet dictionary: `filterset_classes` (only when using with MultipleSettingsFilterBackend)

    Note, that this Filter Backend just tweaks django_filters.rest_framework.DjangoFilterBackend, which means that you
    should use django-filters and django-filters should be installed in your environment. If you are using other
    filtering backend look at implementation for django-filter it's pretty straightforward. Feel free to contact me at
    github so I can include your implementation of other FilterBackend in package.

    If you wish to use different ordering setting for different actions as well (which also seems logical), your ViewSet
    should use `MultipleSettingsOrderingFilter` which gives you access to this dictionaries:
        * Ordering fields dictionary: `ordering_fields_set`
        * Default ordering dictionary: `ordering_set`

    Each dictionary value should have type of corresponding normal GenericAPIView parameters. See Django REST Framework
    documentation if you unsure what it is.

    Class also provides `get_response` method for rendering response from action using whatever data you wish using
    current action's settings.
    """
    serializer_classes = None
    filterset_classes = None

    def get_serializer_class(self):
        if self.serializer_classes is None:
            raise ViewConfigurationError("'%s' should either include a `serializer_classes` attribute, "
                                         "or override the `get_queryset()` method."
                                         % self.__class__.__name__
                                         )
        try:
            return self.serializer_classes[self.action]
        except AttributeError:
            raise ViewConfigurationError("'%s' should either include a `serializer_classes` attribute, "
                                         "or override the `get_serializer_class()` method."
                                         % self.__class__.__name__)
        except KeyError:
            raise ViewConfigurationError("%s's attribute `serializer_classes` does not contain value for `%s` action"
                                         % (self.__class__.__name__, self.action))

    def get_response(self, data, many):
        """
        Render `data` to response using current action serializer

        This method gets QuerySet, then serialize it using serializer, set to this action.

        Method designed to be used inside an action-decorated methods. Usage outside actions was not tested.

        Example:
          # Return issues of title with specified id
          @action(detail=True, name="Title's Issues")
          def issues(self, request, pk):
              title = get_object_or_404(models.Title, pk=pk)
              titles = title.issues.all()
              titles = self.filter_queryset(titles)
             return self.get_response(titles, True)

        :param data: data, which needs to be returned in response
        :param many: many parameter to be passed in serializer
        :return: Response() object
        """
        page = self.paginate_queryset(data)
        if page is not None:
            serializer = self.get_serializer(page, many=many)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(data, many=many)
        return Response(serializer.data)


class ReadOnlyModelMultipleSettingsViewSet(mixins.RetrieveModelMixin,
                                           mixins.ListModelMixin,
                                           GenericMultipleSettingsViewSet):
    """
    A viewset that provides default `list()` and `retrieve()` actions.
    """
    pass


class ModelMultipleSettingsViewSet(mixins.CreateModelMixin,
                                   mixins.RetrieveModelMixin,
                                   mixins.UpdateModelMixin,
                                   mixins.DestroyModelMixin,
                                   mixins.ListModelMixin,
                                   GenericMultipleSettingsViewSet):
    """
    A viewset that provides default `create()`, `retrieve()`, `update()`,
    `partial_update()`, `destroy()` and `list()` actions.
    """
    pass


