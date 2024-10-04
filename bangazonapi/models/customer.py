from django.db import models
from django.contrib.auth.models import User
from .store import Store
from .favorite import Favorite


class Customer(models.Model):

    user = models.OneToOneField(User, on_delete=models.DO_NOTHING,)
    phone_number = models.CharField(max_length=15)
    address = models.CharField(max_length=55)
    favorited_stores = models.ManyToManyField(
        "Store",
        through="Favorite",
        related_name="fav_stores"
    )

    @property
    def recommends(self):
        return self.__recommends

    @recommends.setter
    def recommends(self, value):
        self.__recommends = value

    # def add_favorite_store(self, store):
    #     Favorite.objects.get_or_create(customer=self, store=store)

    # def remove_favorite_store(self, store):
    #     Favorite.objects.filter(customer=self, store=store).delete()