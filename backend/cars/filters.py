from django_filters import rest_framework as filters

from cars.models import Order


class OlderFilterSet(filters.FilterSet):
    name = filters.CharFilter(method='filter_brand')

    class Meta:
        model = Order
        fields = ('name',)

    def filter_brand(self, queryset, name, value):
        lookup = '__'.join(['order_lines__model__brand', name])
        return queryset.filter(**{lookup: value})
