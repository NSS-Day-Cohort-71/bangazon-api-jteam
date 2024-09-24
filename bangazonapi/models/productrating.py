from django.db import models


class ProductRating(models.Model):

    product = models.ForeignKey(
        "Product", on_delete=models.CASCADE, related_name="ratings"
    )
    rating = models.ForeignKey("Rating", on_delete=models.CASCADE)


    class Meta:
        verbose_name = "productrating"
        verbose_name_plural = "productratings"


        def __str__(self):
            return self.rating
