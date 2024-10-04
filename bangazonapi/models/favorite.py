from django.db import models


class Favorite(models.Model):

    customer = models.ForeignKey(
        "Customer",
        on_delete=models.DO_NOTHING,
        related_name="favorite_stores"
    )
    store = models.ForeignKey(
        "Store", 
        on_delete=models.DO_NOTHING, 
        related_name="favorited_by_customers"
    )
