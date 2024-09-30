from rest_framework import serializers, viewsets
from bangazonapi.models import Store


class StoreSerializer(serializers.ModelSerializer):
    """JSON serializer"""

    class Meta:
        model = Store
        fields = (
            "id",
            "customer",  # Still return customer in the response
            "name",
            "description",
        )
        read_only_fields = ["customer"]  # Ensure customer is read-only


class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    pagination_class = None

    def perform_create(self, serializer):
        # Automatically set the customer to the logged-in user (assuming related)
        customer = (
            self.request.user.customer
        )  # Adjust if needed based on your user model
        serializer.save(customer=customer)  # Save with the correct customer
