"""View module for handling requests about customer shopping cart"""

from django.db.models import Sum, F
from django.db.models.functions import Round
import datetime
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers
from bangazonapi.models import Order, Customer, Product, OrderProduct
from .product import ProductSerializer
from .order import OrderSerializer
from bangazonapi.models import Payment


class CartLineItemSerializer(serializers.HyperlinkedModelSerializer):
    """JSON serializer for line items"""

    product = ProductSerializer(many=False)

    class Meta:
        model = OrderProduct
        fields = ("id", "product")


class Cart(ViewSet):
    """Shopping cart for Bangazon eCommerce"""

    def create(self, request, pk=None):
        """
        @api {POST} /cart POST new line items to cart
        @apiName AddLineItem
        @apiGroup ShoppingCart

        @apiSuccessExample {json} Success
            HTTP/1.1 204 No Content
        @apiParam {Number} product_id Id of product to add
        """
        current_user = Customer.objects.get(user=request.auth.user)

        try:
            open_order = Order.objects.get(
                customer=current_user, payment_type__isnull=True
            )
        except Order.DoesNotExist as ex:
            open_order = Order()
            open_order.created_date = datetime.datetime.now()
            open_order.customer = current_user
            open_order.save()

        product_id = request.data.get("product_id")

        line_item = OrderProduct()
        line_item.product = Product.objects.get(pk=product_id)
        line_item.order = open_order
        line_item.save()

        serializer = CartLineItemSerializer(line_item, context={"request": request})

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        """
        @api {DELETE} /cart DELETE line item or empty cart
        @apiName RemoveFromCart
        @apiGroup ShoppingCart

        @apiParam {id} id Product Id to remove from cart
        @apiParam {Boolean} empty Whether to empty the entire cart
        @apiSuccessExample {json} Success
            HTTP/1.1 204 No Content
        """
        current_user = Customer.objects.get(user=request.auth.user)

        try:
            open_order = Order.objects.get(customer=current_user, payment_type=None)

            empty_cart = request.query_params.get("empty", False)

            if empty_cart:
                # Delete all line items in the cart
                OrderProduct.objects.filter(order=open_order).delete()
                open_order.delete()
            else:
                # Delete specific line item
                line_item = OrderProduct.objects.filter(
                    product__id=pk, order=open_order
                ).first()

                if line_item:
                    line_item.delete()
                else:
                    return Response(
                        {"message": "Item not found in cart."},
                        status=status.HTTP_404_NOT_FOUND,
                    )

            return Response({}, status=status.HTTP_204_NO_CONTENT)

        except Order.DoesNotExist:
            return Response(
                {"message": "No open order found."}, status=status.HTTP_404_NOT_FOUND
            )

    def list(self, request):
        """
        @api {GET} /cart GET line items in cart
        @apiName GetCart
        @apiGroup ShoppingCart

        @apiSuccess (200) {Number} id Order cart
        @apiSuccess (200) {String} url URL of order
        @apiSuccess (200) {String} created_date Date created
        @apiSuccess (200) {Object} payment_type Payment id use to complete order
        @apiSuccess (200) {String} customer URI for customer
        @apiSuccess (200) {Object[]} lineitems Line items in cart
        @apiSuccess (200) {Number} size Number of items in cart
        @apiSuccess (200) {Number} total Total price of items in cart
        """
        current_user = Customer.objects.get(user=request.auth.user)
        try:
            open_order = Order.objects.get(customer=current_user, payment_type=None)

            line_items = OrderProduct.objects.filter(order=open_order)

            serialized_order = OrderSerializer(
                open_order, many=False, context={"request": request}
            )

            line_item_serializer = CartLineItemSerializer(
                line_items, many=True, context={"request": request}
            )

            total_price = line_items.aggregate(total=Round(Sum(F("product__price")), 2))

            final = serialized_order.data
            final["lineitems"] = line_item_serializer.data
            final["size"] = len(line_items)
            final["total"] = total_price["total"] or 0

            return Response(final)

        except Order.DoesNotExist as ex:
            return Response({"message": ex.args[0]}, status=status.HTTP_404_NOT_FOUND)

    def retrieve(self, request, pk=None):
        """
        @api {GET} /cart/:id GET specific order in cart
        @apiName GetCartById
        @apiGroup ShoppingCart

        @apiParam {id} id Order Id to retrieve
        @apiSuccessExample {json} Success
            HTTP/1.1 200 OK
            {
                "id": 1,
                "url": "http://localhost:8000/orders/1",
                "created_date": "2024-10-02",
                "payment_type": null,
                "customer": "http://localhost:8000/customers/1",
                "lineitems": [...]
            }
        """
        current_user = Customer.objects.get(user=request.auth.user)

        try:
            # Fetch the specific order (cart) by ID and user
            open_order = Order.objects.get(
                pk=pk, customer=current_user, payment_type__isnull=True
            )

            # Serialize the order and return it
            serializer = OrderSerializer(open_order, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Order.DoesNotExist as ex:
            return Response(
                {"message": "Order not found."}, status=status.HTTP_404_NOT_FOUND
            )

    def update(self, request, pk=None):
        """
        @api {PUT} /cart/:id PUT payment type to complete order
        @apiName AddPaymentToCart
        @apiGroup ShoppingCart

        @apiParam {Number} id Order Id to complete
        @apiParam {Number} payment_type Payment type Id to add to order
        @apiSuccessExample {json} Success
            HTTP/1.1 204 No Content
        """
        current_user = Customer.objects.get(user=request.auth.user)

        try:
            # Get the open order for the customer
            open_order = Order.objects.get(
                pk=pk, customer=current_user, payment_type=None
            )

            # Get the payment type from the request
            payment_type_id = request.data.get("payment_type", None)
            if not payment_type_id:
                return Response(
                    {"message": "Payment type is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                payment = Payment.objects.get(pk=payment_type_id, customer=current_user)
            except Payment.DoesNotExist:
                return Response(
                    {"message": "Invalid payment type"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Assign the payment type to the open order to complete it
            open_order.payment_type = payment
            open_order.save()

            return Response({}, status=status.HTTP_204_NO_CONTENT)

        except Order.DoesNotExist:
            return Response(
                {"message": "Order not found or already completed"},
                status=status.HTTP_404_NOT_FOUND,
            )
