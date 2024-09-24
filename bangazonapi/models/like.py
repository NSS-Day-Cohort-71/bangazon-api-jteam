from django.db import models
from .customer import Customer


class Like(models.Model):

    customer = models.ForeignKey(
        Customer,
        on_delete=models.DO_NOTHING,
    )
    product = models.ForeignKey(
        "Product", on_delete=models.CASCADE, related_name="likes"
    )

    class Meta:
        verbose_name = "like"
        verbose_name_plural = "likes"
