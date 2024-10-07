from rest_framework import serializers, viewsets
from django.contrib.auth.models import User
from bangazonapi.models import Store, Customer, Favorite, StoreProduct, OrderProduct
from rest_framework.response import Response
from rest_framework.decorators import action
from django.http import HttpResponseServerError
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
    is_favorite = serializers.SerializerMethodField()
    products = serializers.SerializerMethodField()
    products_sold = serializers.SerializerMethodField()

    def get_products(self, obj):
        # Get all StoreProduct objects for this store
        store_products = StoreProduct.objects.filter(store=obj)
        # Extract the actual Product objects
        products = [sp.product for sp in store_products]
        return ProductSerializer(
            products, many=True, context={"request": self.context.get("request")}
        ).data
    
    def get_products_sold(self, obj):
        # Get all StoreProduct objects for this store
        store_products = StoreProduct.objects.filter(store=obj)
        
        # Get all products from this store that have been sold
        # (orders with non-null payment_type)
        sold_products = OrderProduct.objects.filter(
            product__in=[sp.product for sp in store_products],
            order__payment_type__isnull=False  # Check for non-null payment_type
        ).values_list('product', flat=True).distinct()
        
        # Get the actual Product objects
        products = [sp.product for sp in store_products if sp.product.id in sold_products]
        
        return ProductSerializer(
            products, many=True, context={"request": self.context.get("request")}
        ).data

    class Meta:
        model = Store
        fields = ("id", "customer", "name", "description", "products", "products_sold", "is_favorite")
        read_only_fields = ["customer"]
    
    def get_is_favorite(self, obj):
        """Check if the current user has favorited the store"""
        user = self.context['request'].user

        customer = Customer.objects.get(user=user)
        return Favorite.objects.filter(customer=customer, store=obj).exists()


class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    pagination_class = None

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def perform_create(self, serializer):
        # Fetch the logged-in user's related customer instance
        customer = Customer.objects.get(user=self.request.user)
        serializer.save(customer=customer)

    # @action(detail=True, methods=["post"])
    # def favorite(self, request, pk=None):
    #     store = self.get_object()
    #     customer = Customer.objects.get(user=request.user)
    #     customer.add_favorite_store(store)
    #     return Response({"status": "store favorited"})

    # @action(detail=True, methods=["post"])
    # def unfavorite(self, request, pk=None):
    #     store = self.get_object()
    #     customer = Customer.objects.get(user=request.user)
    #     customer.remove_favorite_store(store)
    #     return Response({"status": "store unfavorited"})

    
    def retrieve(self, request, pk=None):
        """
        GET request for a single store
        """
        try:
            store = Store.objects.get(pk=pk)
            serializer = StoreSerializer(store, context={"request": request})
            return Response(serializer.data)
        except Exception as ex:
            return HttpResponseServerError(ex)
    
    def list(self, request):
        """
        GET request for a single store
        """
        try:
            stores = Store.objects.all()
            serializer = StoreSerializer(stores, context={"request": request}, many=True)
            return Response(serializer.data)
        except Exception as ex:
            return HttpResponseServerError(ex)

