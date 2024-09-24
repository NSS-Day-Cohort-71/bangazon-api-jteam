from django.db import models


class StoreProduct(models.Model):

    store = models.ForeignKey(
        "Store",
        on_delete=models.DO_NOTHING,
    )

    product = models.ForeignKey(
        "Product",
        on_delete=models.DO_NOTHING,
    )
