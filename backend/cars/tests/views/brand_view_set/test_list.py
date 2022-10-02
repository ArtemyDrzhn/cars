import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_list(user_client, color_factory, brand_factory, car_model_factory, order_line_factory, order_factory):
    color_1 = color_factory()
    brand_1 = brand_factory()
    model_1 = car_model_factory(brand=brand_1)
    model_2 = car_model_factory(brand=brand_1)

    brand_3 = brand_factory()
    model_3 = car_model_factory(brand=brand_3)

    order_1 = order_factory()
    order_line_factory(order=order_1, model=model_1, color=color_1)
    order_line_factory(order=order_1, model=model_2, color=color_1)
    order_line_factory(order=order_1, model=model_3, color=color_1)

    response = user_client.get(reverse('brands-list'))
    assert response.status_code == 200
    assert response.json() == [{'count_brand': 1, 'name': brand_3.name}, {'count_brand': 2, 'name': brand_1.name}]
