from django.db.models import Count
from django_filters import rest_framework as filters
from rest_framework.mixins import ListModelMixin
from rest_framework.pagination import CursorPagination
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from cars.filters import OlderFilterSet
from cars.models import Brand, Color, Order
from cars.serializers import BrandSerializer, ColorSerializer, OrderSerializer


class OrderSetPagination(CursorPagination):
    page_size = 10
    ordering = '-count'


class OrderViewSet(ModelViewSet):
    serializer_class = OrderSerializer
    pagination_class = OrderSetPagination
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = OlderFilterSet

    def get_queryset(self):
        return Order.objects.annotate(count=Count('order_lines'))


class ColorViewSet(ListModelMixin, GenericViewSet):
    serializer_class = ColorSerializer

    def get_queryset(self):
        return Color.objects.annotate(count_model=Count('order_lines')).order_by('count_model')


class BrandViewSet(ListModelMixin, GenericViewSet):
    serializer_class = BrandSerializer

    def get_queryset(self):
        return Brand.objects.annotate(count_brand=Count('models__order_lines')).order_by('count_brand')
