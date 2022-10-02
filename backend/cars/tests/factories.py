import factory
from django.contrib.auth.models import User

from cars.models import Brand, CarModel, Color, Order, OrderLine


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User


class BrandFactory(factory.django.DjangoModelFactory):
    name = factory.Faker('first_name')

    class Meta:
        model = Brand


class CarModelFactory(factory.django.DjangoModelFactory):
    brand = factory.SubFactory(BrandFactory)
    name = factory.Faker('first_name')

    class Meta:
        model = CarModel


class ColorFactory(factory.django.DjangoModelFactory):
    code = factory.Sequence(lambda n: n)
    name = factory.Faker('first_name')

    class Meta:
        model = Color


class OrderFactory(factory.django.DjangoModelFactory):
    created_at = factory.Faker('date')

    class Meta:
        model = Order


class OrderLineFactory(factory.django.DjangoModelFactory):
    model = factory.SubFactory(CarModelFactory)
    color = factory.SubFactory(ColorFactory)
    order = factory.SubFactory(OrderFactory)

    class Meta:
        model = OrderLine
