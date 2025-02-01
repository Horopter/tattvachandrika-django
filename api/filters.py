import django_filters
from .models import SubscriptionMode

class SubscriptionModeFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = SubscriptionMode
        fields = ['name']
