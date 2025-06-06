from rest_framework_mongoengine.serializers import DocumentSerializer
from rest_framework import serializers
from .models import MagazineSubscriber, Subscription, SubscriptionPlan, SubscriberCategory, SubscriberType, SubscriptionLanguage, SubscriptionMode, PaymentMode, AdminUser
from datetime import date, datetime

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
    subscription_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    duration_in_months = serializers.IntegerField(required=True, min_value=1)

    subscription_language = serializers.PrimaryKeyRelatedField(queryset=SubscriptionLanguage.objects.all())
    subscription_mode = serializers.PrimaryKeyRelatedField(queryset=SubscriptionMode.objects.all())

    class Meta:
        model = SubscriptionPlan
        fields = ('_id', 'version', 'name', 'start_date', 'subscription_price', 'subscription_language', 'subscription_mode', 'duration_in_months')

    def validate(self, data):
        duration = data.get('duration_in_months', None)
        if duration is None and not self.partial:
            raise serializers.ValidationError("Duration in months is required.")
        if duration is not None and duration <= 0:
            raise serializers.ValidationError({"duration_in_months": "Duration in months must be greater than zero."})

        price = data.get('subscription_price', None)
        if price is None and not self.partial:
            raise serializers.ValidationError("Price is required.")
        if price is not None and price <= 0:
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
    payment_id = serializers.CharField(required=True)

    class Meta:
        model = Subscription
        fields = '__all__'

    def validate(self, data):
        payment_mode_obj = data.get('payment_mode')
        if payment_mode_obj and not PaymentMode.objects.filter(pk=payment_mode_obj.pk).exists():
            raise serializers.ValidationError({"payment_mode": "Payment mode does not exist."})

        subscription_plan_obj = data.get('subscription_plan')
        if subscription_plan_obj and not SubscriptionPlan.objects.filter(pk=subscription_plan_obj.pk).exists():
            raise serializers.ValidationError({"subscription_plan": "Subscription plan does not exist."})

        payment_date_str = data.get('payment_date')
        if payment_date_str:
            try:
                payment_date = datetime.strptime(payment_date_str, "%Y-%m-%d").date()
                if payment_date > date.today():
                    raise serializers.ValidationError("Payment date cannot be in the future.")
            except ValueError:
                raise serializers.ValidationError("Invalid payment date. Make sure it's in YYYY-MM-DD format and not a future date.")

        start_date = data.get('start_date')
        end_date = data.get('end_date')
        if start_date and end_date and end_date <= start_date:
            raise serializers.ValidationError({"end_date": "End date must be after start date."})

        subscriber = data.get('subscriber')
        if subscriber and subscription_plan_obj and start_date and end_date:
            overlap_qs = Subscription.objects.filter(
                subscriber=subscriber,
                subscription_plan=subscription_plan_obj,
                start_date__lte=end_date,
                end_date__gte=start_date
            )
            if self.instance:
                overlap_qs = overlap_qs.filter(_id__ne=self.instance.id)
            if overlap_qs.count() > 0:
                raise serializers.ValidationError("Duplicate subscription not allowed due to overlapping dates.")

        # Check for exact duplicates (exclude current instance)
        if subscriber and subscription_plan_obj and start_date and end_date:
            dup_qs = Subscription.objects.filter(
                subscriber=subscriber,
                subscription_plan=subscription_plan_obj,
                start_date=start_date,
                end_date=end_date
            )
            if self.instance:
                dup_qs = dup_qs.filter(_id__ne=self.instance.id)
            if dup_qs.count() > 0:
                raise serializers.ValidationError("Duplicate subscription not allowed.")

        # Set active flag automatically
        if end_date:
            data["active"] = date.today() <= end_date
        else:
            data["active"] = True

        return data


class MagazineSubscriberSerializer(DocumentSerializer):
    _id = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    category = serializers.PrimaryKeyRelatedField(queryset=SubscriberCategory.objects.all(), required=True)
    stype = serializers.PrimaryKeyRelatedField(queryset=SubscriberType.objects.all(), required=True)
    email = serializers.CharField(required=False, allow_blank=True, allow_null=True)
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
        # Optimize by limiting to last 10 subscriptions (adjust as needed)
        subscriptions = Subscription.objects.filter(subscriber=obj).order_by('-start_date')[:10]
        return SubscriptionSerializer(subscriptions, many=True).data

    class Meta:
        model = MagazineSubscriber
        fields = [
            '_id', 'name', 'registration_number', 'address', 'city_town',
            'state', 'pincode', 'phone', 'email', 'category', 'stype',
            'notes', 'hasActiveSubscriptions', 'isDeleted', 'subscriptions',
            'created_at'
        ]


class AdminUserSerializer(DocumentSerializer):
    class Meta:
        model = AdminUser
        fields = [
            '_id', 'username', 'email', 'first_name', 'last_name', 'aadhaar', 'mobile',
            'created_at', 'last_login', 'active'
        ]
