import ast

from rest_framework import serializers

from cars import models
from cars.models import CarModel, Order, OrderLine


class ColorSerializer(serializers.ModelSerializer):
    count_model = serializers.IntegerField(read_only=True)

    class Meta:
        model = models.Color
        fields = ('count_model', 'code', 'name')


class BrandSerializer(serializers.ModelSerializer):
    count_brand = serializers.IntegerField(read_only=True)

    class Meta:
        model = models.Brand
        fields = ('count_brand', 'name')


class CarModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarModel
        fields = ('name', 'brand')


class OrderLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderLine
        fields = ('model', 'color')

    def to_representation(self, instance):
        result = super().to_representation(instance)
        result['model'] = {'brand': instance.model.brand.name, 'name': instance.model.name}
        result['color'] = {'code': instance.color.code, 'name': instance.color.name}
        return result


class ListOrderLineSerializer(serializers.ListSerializer):
    def get_value(self, dictionary):
        return [ast.literal_eval(order_line) for order_line in dictionary.getlist('order_lines')]


class OrderSerializer(serializers.ModelSerializer):
    order_lines = ListOrderLineSerializer(child=OrderLineSerializer())
    count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Order
        fields = ('count', 'order_lines', 'created_at')

    def create(self, validated_data):
        created_at = validated_data.get('created_at')
        order_lines = validated_data.get('order_lines')
        order = Order.objects.create(created_at=created_at)

        bulk_list = list()
        for order_line in order_lines:
            bulk_list.append(
                OrderLine(
                    order=order,
                    model=order_line.get('model'),
                    color=order_line.get('color')
                )
            )

        OrderLine.objects.bulk_create(bulk_list)
        return order

    def update(self, instance, validated_data):
        for order_line in validated_data.get('order_lines'):
            OrderLine.objects.update_or_create(
                defaults={'model': order_line['model'],
                          'color': order_line['color']
                          },
                order=instance
            )
        created_at = validated_data.get('created_at')
        if created_at:
            instance.created_at = created_at
            instance.save()
        return instance
