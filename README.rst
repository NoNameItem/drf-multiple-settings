DRF Multiple Settings
=======================
DRF ViewSets supporting different settings for actions

.. contents::
    **Table of Contents**
    :local:
    :depth: 2
    :backlinks: none

Requirements
------------
**Django REST Framework** 3.0+

Installation
------------

Install using pip:

.. code-block:: sh

    pip install drf-multiple-settings
    
Usage
-----

**drf-multiple-settings** provides you with class ``GenericMultipleSettingsViewSet`` which is a subclass of DRF's ``GenericViewSet`` with added support of different settings for actions.

This ViewSet does not contain any actions, so before you using it you should inherit this class adding mixins with desired actions (e.g. ``mixins.RetrieveModelMixin``, ``mixins.ListModelMixin`` to add ``retrieve`` and ``list`` actions)

Instead of parametrize entire viewset with ``serializer_class``, ``filterset_class``, ``ordering_fields`` and ``ordering``, you should give this parameters to each action. To do so, declare next dictionaries with keys equal action names.

Serializer settings
~~~~~~~~~~~~~~~~~~~

You must provide ``serializer_classes`` dictionary to configure serializers in views, using ``GenericMultipleSettingsViewSet``. This dictionary is equivalent of GenericAPIView ``serializer_class`` field and it's value should contain values of same type.
 
If ``serializer_classes`` is not provided or does not contain value for processed action ``ViewConfigurationError`` exception will be raised

Filters settings
~~~~~~~~~~~~~~~~

If you wish to use different filtersets for different actions as well (which seems logical), your ViewSet should use filter backend from  ``drf_multiple_settings.filter_backends`` package. As of now it contains only ``FilterBackend`` which overrides ``django_filters.rest_framework.DjangoFilterBackend`` and gives you access to ``filterset_classes`` dictionary. This dictionary is equivalent ``filterset_class`` field and it's value should contain values of same type. For more information on ``filterset_class`` and ``django-filter`` visit `django-filter documentation`_.

.. _`django-filter documentation`: https://django-filter.readthedocs.io/en/master/


If you are using filtering backend which does not have implementation in ``drf_multiple_settings.filter_backends`` look at implementation for django-filter and write your own it's pretty straightforward. Feel free to contact me at github so I can include your implementation of other FilterBackend in package.

Ordering settings
~~~~~~~~~~~~~~~~~

If you wish to use different ordering setting for different actions as well (which also seems logical), your ViewSet
should use ``MultipleSettingsOrderingFilter`` which gives you access to this dictionaries:

* Ordering fields dictionary: ``ordering_fields_set``
* Default ordering dictionary: ``ordering_set``

Each dictionary value should have type of corresponding normal GenericAPIView parameters. See Django REST Framework
documentation if you unsure what it is.

``get_response`` method
-----------------------
``GenericMultipleSettingsViewSet`` also provides `get_response` method for rendering response from action using whatever data you wish using current action's settings.

.. code-block:: python

    def get_response(self, data, many):

This method gets QuerySet from ``data`` parameter paginate it if needed, then serialize it using serializer, set to this action and return serialized data as ``Response``. Parameter ``many`` tells serializer if it should serialize more then one element. Example of using this method can be found in Example section.

Method designed to be used inside an action-decorated methods. Usage outside actions was not tested.

``ModelViewSet`` and ``ReadonlyModelViewSet``
---------------------------------------------

**DRF** provides two default ViewSets:

* ``ModelViewSet`` for CRUD operations with model
* ``ReadOnlyModelViewSet`` for read operations with model (``list`` and ``retrieve`` actions)

To ease it's usage **drf-multiple-settings** provides ``GenericMultipleSettingsViewSet`` subclasses with same functionality:

* ``ModelMultipleSettingsViewSet``
* ``ReadOnlyModelMultipleSettingsViewSet``

Example
-------

For this example we assume that we have following:

* Two models `Title` and `Issue`
* Three serializers

  * ``TitleListSerializer`` - serializer with main info about title
  * ``TitleDetailDerializer`` - serializer with detail info about title
  * ``IssueListSerializer``

* Two FilterSet classes

  * ``TitleFilter`` - title filters
  * ``IssueFilter`` - issue filters

And we wish create readonly API with following url structure

* ``/title/`` - list of all titles
* ``/title/{id}`` - detail info of title with id={id}
* ``/title/{id}/issues`` - list of all issues of title with id={id}

Additionally we want to allow sorting titles by `name` and issues by `name`, `number` and `publish_date` with default ordering on ``name`` ascending and ``publish_date`` descending accordingly and allow user to filter results using corresponding FilterSet classes.

We can use **drf-multiple-settings** to implement this API as follows (views.py):

.. code-block:: python

    from django.shortcuts import get_object_or_404
    from drf_multiple_settings.filter_backends.django_filters import FilterBackend
    from drf_multiple_settings.viewsets import ReadOnlyModelMultipleSettingsViewSet, MultipleSettingsOrderingFilter
    from rest_framework.decorators import action

    # ... Models and serializers imports...

    class TitleViewSet(ComicsDBBaseViewSet):
        queryset = models.Title.objects.all()
        filter_backends = (MultipleSettingsOrderingFilter, FilterBackend,)

        # Serializers
        serializer_classes = {
            'list': TitleListSerializer,
            'retrieve': TitleDetailSerializer,
            'issues': IssueListSerializer
        }

        # FilterSets
        filterset_classes = {
            'list': TitleFilter,
            'issues': IssueFilter
        }

        # Ordering Parameters
        ordering_fields_set = {
            'list': ("name",),
            'issues': ("name", "number", "publish_date")
        }
        ordering_set = {
            'list': ("name", ),
            'issues': ("-publish_date", ),
        }

        @action(detail=True) # detail = True needed so DRF router include {id} in url
        def issues(self, request, pk):
            title = get_object_or_404(models.Title, pk=pk)
            titles = title.issues.all()
            titles = self.filter_queryset(titles)
            return self.get_response(titles, True)