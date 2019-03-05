"""
Customized filter backends which uses different filterset_classes for different actions

Views, using this backend must declare dictionary `filterset_classes` with keys equals action names instead of
filterset_class parameter. If this dictionary is not provided or not containing value for current action, backends
defaults to standard behaviour of OrderingFilter class.
"""


from django_filters.rest_framework import DjangoFilterBackend


class FilterBackend(DjangoFilterBackend):

    def get_filterset_class(self, view, queryset=None):
        try:
            filterset_classes = getattr(view, 'filterset_classes', None)
            filterset_class = filterset_classes[view.action]
        except (AttributeError, KeyError, TypeError) as err:
            filterset_class = super().get_filterset_class(view, queryset)
        return filterset_class
