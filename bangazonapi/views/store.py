from rest_framework import serializers, viewsets
from bangazonapi.models import Store, Customer


class StoreSerializer(serializers.ModelSerializer):
    """JSON serializer"""

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
