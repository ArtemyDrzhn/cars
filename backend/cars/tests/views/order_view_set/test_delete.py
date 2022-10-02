import pytest
from django.urls import reverse

from cars.models import Order, OrderLine


@pytest.mark.django_db
def test_delete(user_client, color_factory, brand_factory, car_model_factory, order_line_factory, order_factory):
    color = color_factory()
    brand = brand_factory()
    model = car_model_factory(brand=brand)

    order = order_factory()
    order_line_factory(order=order, model=model, color=color)

    response = user_client.delete(reverse('orders-detail', args=[order.pk]))

    assert response.status_code == 204
    assert not Order.objects.exists()
    assert not OrderLine.objects.exists()
