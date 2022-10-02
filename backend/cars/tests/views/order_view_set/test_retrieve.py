import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_retrieve(user_client, color_factory, brand_factory, car_model_factory, order_line_factory, order_factory):
    color_1 = color_factory()
    brand_1 = brand_factory()
    model_1 = car_model_factory(brand=brand_1)

    color_2 = color_factory()
    brand_2 = brand_factory()
    model_2 = car_model_factory(brand=brand_2)

    order = order_factory()
    order_line_factory(order=order, model=model_1, color=color_1)
    order_line_factory(order=order, model=model_2, color=color_2)

    response = user_client.get(reverse('orders-detail', args=[order.pk]))

    assert response.status_code == 200
    assert response.json() == {'count': 2,
                               'created_at': order.created_at,
                               'order_lines': [
                                   {
                                       'color': {
                                           'code': color_1.code,
                                           'name': color_1.name
                                       },
                                       'model': {
                                           'brand': model_1.brand.name,
                                           'name': model_1.name
                                       }
                                   },
                                   {
                                       'color': {
                                           'code': color_2.code,
                                           'name': color_2.name
                                       },
                                       'model': {
                                           'brand': model_2.brand.name,
                                           'name': model_2.name
                                       }
                                   },
                               ]}
