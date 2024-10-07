from django.db import models


class Store(models.Model):

    customer = models.OneToOneField(
        "Customer", on_delete=models.DO_NOTHING, related_name="store"
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
