from django.db import models
from django.conf import settings


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


    @property
    def is_favorite(self):
        """
        Favorited property for store
        Returns boolean for if the store is favorited by the logged in user or not
        """
        return self.__is_favorite
    
    @is_favorite.setter
    def is_favorite(self, value):
        self.__is_favorite = value

    class Meta:
        verbose_name = "store"
        verbose_name_plural = "stores"
