from rest_framework_mongoengine.serializers import DocumentSerializer
from rest_framework import serializers
from .models import MagazineSubscriber, Subscription, SubscriptionPlan, SubscriberCategory, SubscriberType, SubscriptionLanguage, SubscriptionMode, PaymentMode, AdminUser

class SubscriberCategorySerializer(DocumentSerializer):
    _id = serializers.CharField(read_only=True)
    class Meta:
        model = SubscriberCategory
        fields = ('_id', 'name')

class SubscriberTypeSerializer(DocumentSerializer):
    _id = serializers.CharField(read_only=True)
    class Meta:
        model = SubscriberType
        fields = ('_id', 'name')

class SubscriptionLanguageSerializer(DocumentSerializer):
    _id = serializers.CharField(read_only=True)
    class Meta:
        model = SubscriptionLanguage
        fields = ('_id', 'name')

class SubscriptionModeSerializer(DocumentSerializer):
    _id = serializers.CharField(read_only=True)
    class Meta:
        model = SubscriptionMode
        fields = ('_id', 'name')

class SubscriptionPlanSerializer(DocumentSerializer):
    _id = serializers.CharField(read_only=True)
    subscription_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)  # Ensure price is required and has valid decimal format
    duration_in_months = serializers.IntegerField(required=True, min_value=1)  # Ensure duration is required and greater than 0
    
    subscription_language = serializers.PrimaryKeyRelatedField(queryset=SubscriptionLanguage.objects.all())
    subscription_mode = serializers.PrimaryKeyRelatedField(queryset=SubscriptionMode.objects.all())

    class Meta:
        model = SubscriptionPlan
        fields = ('_id', 'version', 'name', 'start_date', 'subscription_price', 'subscription_language', 'subscription_mode', 'duration_in_months')

    def validate(self, data):
        # Check for valid duration_in_months
        duration = data.get('duration_in_months', None)
        if duration is None:
            if self.partial:  # Allow None for partial updates
                return data
            raise serializers.ValidationError("Duration in months is required.")
        
        if duration <= 0:
            raise serializers.ValidationError({"duration_in_months": f"Duration in months must be greater than zero. {data.get('duration_in_months', None)}"})
        
        # Check for valid subscription_price
        price = data.get('subscription_price', None)
        if price is None:
            if self.partial:  # Allow None for partial updates
                return data
            raise serializers.ValidationError("Price is required.")
        
        if price <= 0:
            raise serializers.ValidationError({"subscription_price": "Subscription price must be a positive number."})
        
        return data


class PaymentModeSerializer(DocumentSerializer):
    _id = serializers.CharField(read_only=True)
    class Meta:
        model = PaymentMode
        fields = ['_id', 'name']

    def validate(self, data):
        if 'name' not in data or not data['name']:
            raise serializers.ValidationError({'name': 'This field is required.'})
        return data
        
class SubscriptionSerializer(DocumentSerializer):
    _id = serializers.CharField(read_only=True)
    subscription_plan = serializers.PrimaryKeyRelatedField(queryset=SubscriptionPlan.objects.all())
    payment_mode = serializers.PrimaryKeyRelatedField(queryset=PaymentMode.objects.all())

    class Meta:
        model = Subscription
        fields = '__all__'

    def validate(self, data):
        # Validate payment_mode
        payment_mode_id = data.get('payment_mode')
        if payment_mode_id and PaymentMode.objects.filter(pk=payment_mode_id.pk).count() == 0:
            raise serializers.ValidationError({"payment_mode": "Payment mode does not exist."})

        # Validate subscription_plan
        subscription_plan_id = data.get('subscription_plan')
        if subscription_plan_id and SubscriptionPlan.objects.filter(pk=subscription_plan_id.pk).count() == 0:
            raise serializers.ValidationError({"subscription_plan": "Subscription plan does not exist."})

        # Validate date logic
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        if start_date and end_date and end_date <= start_date:
            raise serializers.ValidationError({"end_date": "End date must be after start date."})

        # Check for duplicate subscriptions (exclude self.instance if updating)
        subscriber = data.get('subscriber')
        if subscriber and subscription_plan_id:
            qs = Subscription.objects.filter(
                subscriber=subscriber, subscription_plan=subscription_plan_id
            )
            if self.instance:
                qs = qs.filter(_id__ne=self.instance.id)
            if qs.count() > 0:
                raise serializers.ValidationError("Duplicate subscription not allowed.")

        return data

class MagazineSubscriberSerializer(DocumentSerializer):
    _id = serializers.CharField(read_only=True)
    category = serializers.PrimaryKeyRelatedField(
        queryset=SubscriberCategory.objects.all(),
        required=True
    )
    stype = serializers.PrimaryKeyRelatedField(
        queryset=SubscriberType.objects.all(),
        required=True
    )
    address = serializers.CharField(required=True)
    city_town = serializers.CharField(required=True)
    state = serializers.CharField(required=True)
    pincode = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    hasActiveSubscriptions = serializers.BooleanField(required=False)
    isDeleted = serializers.BooleanField(required=False)
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