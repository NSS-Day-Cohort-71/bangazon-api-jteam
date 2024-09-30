from rest_framework import serializers, viewsets
from bangazonapi.models import Store


class StoreSerializer(serializers.ModelSerializer):
    """JSON serializer"""

    class Meta:
        model = Store
        fields = (
            "id",
            "customer",
            "name",
            "description"
        )


class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
