import pytest
from django.urls import reverse

from cars.models import Order


@pytest.mark.django_db
def test_list(user_client, color_factory, brand_factory, car_model_factory, order_line_factory, order_factory):
    color_1 = color_factory()
    brand_1 = brand_factory()
    model_1 = car_model_factory(brand=brand_1)

    color_2 = color_factory()
    brand_2 = brand_factory()
    model_2 = car_model_factory(brand=brand_2)

    order_1 = order_factory()
    order_line_factory(order=order_1, model=model_1, color=color_1)
    order_line_factory(order=order_1, model=model_2, color=color_2)

    order_2 = order_factory()
    order_line_factory(order=order_2, model=model_1, color=color_1)

    response = user_client.get(reverse('orders-list'))

    assert response.status_code == 200
    assert response.json() == {
        'next': None,
        'previous': None,
        'results': [
            {'count': 2,
             'created_at': order_1.created_at,
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
             ]},
            {'count': 1,
             'created_at': order_2.created_at,
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
             ]},
        ]
    }


@pytest.mark.django_db
def test_list_pagination(user_client,
                         color_factory,
                         brand_factory,
                         car_model_factory,
                         order_line_factory,
                         order_factory):
    color = color_factory()
    brand = brand_factory()
    model = car_model_factory(brand=brand)

    order = order_factory()
    order_line_factory(order=order, color=color, model=model)

    order_factory.create_batch(15)
    response = user_client.get(reverse('orders-list'))

    assert Order.objects.count() == 16
    assert len(response.json()['results']) == 10

    response = user_client.get(response.json()['next'])
    assert len(response.json()['results']) == 6


@pytest.mark.django_db
def test_list_filter(user_client, color_factory, brand_factory, car_model_factory, order_line_factory, order_factory):
    color_1 = color_factory()
    brand_1 = brand_factory()
    model_1 = car_model_factory(brand=brand_1)

    color_2 = color_factory()
    brand_2 = brand_factory()
    model_2 = car_model_factory(brand=brand_2)

    order_1 = order_factory()
    order_line_factory(order=order_1, model=model_1, color=color_1)
    order_line_factory(order=order_1, model=model_2, color=color_2)

    order_2 = order_factory()
    order_line_factory(order=order_2, model=model_2, color=color_1)

    response = user_client.get(reverse('orders-list'), data={'name': model_1.brand.name})

    assert response.status_code == 200
    assert Order.objects.count() != len(response.json()['results'])
    assert response.json() == {
        'next': None,
        'previous': None,
        'results': [
            {'count': 2,
             'created_at': order_1.created_at,
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
             ]},
        ]
    }
