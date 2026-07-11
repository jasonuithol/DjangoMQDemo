from decimal import Decimal

import factory

from orders.models import Order


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    customer_name = factory.Faker("name")
    total_amount = factory.LazyFunction(lambda: Decimal("42.50"))
