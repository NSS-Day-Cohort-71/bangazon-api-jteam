from rest_framework import serializers, viewsets
from django.contrib.auth.models import User
from bangazonapi.models import Store, Customer, StoreProduct
from rest_framework.response import Response
from rest_framework.decorators import action
from .product import ProductSerializer


class StoreOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
        )


class StoreSerializer(serializers.ModelSerializer):
    """JSON serializer"""

    customer = StoreOwnerSerializer(source="customer.user", read_only=True)
    products = serializers.SerializerMethodField()

    def get_products(self, obj):
        # Get all StoreProduct objects for this store
        store_products = StoreProduct.objects.filter(store=obj)
        # Extract the actual Product objects
        products = [sp.product for sp in store_products]
        return ProductSerializer(products, many=True, context={'request': self.context.get('request')}).data

    class Meta:
        model = Store
        fields = ("id", "customer", "name", "description", "products")
        read_only_fields = ["customer"]


class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    pagination_class = None

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        # Fetch the logged-in user's related customer instance
        customer = Customer.objects.get(user=self.request.user)
        serializer.save(customer=customer)

    @action(detail=True, methods=["post"])
    def favorite(self, request, pk=None):
        store = self.get_object()
        customer = Customer.objects.get(user=request.user)
        customer.add_favorite_store(store)
        return Response({"status": "store favorited"})

    @action(detail=True, methods=["post"])
    def unfavorite(self, request, pk=None):
        store = self.get_object()
        customer = Customer.objects.get(user=request.user)
        customer.remove_favorite_store(store)
        return Response({"status": "store unfavorited"})
