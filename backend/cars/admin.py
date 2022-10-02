from django.contrib import admin

from cars.models import Brand, CarModel, Color, Order, OrderLine

admin.site.register(Color)
admin.site.register(Brand)
admin.site.register(CarModel)
admin.site.register(Order)
admin.site.register(OrderLine)
