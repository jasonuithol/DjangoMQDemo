import factory

from integrations.models import WebhookEvent


class WebhookEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WebhookEvent

    payload = factory.LazyFunction(lambda: {"event": "order.updated", "id": "123"})
    processed = False
