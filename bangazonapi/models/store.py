from django.db import models
from .customer import Customer


class Store(models.Model):

    customer = models.ForeignKey(
        Customer,
        on_delete=models.DO_NOTHING, 
    )
    name = models.CharField(
        max_length=255,
    )
    description = models.CharField(
        max_length=255,
    )

    class Meta:
        verbose_name = "store"
        verbose_name_plural = "stores"
