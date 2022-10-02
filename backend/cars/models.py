from datetime import datetime

from django.db import models


class Color(models.Model):
    code = models.PositiveIntegerField()
    name = models.CharField(max_length=70)

    def __str__(self) -> str:
        return f'{self.code}-{self.name}'


class Brand(models.Model):
    name = models.CharField(max_length=70)

    def __str__(self) -> str:
        return f'{self.name}'


class CarModel(models.Model):
    name = models.CharField(max_length=70)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='models')

    def __str__(self) -> str:
        return f'{self.brand.name}-{self.name}'


class Order(models.Model):
    created_at = models.DateField(blank=True)

    def __str__(self) -> str:
        return f'Date: {self.created_at}'

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.today().date()
        return super().save(*args, **kwargs)


class OrderLine(models.Model):
    """
    This is the order line, that is, the car
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_lines')
    model = models.ForeignKey(CarModel, on_delete=models.CASCADE, related_name='order_lines')
    color = models.ForeignKey(Color, on_delete=models.CASCADE, related_name='order_lines')

    def __str__(self) -> str:
        return f'{self.model.name}-{self.color.name}-{self.order.created_at}'
