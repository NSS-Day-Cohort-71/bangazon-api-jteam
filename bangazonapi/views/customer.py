from django.http import HttpResponseServerError
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework import status
from bangazonapi.models import Customer
from rest_framework.decorators import action
from bangazonapi.models import Customer, Favorite
from django.shortcuts import render


class CustomerSerializer(serializers.HyperlinkedModelSerializer):
    """JSON serializer for customers"""
    class Meta:
        model = Customer
        url = serializers.HyperlinkedIdentityField(
            view_name='customer', lookup_field='id'
        )
        fields = ('id', 'url', 'user', 'phone_number', 'address')
        depth = 1


class Customers(ViewSet):
    queryset = Customer.objects.all()

    def update(self, request, pk=None):
        """
        @api {PUT} /customers/:id PUT changes to customer profile
        @apiName UpdateCustomer
        @apiGroup Customer

        @apiHeader {String} Authorization Auth token
        @apiHeaderExample {String} Authorization
            Token 9ba45f09651c5b0c404f37a2d2572c026c146611

        @apiParam {id} id Customer Id to update
        @apiSuccessExample {json} Success
            HTTP/1.1 204 No Content
        """
        customer = Customer.objects.get(user=request.auth.user)
        customer.user.last_name = request.data["last_name"]
        customer.user.email = request.data["email"]
        customer.address = request.data["address"]
        customer.phone_number = request.data["phone_number"]
        customer.user.save()
        customer.save()

        return Response({}, status=status.HTTP_204_NO_CONTENT)

    @action (detail=False, methods=['get'])
    def favorite_sellers_report(self, request):
        """Generates HTML report for a single customer's favorite stores"""

        customer_id = request.GET.get('customer')

        # Get the customer based on the passed customer_id
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found'}, status=404)
        
        # Get the customer's favorite stores through the Favorite model
        favorite_stores = Favorite.objects.filter(customer=customer).select_related('store__customer')

        # Create a list of dictionaries for the stores and their owners
        favorite_sellers = [
            {
                'name': favorite.store.name,
                'owner': f"{favorite.store.customer.user.first_name} {favorite.store.customer.user.last_name}"
            }
            for favorite in favorite_stores
        ]

        context = {
            'customer_name': f"{customer.user.first_name} {customer.user.last_name}",
            'favorite_sellers': favorite_sellers
        }

        return render(request, 'reports/favorite_sellers.html', context)