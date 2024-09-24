from django.db import models


class Favorite(models.Model):

    customer = models.ForeignKey(
        "Customer",
        on_delete=models.DO_NOTHING,
    )
    store = models.ForeignKey(
        "Store", on_delete=models.DO_NOTHING, related_name="favorited_store", null=True
    )
