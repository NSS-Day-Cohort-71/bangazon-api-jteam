"""View module for handling requests about products"""

from rest_framework.decorators import action
import base64
from django.core.files.base import ContentFile
from django.http import HttpResponseServerError
from django.shortcuts import render
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from bangazonapi.models import (
    Product,
    Customer,
    ProductCategory,
    Rating,
    Recommendation,
    Like,
)


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ("id", "customer", "score", "rating_text")
        read_only_fields = ("customer",)


class ProductSerializer(serializers.ModelSerializer):
    """JSON serializer for products"""

    average_rating = serializers.ReadOnlyField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "price",
            "number_sold",
            "description",
            "quantity",
            "created_date",
            "location",
            "image_path",
            "average_rating",
            "can_be_rated",
            "rating_count",
            "number_of_likes",
            "is_liked",
        )
        depth = 1

    def get_is_liked(self, obj):
        """Check if the current user has liked the product"""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.likes.filter(customer__user=request.user).exists()
        return False


class Products(ViewSet):
    """Request handlers for Products in the Bangazon Platform"""

    permission_classes = (IsAuthenticatedOrReadOnly,)

    def create(self, request):
        """
        @api {POST} /products POST new product
        @apiName CreateProduct
        @apiGroup Product

        @apiHeader {String} Authorization Auth token
        @apiHeaderExample {String} Authorization
            Token 9ba45f09651c5b0c404f37a2d2572c026c146611

        @apiParam {String} name Short form name of product
        @apiParam {Number} price Cost of product
        @apiParam {String} description Long form description of product
        @apiParam {Number} quantity Number of items to sell
        @apiParam {String} location City where product is located
        @apiParam {Number} category_id Category of product
        @apiParamExample {json} Input
            {
                "name": "Kite",
                "price": 14.99,
                "description": "It flies high",
                "quantity": 60,
                "location": "Pittsburgh",
                "category_id": 4
            }

        @apiSuccess (200) {Object} product Created product
        @apiSuccess (200) {id} product.id Product Id
        @apiSuccess (200) {String} product.name Short form name of product
        @apiSuccess (200) {String} product.description Long form description of product
        @apiSuccess (200) {Number} product.price Cost of product
        @apiSuccess (200) {Number} product.quantity Number of items to sell
        @apiSuccess (200) {Date} product.created_date City where product is located
        @apiSuccess (200) {String} product.location City where product is located
        @apiSuccess (200) {String} product.image_path Path to product image
        @apiSuccess (200) {Number} product.average_rating Average customer rating of product
        @apiSuccess (200) {Number} product.number_sold How many items have been purchased
        @apiSuccess (200) {Object} product.category Category of product
        @apiSuccessExample {json} Success
            {
                "id": 101,
                "url": "http://localhost:8000/products/101",
                "name": "Kite",
                "price": 14.99,
                "number_sold": 0,
                "description": "It flies high",
                "quantity": 60,
                "created_date": "2019-10-23",
                "location": "Pittsburgh",
                "image_path": null,
                "average_rating": 0,
                "category": {
                    "url": "http://localhost:8000/productcategories/6",
                    "name": "Games/Toys"
                }
            }
        """
        # Create a serializer instance with the request data
        serializer = ProductSerializer(
            data={
                "name": request.data["name"],
                "price": request.data["price"],
                "description": request.data["description"],
                "quantity": request.data["quantity"],
                "location": request.data["location"],
            }
        )

        # This will run the validators
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # If validation passes, create the product
        new_product = Product()
        new_product.name = request.data["name"]
        new_product.price = request.data["price"]
        new_product.description = request.data["description"]
        new_product.quantity = request.data["quantity"]
        new_product.location = request.data["location"]

        customer = Customer.objects.get(user=request.auth.user)
        new_product.customer = customer

        product_category = ProductCategory.objects.get(pk=request.data["category_id"])
        new_product.category = product_category

        if "image_path" in request.data:
            format, imgstr = request.data["image_path"].split(";base64,")
            ext = format.split("/")[-1]
            data = ContentFile(
                base64.b64decode(imgstr),
                name=f'{new_product.id}-{request.data["name"]}.{ext}',
            )

            new_product.image_path = data

        new_product.save()

        serializer = ProductSerializer(new_product, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        """
        @api {GET} /products/:id GET product
        @apiName GetProduct
        @apiGroup Product

        @apiParam {id} id Product Id

        @apiSuccess (200) {Object} product Created product
        @apiSuccess (200) {id} product.id Product Id
        @apiSuccess (200) {String} product.name Short form name of product
        @apiSuccess (200) {String} product.description Long form description of product
        @apiSuccess (200) {Number} product.price Cost of product
        @apiSuccess (200) {Number} product.quantity Number of items to sell
        @apiSuccess (200) {Date} product.created_date City where product is located
        @apiSuccess (200) {String} product.location City where product is located
        @apiSuccess (200) {String} product.image_path Path to product image
        @apiSuccess (200) {Number} product.average_rating Average customer rating of product
        @apiSuccess (200) {Number} product.number_sold How many items have been purchased
        @apiSuccess (200) {Object} product.category Category of product
        @apiSuccessExample {json} Success
            {
                "id": 101,
                "url": "http://localhost:8000/products/101",
                "name": "Kite",
                "price": 14.99,
                "number_sold": 0,
                "description": "It flies high",
                "quantity": 60,
                "created_date": "2019-10-23",
                "location": "Pittsburgh",
                "image_path": null,
                "average_rating": 0,
                "category": {
                    "url": "http://localhost:8000/productcategories/6",
                    "name": "Games/Toys"
                }
            }
        """
        try:
            product = Product.objects.get(pk=pk)
            serializer = ProductSerializer(product, context={"request": request})
            return Response(serializer.data)
        except Exception as ex:
            return HttpResponseServerError(ex)

    def update(self, request, pk=None):
        """
        @api {PUT} /products/:id PUT changes to product
        @apiName UpdateProduct
        @apiGroup Product

        @apiHeader {String} Authorization Auth token
        @apiHeaderExample {String} Authorization
            Token 9ba45f09651c5b0c404f37a2d2572c026c146611

        @apiParam {id} id Product Id to update
        @apiSuccessExample {json} Success
            HTTP/1.1 204 No Content
        """
        product = Product.objects.get(pk=pk)
        product.name = request.data["name"]
        product.price = request.data["price"]
        product.description = request.data["description"]
        product.quantity = request.data["quantity"]
        product.created_date = request.data["created_date"]
        product.location = request.data["location"]

        customer = Customer.objects.get(user=request.auth.user)
        product.customer = customer

        product_category = ProductCategory.objects.get(pk=request.data["category_id"])
        product.category = product_category
        product.save()

        return Response({}, status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, pk=None):
        """
        @api {DELETE} /products/:id DELETE product
        @apiName DeleteProduct
        @apiGroup Product

        @apiHeader {String} Authorization Auth token
        @apiHeaderExample {String} Authorization
            Token 9ba45f09651c5b0c404f37a2d2572c026c146611

        @apiParam {id} id Product Id to delete
        @apiSuccessExample {json} Success
            HTTP/1.1 204 No Content
        """
        try:
            product = Product.objects.get(pk=pk)
            product.delete()

            return Response({}, status=status.HTTP_204_NO_CONTENT)

        except Product.DoesNotExist as ex:
            return Response({"message": ex.args[0]}, status=status.HTTP_404_NOT_FOUND)

        except Exception as ex:
            return Response(
                {"message": ex.args[0]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def list(self, request):
        """
        @api {GET} /products GET all products
        @apiName ListProducts
        @apiGroup Product

        @apiSuccess (200) {Object[]} products Array of products, grouped by category if no filters.
        """
        # Check if filters are applied
        filters_applied = any(
            param in request.query_params
            for param in [
                "category",
                "min_price",
                "name",
                "location",
                "quantity",
                "number_sold",
                "order_by",
                "direction",
            ]
        )

        if filters_applied:
            # Handle filtered products, no grouping by category
            products = Product.objects.all()

            category = request.query_params.get("category", None)
            min_price = request.query_params.get("min_price", None)
            name = request.query_params.get("name", None)
            location = request.query_params.get("location", None)
            quantity = request.query_params.get("quantity", None)
            number_sold = request.query_params.get("number_sold", None)
            order = request.query_params.get("order_by", None)
            direction = request.query_params.get("direction", None)

            if category is not None:
                products = products.filter(category__id=category)

            if min_price is not None:
                products = products.filter(price__gte=float(min_price))

            if name is not None:
                products = products.filter(name__contains=name)

            if location is not None:
                products = products.filter(location__contains=location)

            if quantity is not None:
                products = products.order_by("-created_date")[: int(quantity)]

            if number_sold is not None:
                products = products.filter(number_sold__gte=int(number_sold))

            if order is not None:
                order_filter = order
                if direction is not None and direction == "desc":
                    order_filter = f"-{order}"
                products = products.order_by(order_filter)

            serializer = ProductSerializer(
                products, many=True, context={"request": request}
            )
            return Response(
                {"header": "Products matching filters", "products": serializer.data}
            )

        else:
            # No filters applied, group products by category and return 5 most recent products per category
            categories = ProductCategory.objects.all()
            grouped_products = []

            for category in categories:
                # Get the 5 most recent products per category
                recent_products = Product.objects.filter(category=category).order_by(
                    "-created_date"
                )[:5]
                if recent_products:
                    grouped_products.append(
                        {
                            "category": category.name,
                            "products": ProductSerializer(
                                recent_products, many=True, context={"request": request}
                            ).data,
                        }
                    )

            return Response(grouped_products)

    @action(methods=["post"], detail=True, url_path="recommend")
    def recommend(self, request, pk=None):
        """Recommend products to other users"""
        if request.method == "POST":
            rec = Recommendation()
            rec.recommender = Customer.objects.get(user=request.auth.user)

            # Extract the 'customer' field from request.data
            user_id = request.data.get("customer")

            # Get the Customer instance using the user_id (not customer_id directly)
            try:
                recipient_customer = Customer.objects.get(id=user_id)
            except Customer.DoesNotExist:
                return Response(
                    {"message": "Recipient customer not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            rec.customer = recipient_customer
            rec.product = Product.objects.get(pk=pk)

            rec.save()

            return Response(None, status=status.HTTP_201_CREATED)

        return Response(None, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(methods=["post"], detail=True, url_path="rate-product")
    def rate_product(self, request, pk=None):
        """Add a rating to a product"""
        try:
            product = Product.objects.get(pk=pk)

            # Create the rating
            rating = Rating.objects.create(
                customer=request.auth.user.customer,
                score=request.data["score"],
                rating_text=request.data.get("rating_text", None),
            )

            # Associate the rating with the product
            product.rating.add(rating)

            serializer = RatingSerializer(rating)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Product.DoesNotExist:
            return Response(
                {"message": "Product does not exist."}, status=status.HTTP_404_NOT_FOUND
            )
        except KeyError as ex:
            return Response(
                {"message": f"Key {str(ex)} is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["get"], url_path="liked")
    def list_liked_products(self, request):
        """
        Handle GET requests to /products/liked to list products liked by the authenticated user.
        """
        try:
            # Get the customer (user) from the request
            customer = Customer.objects.get(user=request.auth.user)

            # Get the products liked by the authenticated user
            liked_products = Product.objects.filter(likes__customer=customer)

            # Serialize the liked products
            serializer = ProductSerializer(
                liked_products, many=True, context={"request": request}
            )

            # Return the serialized product data
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Customer.DoesNotExist:
            return Response(
                {"message": "Customer not found."}, status=status.HTTP_404_NOT_FOUND
            )

    @action(methods=["get"], detail=False, url_path="deleted")
    def deleted_products(self, request):
        """
        @api {GET} /products/deleted GET soft-deleted products
        @apiName GetDeletedProducts
        @apiGroup Product

        @apiSuccess (200) {Array} products List of soft-deleted products.
        """

        # Get only soft-deleted products
        deleted_products = Product.objects.deleted_only()

        serializer = ProductSerializer(
            deleted_products, many=True, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=["post", "delete"], detail=True, url_path="like")
    def like_unlike(self, request, pk=None):
        if request.method == "POST":
            try:
                product = Product.objects.get(pk=pk)
                customer = Customer.objects.get(user=request.auth.user)

                # Check if the customer has already liked this product
                if Like.objects.filter(product=product, customer=customer).exists():
                    return Response(
                        {"message": "Product already liked."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Create a new Like instance
                Like.objects.create(product=product, customer=customer)

                return Response(
                    {"message": "Product liked successfully."},
                    status=status.HTTP_201_CREATED,
                )

            except Product.DoesNotExist:
                return Response(
                    {"message": "Product not found."}, status=status.HTTP_404_NOT_FOUND
                )

        elif request.method == "DELETE":
            try:
                product = Product.objects.get(pk=pk)
                customer = Customer.objects.get(user=request.auth.user)

                # Check if the like exists
                like = Like.objects.filter(product=product, customer=customer).first()
                if not like:
                    return Response(
                        {"message": "Like not found."}, status=status.HTTP_404_NOT_FOUND
                    )

                # Delete the like
                like.delete()

                return Response(
                    {"message": "Product unliked successfully."},
                    status=status.HTTP_204_NO_CONTENT,
                )

            except Product.DoesNotExist:
                return Response(
                    {"message": "Product not found."}, status=status.HTTP_404_NOT_FOUND
                )


# Product Reports
def expensive_products_report(request):
    products = Product.objects.filter(price__gte=1000).order_by("-price")

    context = {
        "report_title": "Expensive Products Report",
        "report_description": "Products priced at $1000 or more",
        "products": products,
    }

    return render(request, "reports/price_report.html", context)


def inexpensive_products_report(request):
    products = Product.objects.filter(price__lt=1000).order_by("-price")

    context = {
        "report_title": "Inexpensive Products Report",
        "report_description": "Products priced at $999 or less",
        "products": products,
    }

    return render(request, "reports/price_report.html", context)
