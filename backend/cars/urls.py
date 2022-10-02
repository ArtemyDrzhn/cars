from django.urls import include, path
from rest_framework import routers

from cars.views import BrandViewSet, ColorViewSet, OrderViewSet

router = routers.SimpleRouter()

router.register(r'', OrderViewSet, basename='orders')
router.register(r'colors/', ColorViewSet, basename='colors')
router.register(r'brands/', BrandViewSet, basename='brands')

urlpatterns = [
    path('orders/', include(router.urls)),
]
