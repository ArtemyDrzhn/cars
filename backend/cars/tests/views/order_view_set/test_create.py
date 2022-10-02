import datetime

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_create(user_client, color_factory, brand_factory, car_model_factory):
    color_1 = color_factory()
    brand_1 = brand_factory()
    model_1 = car_model_factory(brand=brand_1)

    color_2 = color_factory()
    brand_2 = brand_factory()
    model_2 = car_model_factory(brand=brand_2)

    url = reverse('orders-list')
    response = user_client.post(
        url, data={
            'created_at': '2022-10-10',
            'order_lines': [
                {'color': color_1.pk, 'model': model_1.pk},
                {'color': color_2.pk, 'model': model_2.pk},
            ]
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        'created_at': '2022-10-10',
        'order_lines': [
            {
                'color': {
                    'code': color_1.code,
                    'name': color_1.name,
                },
                'model': {
                    'brand': model_1.brand.name,
                    'name': model_1.name,
                }
            },
            {
                'color': {
                    'code': color_2.code,
                    'name': color_2.name,
                },
                'model': {
                    'brand': model_2.brand.name,
                    'name': model_2.name,
                }
            },
        ]}


@pytest.mark.django_db
def test_create_with_empty_date(user_client, color_factory, brand_factory, car_model_factory):
    color_1 = color_factory()
    brand_1 = brand_factory()
    model_1 = car_model_factory(brand=brand_1)

    url = reverse('orders-list')
    response = user_client.post(
        url, data={'order_lines': [
            {'color': color_1.pk, 'model': model_1.pk},
        ]},
    )
    assert response.status_code == 201
    assert response.json() == {
        'created_at': str(datetime.datetime.today().date()),
        'order_lines': [
            {
                'color': {
                    'code': color_1.code,
                    'name': color_1.name,
                },
                'model': {
                    'brand': model_1.brand.name,
                    'name': model_1.name,
                },
            },
        ]}
