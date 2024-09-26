from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from safedelete.models import SafeDeleteModel
from safedelete.models import SOFT_DELETE
from .customer import Customer
from .productcategory import ProductCategory
from .orderproduct import OrderProduct
from .rating import Rating


class Product(SafeDeleteModel):

    _safedelete_policy = SOFT_DELETE
    name = models.CharField(max_length=50,)
    customer = models.ForeignKey(
        Customer, on_delete=models.DO_NOTHING, related_name='products')
    price = models.FloatField(
        validators=[MinValueValidator(0.00), MaxValueValidator(10000.00)],)
    description = models.CharField(max_length=255,)
    quantity = models.IntegerField(validators=[MinValueValidator(0)],)
    created_date = models.DateField(auto_now_add=True)
    category = models.ForeignKey(
        ProductCategory, on_delete=models.DO_NOTHING, related_name='products')
    location = models.CharField(max_length=50,)
    image_path = models.ImageField(
        upload_to='products', height_field=None,
        width_field=None, max_length=None, null=True)
    rating = models.ManyToManyField(
        "Rating",
        through="ProductRating"
    )

    @property
    def number_sold(self):
        """number_sold property of a product

        Returns:
            int -- Number items on completed orders
        """
        sold = OrderProduct.objects.filter(
            product=self, order__payment_type__isnull=False)
        return sold.count()

    @property
    def can_be_rated(self):
        """can_be_rated property, which will be calculated per user

        Returns:
            boolean -- If the user can rate the product or not
        """
        return self.__can_be_rated

    @can_be_rated.setter
    def can_be_rated(self, value):
        self.__can_be_rated = value

    @property
    def average_rating(self):
        """Average rating calculated attribute for each product

        Returns:
            number -- The average rating for the product
        """
        
        try:
            ratings = Rating.objects.filter(product=self)
            total_rating = 0
            for rating in ratings:
                total_rating += rating.score

            avg = total_rating / len(ratings)
            return avg
        except ZeroDivisionError:
            return 0
    
    @property
    def rating_count(self):
        """rating_count property
        Returns:
            int -- The number of ratings for the product
        """
        return self.rating.count()
    
    @property
    def number_of_likes(self):
        """Count the number of likes for this product

        Returns:
            int -- TAhe number of likes for the product
        """

        return self.likes.count()

    class Meta:
        verbose_name = ("product")
        verbose_name_plural = ("products")
