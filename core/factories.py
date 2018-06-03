import factory

from core.models import Bucket, TimeSpan


class BucketFactory(factory.django.DjangoModelFactory):
    title = factory.Faker('name')

    class Meta:
        model = Bucket


class TimeSpanFactory(factory.django.DjangoModelFactory):
    start = factory.Faker('date_time')
    end = factory.Faker('date_time')
    bucket = factory.SubFactory(BucketFactory)

    class Meta:
        model = TimeSpan
