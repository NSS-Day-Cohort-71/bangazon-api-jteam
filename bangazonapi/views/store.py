from rest_framework import serializers, viewsets
from django.contrib.auth.models import User
from bangazonapi.models import Store, Customer

class StoreOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "id", "first_name", "last_name"

class StoreSerializer(serializers.ModelSerializer):
    """JSON serializer"""

    customer = StoreOwnerSerializer(source="customer.user", read_only=True)

    class Meta:
        model = Store
        fields = (
            "id",
            "customer",
            "name",
            "description",
        )
        read_only_fields = ["customer"]


class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    pagination_class = None

    def perform_create(self, serializer):
        # Fetch the logged-in user's related customer instance
        customer = Customer.objects.get(user=self.request.user)
        serializer.save(customer=customer)
