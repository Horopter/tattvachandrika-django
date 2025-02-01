from rest_framework_mongoengine import viewsets
from rest_framework import status
from rest_framework.response import Response
from .models import UserToken, MagazineSubscriber, Subscription, SubscriptionPlan, SubscriberCategory, SubscriberType, SubscriptionLanguage, SubscriptionMode, PaymentMode, AdminUser
from .serializers import MagazineSubscriberSerializer, SubscriptionSerializer, SubscriptionPlanSerializer, SubscriberCategorySerializer, SubscriberTypeSerializer, SubscriptionLanguageSerializer, SubscriptionModeSerializer, PaymentModeSerializer, AdminUserSerializer
from rest_framework.decorators import action
import hashlib
from rest_framework.permissions import AllowAny
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

class TokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token = None
        
        # Try to extract token from Authorization header for all request methods
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]  # Extract the token
        else:
            # Fallback to request body for POST requests
            if request.method == 'POST':
                token = request.data.get('token')
            # If token not found in POST, or it's a different method (PUT, PATCH, DELETE)
            if request.method in ['PUT', 'PATCH', 'DELETE'] and not token:
                token = request.data.get('token')
        
        # If no token found at all
        if not token:
            raise AuthenticationFailed('Token is missing or invalid.')
        
        # Validate the token in the database (using your UserToken model)
        user_token = UserToken.objects(token=token).first()
        if not user_token:
            raise AuthenticationFailed('Invalid token.')

        # Return the user and token if it's valid
        return (user_token.user, token)

class SubscriberCategoryViewSet(viewsets.ModelViewSet):
    lookup_field = '_id'
    serializer_class = SubscriberCategorySerializer
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        return SubscriberCategory.objects.all()

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        filter_kwargs = {self.lookup_field: self.kwargs[self.lookup_field]}
        obj = queryset.get(**filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj

class SubscriberTypeViewSet(viewsets.ModelViewSet):
    lookup_field = '_id'
    serializer_class = SubscriberTypeSerializer
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        return SubscriberType.objects.all()

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        filter_kwargs = {self.lookup_field: self.kwargs[self.lookup_field]}
        obj = queryset.get(**filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj

class SubscriptionLanguageViewSet(viewsets.ModelViewSet):
    lookup_field = '_id'
    serializer_class = SubscriptionLanguageSerializer
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        return SubscriptionLanguage.objects.all()

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        filter_kwargs = {self.lookup_field: self.kwargs[self.lookup_field]}
        obj = queryset.get(**filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj

class SubscriptionModeViewSet(viewsets.ModelViewSet):
    lookup_field = '_id'
    serializer_class = SubscriptionModeSerializer
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        return SubscriptionMode.objects.all()

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        filter_kwargs = {self.lookup_field: self.kwargs[self.lookup_field]}
        obj = queryset.get(**filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj

class SubscriptionPlanViewSet(viewsets.ModelViewSet):
    lookup_field = '_id'
    serializer_class = SubscriptionPlanSerializer
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        return SubscriptionPlan.objects.all()

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        filter_kwargs = {self.lookup_field: self.kwargs[self.lookup_field]}
        obj = queryset.get(**filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj

class PaymentModeViewSet(viewsets.ModelViewSet):
    lookup_field = '_id'
    serializer_class = PaymentModeSerializer
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        return PaymentMode.objects.all()

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        filter_kwargs = {self.lookup_field: self.kwargs[self.lookup_field]}
        obj = queryset.get(**filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj


class MagazineSubscriberViewSet(viewsets.ModelViewSet):
    lookup_field = '_id'
    serializer_class = MagazineSubscriberSerializer
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        return MagazineSubscriber.objects.all()

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        filter_kwargs = {self.lookup_field: self.kwargs[self.lookup_field]}
        obj = queryset.get(**filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj

    @action(detail=True, methods=['post'])
    def activate(self, request, _id=None):
        try:
            subscriber = self.get_object()
            subscriber.isDeleted = False
            subscriber.save()
            return Response({'status': 'subscriber activated'}, status=status.HTTP_200_OK)
        except MagazineSubscriber.DoesNotExist:
            raise NotFound('Subscriber not found')

    def perform_destroy(self, instance):
        instance.isDeleted = True
        instance.save()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class SubscriptionViewSet(viewsets.ModelViewSet):
    lookup_field = '_id'
    serializer_class = SubscriptionSerializer
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        return Subscription.objects.all()

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        filter_kwargs = {self.lookup_field: self.kwargs[self.lookup_field]}
        obj = queryset.get(**filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj
        
    @action(detail=False, methods=['get'], url_path='by_subscriber/(?P<subscriber_id>[^/.]+)')
    def get_by_subscriber(self, request, subscriber_id=None):
        try:
            subscriptions = Subscription.objects.filter(subscriber=subscriber_id)
            serializer = self.get_serializer(subscriptions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Subscription.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)


class AdminUserViewSet(viewsets.ModelViewSet):
    serializer_class = AdminUserSerializer
    lookup_field = '_id'

    def get_queryset(self):
        """Return all admin users."""
        return AdminUser.objects.all()

    @action(detail=False, methods=['post'], url_path='signup')
    def signup(self, request):
        """Create a new admin user account."""
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        aadhaar = request.data.get('aadhaar')
        mobile = request.data.get('mobile')

        # Check for existing user
        if AdminUser.objects(username=username).first() or AdminUser.objects(email=email).first():
            return Response({"error": "Username or email already exists."}, status=status.HTTP_400_BAD_REQUEST)

        # Hash the password before saving
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Create new admin user
        new_user = AdminUser(
            username=username,
            password=hashed_password,
            email=email,
            first_name=first_name,
            last_name=last_name,
            aadhaar=aadhaar,
            mobile=mobile  
        )
        new_user.save()  # Save to MongoDB

        return Response(AdminUserSerializer(new_user).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='login', permission_classes=[AllowAny])
    def login(self, request):
        """Log in an admin user."""
        username = request.data.get('username')
        password = request.data.get('password')

        # Hash the password to compare
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        admin_user = AdminUser.objects(username=username, password=hashed_password).first()

        if admin_user:
            # Create a new token for the user
            token = UserToken.create_token(admin_user)  # Use the custom method to create a token

            # Update last login time
            admin_user.update_last_login()

            return Response({"token": token, "message": "Login successful!"}, status=status.HTTP_200_OK)

        return Response({"error": "Invalid username or password."}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='logout', permission_classes=[AllowAny])
    def logout(self, request):
        """Log out the admin user."""
        token = request.data.get('token')  # Get the token from the request body

        if token:
            # Attempt to delete the token from the database
            token_entry = UserToken.objects(token=token).first()
            if token_entry:
                token_entry.delete()  # Token exists, so delete it
                return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)
            return Response({"error": "Invalid token."}, status=status.HTTP_401_UNAUTHORIZED)

        return Response({"error": "Token not provided."}, status=status.HTTP_400_BAD_REQUEST)
