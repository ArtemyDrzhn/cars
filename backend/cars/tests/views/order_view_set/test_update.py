import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_update(user_client, color_factory, brand_factory, car_model_factory, order_line_factory, order_factory):
    color = color_factory()
    brand = brand_factory()
    model = car_model_factory(brand=brand)

    update_color = color_factory()
    update_model = car_model_factory(brand=brand)

    order = order_factory()
    order_line_factory(order=order, model=model, color=color)

    response = user_client.patch(reverse('orders-detail', args=[order.pk]),
                                 data={'created_at': '1917-10-25',
                                       'order_lines': [{
                                           'color': update_color.pk,
                                           'model': update_model.pk
                                       }
                                       ]})

    assert response.status_code == 200
    assert response.json() == {'count': 1,
                               'created_at': '1917-10-25',
                               'order_lines': [{
                                   'color': {
                                       'code': update_color.code,
                                       'name': update_color.name
                                   },
                                   'model': {
                                       'brand': update_model.brand.name,
                                       'name': update_model.name
                                   }},
                               ]}
