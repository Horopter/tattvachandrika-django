from rest_framework_mongoengine.serializers import DocumentSerializer
from rest_framework import serializers
from .models import MagazineSubscriber, Subscription, SubscriptionPlan, SubscriberCategory, SubscriberType, SubscriptionLanguage, SubscriptionMode, PaymentMode, AdminUser

class SubscriberCategorySerializer(DocumentSerializer):
    class Meta:
        model = SubscriberCategory
        fields = ('_id', 'name')

class SubscriberTypeSerializer(DocumentSerializer):
    class Meta:
        model = SubscriberType
        fields = ('_id', 'name')

class SubscriptionLanguageSerializer(DocumentSerializer):
    class Meta:
        model = SubscriptionLanguage
        fields = ('_id', 'name')

class SubscriptionModeSerializer(DocumentSerializer):
    class Meta:
        model = SubscriptionMode
        fields = ('_id', 'name')

class SubscriptionPlanSerializer(DocumentSerializer):
    subscription_language = serializers.PrimaryKeyRelatedField(queryset=SubscriptionLanguage.objects.all())
    subscription_mode = serializers.PrimaryKeyRelatedField(queryset=SubscriptionMode.objects.all())

    class Meta:
        model = SubscriptionPlan
        fields = ('_id', 'version', 'name', 'start_date', 'subscription_price', 'subscription_language', 'subscription_mode', 'duration_in_months')

class PaymentModeSerializer(DocumentSerializer):
    class Meta:
        model = PaymentMode
        fields = ['_id', 'name']
        
class SubscriptionSerializer(DocumentSerializer):
    subscription_plan = serializers.PrimaryKeyRelatedField(queryset=SubscriptionPlan.objects.all())
    payment_mode = serializers.PrimaryKeyRelatedField(queryset=PaymentMode.objects.all())

    class Meta:
        model = Subscription
        fields = '__all__'

    def validate(self, data):
        if 'subscription_plan' in data and isinstance(data['subscription_plan'], str):
            try:
                data['subscription_plan'] = SubscriptionPlan.objects.get(pk=data['subscription_plan'])
            except SubscriptionPlan.DoesNotExist:
                raise ValidationError({'subscription_plan': 'SubscriptionPlan matching query does not exist.'})
        if 'payment_mode' in data and isinstance(data['payment_mode'], str):
            try:
                data['payment_mode'] = PaymentMode.objects.get(pk=data['payment_mode'])
            except PaymentMode.DoesNotExist:
                raise ValidationError({'payment_mode': 'PaymentMode matching query does not exist.'})
        return data

class MagazineSubscriberSerializer(DocumentSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=SubscriberCategory.objects.all())
    stype = serializers.PrimaryKeyRelatedField(queryset=SubscriberType.objects.all())
    subscriptions = serializers.SerializerMethodField()
    
    def get_subscriptions(self, obj):
        subscriptions = Subscription.objects.filter(subscriber=obj)
        return SubscriptionSerializer(subscriptions, many=True).data

    class Meta:
        model = MagazineSubscriber
        fields = [
            '_id', 'name', 'registration_number', 'address', 'city_town',
            'state', 'pincode', 'phone', 'email', 'category', 'stype',
            'notes', 'hasActiveSubscriptions', 'isDeleted', 'subscriptions'
        ]

class AdminUserSerializer(DocumentSerializer):
    class Meta:
        model = AdminUser
        fields = [
            '_id', 'username', 'email', 'first_name', 'last_name', 'aadhaar', 'mobile',
            'created_at', 'last_login', 'active'
        ]