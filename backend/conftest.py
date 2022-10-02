import pytest
from pytest_factoryboy import register
from rest_framework.test import APIClient

from cars.tests.factories import (
    BrandFactory,
    CarModelFactory,
    ColorFactory,
    OrderFactory,
    OrderLineFactory,
    UserFactory
)

register(UserFactory)
register(CarModelFactory)
register(BrandFactory)
register(ColorFactory)
register(OrderLineFactory)
register(OrderFactory)


@pytest.fixture()
def user(user_factory):
    return user_factory()


@pytest.fixture()
def user_client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client
