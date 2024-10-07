"""View module for handling requests about customer profiles"""

from django.http import HttpResponseServerError
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from bangazonapi.models import (
    Customer,
    Product,
    Favorite,
    Recommendation,
    Like,
)
from .store import StoreSerializer


class UserSerializer(serializers.HyperlinkedModelSerializer):
    """JSON serializer for customer profile

    Arguments:
        serializers
    """

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "username")
        depth = 1


class CustomerSerializer(serializers.ModelSerializer):
    """JSON serializer for recommendation customers"""

    user = UserSerializer()

    class Meta:
        model = Customer
        fields = (
            "id",
            "user",
        )


class ProfileProductSerializer(serializers.ModelSerializer):
    """JSON serializer for products"""

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "image_path",
            "price",
            "description",
        )


class RecommenderSerializer(serializers.ModelSerializer):
    """JSON serializer for recommendations"""

    customer = CustomerSerializer()
    product = ProfileProductSerializer()

    class Meta:
        model = Recommendation
        fields = (
            "product",
            "customer",
        )


class ReceivedRecommendationSerializer(serializers.ModelSerializer):
    """JSON serializer for recommendations received by the user"""

    recommender = CustomerSerializer()
    product = ProfileProductSerializer()

    class Meta:
        model = Recommendation
        fields = ("product", "recommender")


class FavoriteUserSerializer(serializers.HyperlinkedModelSerializer):
    """JSON serializer for favorite sellers user

    Arguments:
        serializers
    """

    class Meta:
        model = User
        fields = ("first_name", "last_name", "username")
        depth = 1


class FavoriteSellerSerializer(serializers.HyperlinkedModelSerializer):
    """JSON serializer for favorite sellers

    Arguments:
        serializers
    """

    user = FavoriteUserSerializer(many=False)

    class Meta:
        model = Customer
        fields = (
            "id",
            "url",
            "user",
        )
        depth = 1


class FavoriteSerializer(serializers.ModelSerializer):
    """JSON serializer for favorites"""

    store = StoreSerializer()

    class Meta:
        model = Favorite
        fields = ("id", "store")


class LikeSerializer(serializers.ModelSerializer):
    """JSON serializer for liked products"""

    product = ProfileProductSerializer()

    class Meta:
        model = Like
        fields = ("id", "product")


class ProfileSerializer(serializers.ModelSerializer):
    """JSON serializer for customer profile

    Arguments:
        serializers
    """

    user = UserSerializer(many=False)
    recommends = RecommenderSerializer(many=True)  # Recommendations made by the user
    received_recommendations = ReceivedRecommendationSerializer(
        many=True
    )  # Recommendations made to the user
    favorites = FavoriteSerializer(many=True, source="favorite_stores")
    likes = LikeSerializer(many=True, source="like_set")
    store = StoreSerializer(many=False, read_only=True)

    class Meta:
        model = Customer
        fields = (
            "id",
            "url",
            "user",
            "phone_number",
            "address",
            "payment_types",
            "recommends",
            "received_recommendations",
            "favorites",
            "likes",
            "store",
        )
        depth = 1


class Profile(ViewSet):
    """Request handlers for user profile info in the Bangazon Platform"""

    permission_classes = (IsAuthenticatedOrReadOnly,)

    def list(self, request):
        """
        @api {GET} /profile GET user profile info
        @apiName GetProfile
        @apiGroup UserProfile

        @apiHeader {String} Authorization Auth token
        @apiHeaderExample {String} Authorization
            Token 9ba45f09651c5b0c404f37a2d2572c026c146611

        @apiSuccess (200) {Number} id Profile id
        @apiSuccess (200) {String} url URI of customer profile
        @apiSuccess (200) {Object} user Related user object
        @apiSuccess (200) {String} user.first_name Customer first name
        @apiSuccess (200) {String} user.last_name Customer last name
        @apiSuccess (200) {String} user.email Customer email
        @apiSuccess (200) {String} phone_number Customer phone number
        @apiSuccess (200) {String} address Customer address
        @apiSuccess (200) {Object[]} payment_types Array of user's payment types
        @apiSuccess (200) {Object[]} recommends Array of recommendations made by the user

        @apiSuccessExample {json} Success
            HTTP/1.1 200 OK
            {
                "id": 7,
                "url": "http://localhost:8000/customers/7",
                "user": {
                    "first_name": "Brenda",
                    "last_name": "Long",
                    "email": "brenda@brendalong.com"
                },
                "phone_number": "555-1212",
                "address": "100 Indefatiguable Way",
                "payment_types": [
                    {
                        "url": "http://localhost:8000/paymenttypes/3",
                        "deleted": null,
                        "merchant_name": "Visa",
                        "account_number": "fj0398fjw0g89434",
                        "expiration_date": "2020-03-01",
                        "create_date": "2019-03-11",
                        "customer": "http://localhost:8000/customers/7"
                    }
                ],
                "recommends": [
                    {
                        "product": {
                            "id": 32,
                            "name": "DB9"
                        },
                        "customer": {
                            "id": 5,
                            "user": {
                                "first_name": "Joe",
                                "last_name": "Shepherd",
                                "email": "joe@joeshepherd.com"
                            }
                        }
                    }
                ]
            }
        """
        try:
            current_user = Customer.objects.get(user=request.auth.user)
            # Recommendations made by the user
            current_user.recommends = Recommendation.objects.filter(
                recommender=current_user
            )
            # Recommendations made to the user
            current_user.received_recommendations = Recommendation.objects.filter(
                customer=current_user
            )

            serializer = ProfileSerializer(
                current_user, many=False, context={"request": request}
            )

            return Response(serializer.data)
        except Exception as ex:
            return HttpResponseServerError(ex)

    @action(methods=["get"], detail=False)
    def favoritesellers(self, request):
        """
        @api {GET} /profile/favoritesellers GET favorite sellers
        @apiName GetFavoriteSellers
        @apiGroup UserProfile

        @apiHeader {String} Authorization Auth token
        @apiHeaderExample {String} Authorization
            Token 9ba45f09651c5b0c404f37a2d2572c026c146611

        @apiSuccess (200) {id} id Favorite id
        @apiSuccess (200) {Object} seller Favorited seller
        @apiSuccess (200) {String} seller.url Seller URI
        @apiSuccess (200) {String} seller.phone_number Seller phone number
        @apiSuccess (200) {String} seller.address Seller address
        @apiSuccess (200) {String} seller.user Seller user profile URI
        @apiSuccessExample {json} Success
            [
                {
                    "id": 1,
                    "seller": {
                        "url": "http://localhost:8000/customers/5",
                        "phone_number": "555-1212",
                        "address": "100 Endless Way",
                        "user": "http://localhost:8000/users/6"
                    }
                },
                {
                    "id": 2,
                    "seller": {
                        "url": "http://localhost:8000/customers/6",
                        "phone_number": "555-1212",
                        "address": "100 Dauntless Way",
                        "user": "http://localhost:8000/users/7"
                    }
                },
                {
                    "id": 3,
                    "seller": {
                        "url": "http://localhost:8000/customers/7",
                        "phone_number": "555-1212",
                        "address": "100 Indefatiguable Way",
                        "user": "http://localhost:8000/users/8"
                    }
                }
            ]
        """
        customer = Customer.objects.get(user=request.auth.user)
        favorites = Favorite.objects.filter(customer=customer)

        serializer = FavoriteSerializer(
            favorites, many=True, context={"request": request}
        )
        return Response(serializer.data)
