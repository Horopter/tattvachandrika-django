import mongoengine as me
import datetime
import calendar
from .utils import generate_id
import pytz
import uuid  # To generate unique tokens

class SubscriberCategory(me.Document):
    _id = me.StringField(primary_key=True, default=lambda: generate_id('SCAT', 'subscriber_category'))
    name = me.StringField(max_length=255, unique=True)

class SubscriberType(me.Document):
    _id = me.StringField(primary_key=True, default=lambda: generate_id('STYPE', 'subscriber_type'))
    name = me.StringField(max_length=255, unique=True)

class SubscriptionLanguage(me.Document):
    _id = me.StringField(primary_key=True, default=lambda: generate_id('SLANG', 'subscription_language'))
    name = me.StringField(max_length=50, unique=True)

class SubscriptionMode(me.Document):
    _id = me.StringField(primary_key=True, default=lambda: generate_id('SMODE', 'subscription_mode'))
    name = me.StringField(max_length=50, unique=True)

class SubscriptionPlan(me.Document):
    _id = me.StringField(primary_key=True, default=lambda: generate_id('SPLAN', 'subscription_plan'))
    version = me.StringField(max_length=10)
    name = me.StringField(max_length=255)
    start_date = me.DateField()
    subscription_price = me.DecimalField()
    subscription_language = me.ReferenceField(SubscriptionLanguage, null=True)
    subscription_mode = me.ReferenceField(SubscriptionMode, null=True)
    duration_in_months = me.IntField()  # Duration in months

    def save(self, *args, **kwargs):
        self.version = self.generate_version()
        self.name = f"{self.duration_in_months} months - {self.subscription_language.name} - {self.subscription_mode.name}"
        super(SubscriptionPlan, self).save(*args, **kwargs)

    def generate_version(self):
        existing_plans = SubscriptionPlan.objects(
            subscription_language=self.subscription_language,
            subscription_mode=self.subscription_mode,
            duration_in_months=self.duration_in_months
        ).order_by('-version')

        if existing_plans:
            latest_plan = existing_plans.first()
            if latest_plan.subscription_price == self.subscription_price:
                return latest_plan.version
            else:
                latest_version_number = int(latest_plan.version[1:])
                return f"v{latest_version_number + 1}"
        else:
            return "v1"
            
class PaymentMode(me.Document):
    _id = me.StringField(primary_key=True, default=lambda: generate_id('PMODE', 'payment_mode'))
    name = me.StringField(max_length=255)

class MagazineSubscriber(me.Document):
    _id = me.StringField(primary_key=True, default=lambda: generate_id('SUBS', 'subscriber'))
    name = me.StringField(max_length=255)
    registration_number = me.StringField(max_length=255, unique=True)
    address = me.StringField()
    city_town = me.StringField(max_length=255)
    state = me.StringField(max_length=255)
    pincode = me.StringField(max_length=10)
    phone = me.StringField(max_length=15)
    email = me.EmailField(unique=True)
    category = me.ReferenceField(SubscriberCategory, null=True)
    stype = me.ReferenceField(SubscriberType, null=True)
    notes = me.StringField()
    hasActiveSubscriptions = me.BooleanField(default=False)
    isDeleted = me.BooleanField(default=False)
    
    def get_subscriptions(self):
        return Subscription.objects.filter(subscriber=self)

class Subscription(me.Document):
    _id = me.StringField(primary_key=True, default=lambda: generate_id('SUBSCR', 'subscription'))
    subscriber = me.ReferenceField(MagazineSubscriber, reverse_delete_rule=me.CASCADE)
    subscription_plan = me.ReferenceField(SubscriptionPlan, null=True)
    start_date = me.DateField()
    end_date = me.DateField()
    active = me.BooleanField(default=True)
    payment_status = me.StringField(max_length=50, choices=["Pending", "Paid", "Failed"], default="Pending")
    payment_mode = me.ReferenceField(PaymentMode, null=True)
    payment_date = me.DateField(null=True)

    def save(self, *args, **kwargs):
        self.start_date = self.calculate_start_date()
        self.end_date = self.calculate_end_date()
        super(Subscription, self).save(*args, **kwargs)
        # Update hasActiveSubscriptions
        now = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
        active_subs_count = Subscription.objects(subscriber=self.subscriber, end_date__gte=now, active=True).count()
        self.subscriber.hasActiveSubscriptions = active_subs_count > 0
        self.subscriber.save()

    def calculate_start_date(self):
        today = datetime.date.today()
        next_month = today.month + 1 if today.month < 12 else 1
        next_year = today.year if next_month != 1 else today.year + 1
        return datetime.date(next_year, next_month, 10)

    def calculate_end_date(self):
        duration = self.subscription_plan.duration_in_months
        start_date = self.start_date
        end_year = start_date.year + ((start_date.month + duration - 1) // 12)
        end_month = (start_date.month + duration - 1) % 12 + 1
        last_day_of_month = calendar.monthrange(end_year, end_month)[1]
        return datetime.date(end_year, end_month, last_day_of_month)
    
class AdminUser(me.Document):
    _id = me.StringField(primary_key=True, default=lambda: generate_id('ADMIN', 'adminuser'))
    username = me.StringField(required=True, unique=True)
    password = me.StringField(required=True)  # Consider using hashed passwords
    email = me.StringField(required=True, unique=True)
    first_name = me.StringField(required=True)
    last_name = me.StringField(required=True)
    aadhaar = me.StringField(required=True, unique=True)
    mobile = me.StringField(required=True, unique=True)
    created_at = me.DateTimeField(default=datetime.datetime.utcnow)
    last_login = me.DateTimeField(null=True)
    active = me.BooleanField(default=True)

    def save(self, *args, **kwargs):
        """Override save to check for any required conditions before saving."""
        # Call the original save method
        super(AdminUser, self).save(*args, **kwargs)

    def update_last_login(self):
        """Update last_login to current datetime when the user logs in."""
        now = datetime.datetime.now()
        self.last_login = now
        self.save()  # Save only the last_login field

    def deactivate_account(self):
        """ Deactivate the admin account. """
        self.active = False
        self.save()

    def activate_account(self):
        """ Activate the admin account. """
        self.active = True
        self.save()

    def is_active(self):
        """ Check if the admin user is active. """
        return self.active
    
class UserToken(me.Document):
    user = me.ReferenceField('AdminUser', required=True)  # Link to AdminUser
    token = me.StringField(required=True)

    @staticmethod
    def create_token(user):
        """Generate a new token for the user."""
        token = str(uuid.uuid4())  # Generate a random UUID as the token
        UserToken(user=user, token=token).save()  # Save the token to the database
        return token

    @staticmethod
    def get_user_by_token(token):
        """Retrieve the user associated with the token."""
        user_token = UserToken.objects(token=token).first()
        return user_token.user if user_token else None