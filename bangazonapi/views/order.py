"""View module for handling requests about customer order"""

from django.db.models import Sum, F
from django.http import HttpResponseServerError
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import serializers, status
from rest_framework.decorators import action
from bangazonapi.models import Order, Customer, OrderProduct, Payment
from .product import ProductSerializer


class PaymentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ("id", "merchant_name")


class OrderLineItemSerializer(serializers.HyperlinkedModelSerializer):
    """JSON serializer for line items"""

    product = ProductSerializer(many=False)

    class Meta:
        model = OrderProduct
        url = serializers.HyperlinkedIdentityField(
            view_name="lineitem", lookup_field="id"
        )
        fields = ("id", "product")
        depth = 1


class OrderSerializer(serializers.HyperlinkedModelSerializer):
    """JSON serializer for customer orders"""

    lineitems = OrderLineItemSerializer(many=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    payment_type = PaymentTypeSerializer(read_only=True)

    class Meta:
        model = Order
        url = serializers.HyperlinkedIdentityField(view_name="order", lookup_field="id")
        fields = (
            "id",
            "url",
            "created_date",
            "payment_type",
            "customer",
            "lineitems",
            "total",
        )


class Orders(ViewSet):
    """View for interacting with customer orders"""

    def retrieve(self, request, pk=None):
        """
        @api {GET} /cart/:id GET single order
        @apiName GetOrder
        @apiGroup Orders

        @apiHeader {String} Authorization Auth token
        @apiHeaderExample {String} Authorization
            Token 9ba45f09651c5b0c404f37a2d2572c026c146611


        @apiSuccess (200) {id} id Order id
        @apiSuccess (200) {String} url Order URI
        @apiSuccess (200) {String} created_date Date order was created
        @apiSuccess (200) {String} payment_type Payment URI
        @apiSuccess (200) {String} customer Customer URI

        @apiSuccessExample {json} Success
            {
                "id": 1,
                "url": "http://localhost:8000/orders/1",
                "created_date": "2019-08-16",
                "payment_type": "http://localhost:8000/paymenttypes/1",
                "customer": "http://localhost:8000/customers/5"
            }
        """
        try:
            customer = Customer.objects.get(user=request.auth.user)
            order = (
                Order.objects.annotate(total=Sum(F("lineitems__product__price")))
                .select_related("payment_type")
                .get(pk=pk, customer=customer, payment_type__isnull=False)
            )
            serializer = OrderSerializer(order, context={"request": request})
            return Response(serializer.data)

        except Order.DoesNotExist as ex:
            return Response(
                {
                    "message": "The requested order does not exist, or you do not have permission to access it."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as ex:
            return HttpResponseServerError(ex)

    def update(self, request, pk=None):
        """
        @api {PUT} /order/:id PUT new payment for order
        @apiName AddPayment
        @apiGroup Orders

        @apiHeader {String} Authorization Auth token
        @apiHeaderExample {String} Authorization
            Token 9ba45f09651c5b0c404f37a2d2572c026c146611

        @apiParam {id} id Order Id route parameter
        @apiParam {id} payment_type Payment Id to pay for the order
        @apiParamExample {json} Input
            {
                "payment_type": 6
            }

        @apiSuccessExample {json} Success
            HTTP/1.1 204 No Content
        """
        customer = Customer.objects.get(user=request.auth.user)
        
        # Retrieve the order instance
        order = Order.objects.get(pk=pk, customer=customer)
        
        # Retrieve the Payment instance using the provided payment_type ID
        try:
            payment = Payment.objects.get(pk=request.data["payment_type"])
        except Payment.DoesNotExist:
            return Response({'message': 'Invalid payment type.'}, status=status.HTTP_400_BAD_REQUEST)

        # Assign the Payment instance to the order's payment_type field
        order.payment_type = payment
        order.save()

        return Response({}, status=status.HTTP_204_NO_CONTENT)


    def list(self, request):
        """
        @api {GET} /orders GET customer orders
        @apiName GetOrders
        @apiGroup Orders

        @apiHeader {String} Authorization Auth token
        @apiHeaderExample {String} Authorization
            Token 9ba45f09651c5b0c404f37a2d2572c026c146611

        @apiParam {id} payment_id Query param to filter by payment used

        @apiSuccess (200) {Object[]} orders Array of order objects
        @apiSuccess (200) {id} orders.id Order id
        @apiSuccess (200) {String} orders.url Order URI
        @apiSuccess (200) {String} orders.created_date Date order was created
        @apiSuccess (200) {String} orders.payment_type Payment URI
        @apiSuccess (200) {String} orders.customer Customer URI

        @apiSuccessExample {json} Success
            [
                {
                    "id": 1,
                    "url": "http://localhost:8000/orders/1",
                    "created_date": "2019-08-16",
                    "payment_type": "http://localhost:8000/paymenttypes/1",
                    "customer": "http://localhost:8000/customers/5"
                }
            ]
        """
        customer = Customer.objects.get(user=request.auth.user)
        orders = (
            Order.objects.filter(customer=customer, payment_type__isnull=False)
            .annotate(total=Sum(F("lineitems__product__price")))
            .select_related("payment_type")
            .order_by("-created_date")
        )

        payment = self.request.query_params.get("payment_id", None)
        if payment is not None:
            orders = orders.filter(payment__id=payment)

        json_orders = OrderSerializer(orders, many=True, context={"request": request})

        return Response(json_orders.data)
