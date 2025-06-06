import mongoengine as me
from datetime import datetime, date
import calendar
from .utils import generate_id
import pytz
import uuid

class SubscriberCategory(me.Document):
    _id = me.StringField(primary_key=True, default=lambda: generate_id('SCAT', 'subscriber_category'))
    name = me.StringField(max_length=255, unique=True)

    meta = {'indexes': ['name']}

class SubscriberType(me.Document):
    _id = me.StringField(primary_key=True, default=lambda: generate_id('STYPE', 'subscriber_type'))
    name = me.StringField(max_length=255, unique=True)

    meta = {'indexes': ['name']}

class SubscriptionLanguage(me.Document):
    _id = me.StringField(primary_key=True, default=lambda: generate_id('SLANG', 'subscription_language'))
    name = me.StringField(max_length=50, unique=True)

    meta = {'indexes': ['name']}

class SubscriptionMode(me.Document):
    _id = me.StringField(primary_key=True, default=lambda: generate_id('SMODE', 'subscription_mode'))
    name = me.StringField(max_length=50, unique=True)

    meta = {'indexes': ['name']}

class SubscriptionPlan(me.Document):
    _id = me.StringField(primary_key=True, default=lambda: generate_id('SPLAN', 'subscription_plan'))
    version = me.StringField(max_length=10)
    name = me.StringField(max_length=255)
    start_date = me.DateField(required=True)
    subscription_price = me.DecimalField(required=True)
    subscription_language = me.ReferenceField(SubscriptionLanguage, required=True)
    subscription_mode = me.ReferenceField(SubscriptionMode, required=True)
    duration_in_months = me.IntField(required=True)

    meta = {
        'indexes': [
            'subscription_language',
            'subscription_mode',
            'duration_in_months',
            ('subscription_language', 'subscription_mode', 'duration_in_months', 'version')
        ]
    }

    def clean(self):
        if not self.subscription_language:
            raise ValueError("Subscription language must be set.")
        if not self.subscription_mode:
            raise ValueError("Subscription mode must be set.")
        if self.subscription_price <= 0:
            raise ValueError("Subscription price must be a positive number.")
        if self.duration_in_months <= 0:
            raise ValueError("Duration in months must be greater than zero.")

    def save(self, *args, **kwargs):
        self.clean()
        self.version = self.generate_version()
        self.name = f"{self.duration_in_months} months - {self.subscription_language.name} - {self.subscription_mode.name}"
        super().save(*args, **kwargs)

    def generate_version(self):
        existing_plans = SubscriptionPlan.objects(
            subscription_language=self.subscription_language,
            subscription_mode=self.subscription_mode,
            duration_in_months=self.duration_in_months
        ).order_by('-version').only('version', 'subscription_price')

        if existing_plans:
            latest_plan = existing_plans.first()
            if latest_plan.subscription_price == self.subscription_price:
                return latest_plan.version
            try:
                latest_version_number = int(latest_plan.version.lstrip('v'))
            except Exception:
                latest_version_number = 0
            return f"v{latest_version_number + 1}"
        return "v1"

class PaymentMode(me.Document):
    _id = me.StringField(primary_key=True, default=lambda: generate_id('PMODE', 'payment_mode'))
    name = me.StringField(max_length=255)
    details = me.StringField(max_length=400)

    meta = {'indexes': ['name']}

class MagazineSubscriber(me.Document):
    _id = me.StringField(primary_key=True, default=lambda: generate_id('SUBS', 'subscriber'))
    name = me.StringField(max_length=255, required=True)
    registration_number = me.StringField(max_length=255, unique=True, required=False)
    address = me.StringField(required=True)
    city_town = me.StringField(max_length=255, required=True)
    district = me.StringField(max_length=255, required=False)
    state = me.StringField(max_length=255, required=True)
    pincode = me.StringField(max_length=6, required=True)
    phone = me.StringField(max_length=10, required=True)
    email = me.EmailField(required=False)
    category = me.ReferenceField(SubscriberCategory, null=True, required=False)
    stype = me.ReferenceField(SubscriberType, null=True, required=False)
    notes = me.StringField(required=False)
    hasActiveSubscriptions = me.BooleanField(default=False, required=False)
    isDeleted = me.BooleanField(default=False, required=False)
    created_at = me.DateTimeField(default=datetime.utcnow)

    meta = {
        'indexes': ['registration_number', 'phone', 'email']
    }

    def get_subscriptions(self):
        # eager load subscription_plan & payment_mode to reduce queries downstream
        return Subscription.objects(subscriber=self).select_related('subscription_plan', 'payment_mode')

class Subscription(me.Document):
    _id = me.StringField(primary_key=True, default=lambda: generate_id('SUBSCR', 'subscription'))
    subscriber = me.ReferenceField(MagazineSubscriber, reverse_delete_rule=me.CASCADE)
    subscription_plan = me.ReferenceField(SubscriptionPlan, null=True)
    start_date = me.DateField(required=True)
    end_date = me.DateField()
    active = me.BooleanField(default=True)
    payment_status = me.StringField(max_length=50, choices=["Pending", "Paid", "Failed"], default="Pending")
    payment_mode = me.ReferenceField(PaymentMode, null=True)
    payment_id = me.StringField(max_length=100)
    payment_date = me.DateField(null=True)

    meta = {
        'indexes': [
            'subscriber',
            'subscription_plan',
            'active',
            'payment_status',
            ('subscriber', 'active')
        ]
    }

    def clean(self):
        if not self.start_date or not isinstance(self.start_date, date):
            self.start_date = self.calculate_start_date()
        self.end_date = self.calculate_end_date()
        self.active = self.end_date and date.today() <= self.end_date

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @classmethod
    def update_active_subscription_flag(cls, subscriber):
        now = datetime.now(pytz.timezone('Asia/Kolkata'))
        active_count = cls.objects(subscriber=subscriber, end_date__gte=now, active=True).count()
        if subscriber.hasActiveSubscriptions != (active_count > 0):
            subscriber.hasActiveSubscriptions = active_count > 0
            subscriber.save()

    def calculate_start_date(self):
        today = date.today()
        next_month = today.month + 1 if today.month < 12 else 1
        next_year = today.year if next_month != 1 else today.year + 1
        return date(next_year, next_month, 10)

    def calculate_end_date(self):
        duration = self.subscription_plan.duration_in_months if self.subscription_plan else 0
        start_date = self.start_date or date.today()
        end_year = start_date.year + ((start_date.month + duration - 1) // 12)
        end_month = (start_date.month + duration - 1) % 12 + 1
        last_day = calendar.monthrange(end_year, end_month)[1]
        return date(end_year, end_month, last_day)

class AdminUser(me.Document):
    _id = me.StringField(primary_key=True, default=lambda: generate_id('ADMIN', 'adminuser'))
    username = me.StringField(required=True, unique=True)
    password = me.StringField(required=True)  # Consider hashing in production
    email = me.StringField(required=True, unique=True)
    first_name = me.StringField(required=True)
    last_name = me.StringField(required=True)
    aadhaar = me.StringField(required=True, unique=True)
    mobile = me.StringField(required=True, unique=True)
    created_at = me.DateTimeField(default=datetime.utcnow)
    last_login = me.DateTimeField(null=True)
    active = me.BooleanField(default=True)

    meta = {
        'indexes': ['username', 'email', 'aadhaar', 'mobile']
    }

    def update_last_login(self):
        self.last_login = datetime.utcnow()
        self.save()

    def deactivate_account(self):
        self.active = False
        self.save()

    def activate_account(self):
        self.active = True
        self.save()

    def is_active(self):
        return self.active

class UserToken(me.Document):
    user = me.ReferenceField(AdminUser, required=True)
    token = me.StringField(required=True)

    @staticmethod
    def create_token(user):
        token = str(uuid.uuid4())
        UserToken(user=user, token=token).save()
        return token

    @staticmethod
    def get_user_by_token(token):
        user_token = UserToken.objects(token=token).first()
        return user_token.user if user_token else None