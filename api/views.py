# Third-party libraries
import hashlib

# Rest Framework
from rest_framework import status
from rest_framework.authentication import BaseAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied, NotFound
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_mongoengine import viewsets

# FPDF
from fpdf import FPDF
from django.http import HttpResponse

# Local app models
from .models import (
    AdminUser,
    MagazineSubscriber,
    PaymentMode,
    SubscriberCategory,
    SubscriberType,
    Subscription,
    SubscriptionLanguage,
    SubscriptionMode,
    SubscriptionPlan,
    UserToken,
)

# Local app serializers
from .serializers import (
    AdminUserSerializer,
    MagazineSubscriberSerializer,
    PaymentModeSerializer,
    SubscriberCategorySerializer,
    SubscriberTypeSerializer,
    SubscriptionLanguageSerializer,
    SubscriptionModeSerializer,
    SubscriptionPlanSerializer,
    SubscriptionSerializer,
)

class TokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token = request.data.get('token')  # Get the token from the request body
        print("Got called")
        if not token:
            return None  # No token provided, continue to other authentication methods

        # Validate the token
        user_token = UserToken.objects(token=token).first()
        if not user_token:
            raise AuthenticationFailed('Invalid token.')

        return (user_token.user, token)  # Return user and token if valid

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

    @action(detail=False, methods=['get'], url_path='search')
    def search(self, request):
        """
        Search subscribers based on a given filter and query.
        For example, if filter=name and query=Srihari, it will perform a case-insensitive search on the 'name' field.
        """
        search_filter = request.query_params.get('filter', None)
        query = request.query_params.get('query', None)
        queryset = self.get_queryset()

        if search_filter and query:
            # Use icontains for a case-insensitive partial match.
            filter_kwargs = {f"{search_filter}__icontains": query}
            queryset = queryset.filter(**filter_kwargs)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

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

    @action(detail=False, methods=['get'])
    def report(self, request):
        """
        Fetches filtered subscriber data and returns a formatted report.
        """
        # Get query parameters
        char_limit = int(request.query_params.get('char_limit', 42))
        subscriber_status = request.query_params.get('subscriberStatus', 'active')
        subscriber_type = request.query_params.get('subscriberType', None)
        subscriber_category = request.query_params.get('subscriberCategory', None)

        # Helper function to split an address into multiple lines based on character limit.
        def split_address(address, char_limit):
            if not address:
                return []
            lines = []
            while len(address) > char_limit:
                split_at = address[:char_limit].rfind(' ')
                if split_at == -1:  # If no space found, split at the char limit
                    split_at = char_limit
                lines.append(address[:split_at].strip())
                address = address[split_at:].strip()
            lines.append(address)
            return lines

        # Filter subscribers based on provided filters
        filters = {}
        if subscriber_status == 'active':
            filters['isDeleted'] = False
        elif subscriber_status == 'inactive':
            filters['isDeleted'] = True

        if subscriber_type:
            try:
                # Fetch the corresponding SubscriberType ID by name
                subscriber_type_obj = SubscriberType.objects.get(name=subscriber_type)
                filters['stype'] = subscriber_type_obj.id
            except SubscriberType.DoesNotExist:
                raise PermissionDenied(f"Invalid subscriber type: {subscriber_type}")

        if subscriber_category:
            try:
                # Fetch the corresponding SubscriberCategory ID by name
                subscriber_category_obj = SubscriberCategory.objects.get(name=subscriber_category)
                filters['category'] = subscriber_category_obj.id
            except SubscriberCategory.DoesNotExist:
                raise PermissionDenied(f"Invalid subscriber category: {subscriber_category}")

        # Fetch and process subscribers
        subscribers = self.get_queryset().filter(**filters)
        report = []
        for subscriber in subscribers:
            address_lines = split_address(subscriber.address, char_limit)
            report.append({
                "Name": subscriber.name,
                "Active": not subscriber.isDeleted,  # True for active, False for inactive
                "Category": subscriber.category.name if subscriber.category else "N/A",
                "Type": subscriber.stype.name if subscriber.stype else "N/A",
                "Address line 1": address_lines[0] if len(address_lines) > 0 else "",
                "Address line 2": address_lines[1] if len(address_lines) > 1 else "",
                "City": subscriber.city_town or "",
                "District": subscriber.district or "",
                "State": subscriber.state or "",
                "Pincode": subscriber.pincode or "",
                "Phone Number": subscriber.phone or "",
            })

        return Response(report, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def generate_pdf_report(self, request):
        """
        Generates a PDF report with subscriber data fetched from the database, skipping empty strings.
        Includes <status, category, type> in the header of each page.
        """
        try:
            # Fetch data from the report endpoint
            char_limit = int(request.query_params.get('char_limit', 42))
            subscriber_status = request.query_params.get('subscriberStatus', 'active')
            subscriber_type = request.query_params.get('subscriberType', None) or "ALL"
            subscriber_category = request.query_params.get('subscriberCategory', None) or "ALL"
            report_data = self.report(request).data  # Use the existing `report` function to fetch data

            # Initialize FPDF
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)

            def add_page_with_header():
                pdf.add_page()
                pdf.set_font("Arial", size=11, style='B')
                header = f"Status: {subscriber_status.capitalize()} | Category: {subscriber_category} | Type: {subscriber_type}"
                pdf.cell(0, 10, header, align='C', ln=True)
                pdf.ln(5)  # Add some space after the header to separate from the content

            add_page_with_header()  # Add the first page with the header

            # Set base font size and other layout parameters
            base_font_size = 11
            pdf.set_font("Arial", size=base_font_size)

            # Layout parameters
            page_width = 210  # A4 page width in mm
            page_height = 297  # A4 page height in mm
            margin = 10  # Page margin
            usable_width = page_width - 2 * margin
            usable_height = page_height - 2 * margin - 15  # Adjust for header
            column_width = usable_width / 2  # Two columns
            box_height = usable_height / 5  # Five rows per column

            # Draw table boundaries and add values
            for index, subscriber in enumerate(report_data):
                # Determine column and row positions for column-wise filling
                column = index % 2  # 0 = first column, 1 = second column
                row = (index // 2) % 5  # 5 rows per column

                # Start a new page after 10 entries (5 rows per column * 2 columns)
                if index > 0 and index % 10 == 0:
                    add_page_with_header()

                # Calculate position
                x_position = margin + (column * column_width)
                y_position = margin + (row * box_height) + 15  # Offset to avoid header overlap

                # Draw a rectangle for the boundary
                pdf.rect(x_position, y_position, column_width, box_height)

                # Handle None/null values
                def sanitize(value):
                    return str(value) if value not in [None, 'null', 'None', ""] else None

                # Write subscriber details inside the rectangle
                values = [
                    sanitize(subscriber.get("Name")),
                    sanitize(subscriber.get("Address line 1")),
                    sanitize(subscriber.get("Address line 2")),
                    sanitize(f"{subscriber.get('City', '')}, {subscriber.get('District', '')}".strip(", ")),
                    sanitize(f"{subscriber.get('State', '')}, {subscriber.get('Pincode', '')}".strip(", ")),
                    sanitize(subscriber.get("Phone Number")),
                ]
                current_y = y_position + 2  # Padding inside the rectangle
                pdf.set_xy(x_position + 2, current_y)  # Start writing with padding

                # Write the values, skipping empty ones
                for value in values:
                    if value:  # Skip empty strings or None
                        truncated_value = value[:char_limit - 3] + "..." if len(value) > char_limit else value
                        pdf.cell(column_width - 4, 7, truncated_value, ln=True)  # Reduced line height
                        pdf.set_xy(x_position + 2, pdf.get_y())

            # Output PDF to response
            pdf_output = pdf.output(dest='S').encode('latin1')
            return HttpResponse(
                pdf_output,
                content_type="application/pdf",
                headers={"Content-Disposition": 'attachment; filename="subscriber_report.pdf"'},
            )

        except Exception as e:
            # Handle errors gracefully
            return Response({"error": str(e)}, status=500)

    @action(detail=False, methods=['get'])
    def generate_report_dummy(self, request):
        """
        Generates a PDF report with distinct dummy subscriber data for testing purposes.
        """
        import random
        import string
        from fpdf import FPDF
        from django.http import HttpResponse
        from rest_framework.response import Response

        try:
            # Generate distinct dummy data
            def create_dummy_entry(index, category, stype):
                return {
                    "Name": f"Subscriber {index} " + ''.join(random.choices(string.ascii_uppercase, k=5)),
                    "Address line 1": f"{random.randint(1, 999)} Elm Street",
                    "Address line 2": f"Apartment {random.randint(1, 50)}B",
                    "City": f"City-{index}",
                    "District": f"District-{random.randint(1, 10)}",
                    "State": f"State-{random.randint(1, 5)}",
                    "Pincode": f"{random.randint(100000, 999999)}",
                    "Phone Number": f"{random.randint(100, 999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
                    "Category": category,
                    "Type": stype,
                }

            filters = [
                ("active", "Domestic", "Regular", 37),
                ("active", "NRI", "Donor", 41),
            ]

            # Generate distinct dummy data for each filter combination
            report_data = []
            for status, category, stype, count in filters:
                report_data += [create_dummy_entry(i + 1, category, stype) for i in range(count)]

            char_limit = int(request.query_params.get('char_limit', 42))
            cols = int(request.query_params.get('cols', 4))  # Default to 4 columns
            rows = int(request.query_params.get('rows', 6))  # Default to 6 rows

            # Initialize FPDF in landscape mode
            pdf = FPDF(orientation='L', unit='mm', format='A4')
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_font("Arial", size=8)  # Set font size to 9

            def add_page_with_header(status, category, stype):
                pdf.add_page()
                pdf.set_font("Arial", style='B', size=8)  # Header slightly larger
                header = f"Status: {status.capitalize()} | Category: {category or 'ALL'} | Type: {stype or 'ALL'}"
                pdf.cell(0, 10, header, align='C', ln=True)
                pdf.ln(5)

            # Layout parameters
            page_width = 297  # A4 landscape width in mm
            page_height = 210  # A4 landscape height in mm
            margin = 10  # Page margin
            usable_width = page_width - 2 * margin
            usable_height = page_height - 2 * margin - 10  # Adjust for header
            column_width = usable_width / cols
            box_height = usable_height / rows

            current_filter_index = 0  # Track current filter set
            entries_in_current_filter = 0  # Count entries per filter set

            for _, subscriber in enumerate(report_data):
                # Switch filter set when reaching its limit
                if (
                    (current_filter_index == 0 and entries_in_current_filter >= 37)
                    or (current_filter_index == 1 and entries_in_current_filter >= 41)
                ):
                    current_filter_index += 1
                    entries_in_current_filter = 0

                # Add a new page with the current filter's header
                if entries_in_current_filter % (cols * rows) == 0:  # Fit dynamically based on columns and rows
                    status, category, stype, _ = filters[current_filter_index]
                    add_page_with_header(status, category, stype)

                # Determine column and row positions
                column = entries_in_current_filter % cols
                row = (entries_in_current_filter // cols) % rows

                # Calculate position
                x_position = margin + (column * column_width)
                y_position = margin + (row * box_height) + 15  # Offset to avoid header overlap

                # Draw a rectangle for the boundary
                pdf.rect(x_position, y_position, column_width, box_height)

                # Handle None/null values
                def sanitize(value):
                    return str(value) if value not in [None, 'null', 'None', ""] else None

                # Write subscriber details inside the rectangle
                values = [
                    sanitize(subscriber.get("Name")),
                    sanitize(subscriber.get("Address line 1")),
                    sanitize(subscriber.get("Address line 2")),
                    sanitize(f"{subscriber.get('City', '')}, {subscriber.get('District', '')}".strip(", ")),
                    sanitize(f"{subscriber.get('State', '')}, {subscriber.get('Pincode', '')}".strip(", ")),
                    sanitize(subscriber.get("Phone Number")),
                ]
                current_y = y_position + 2  # Padding inside the rectangle
                pdf.set_xy(x_position + 2, current_y)  # Start writing with padding

                # Write the values, skipping empty ones
                for value in values:
                    if value:  # Skip empty strings or None
                        truncated_value = value[:char_limit - 3] + "..." if len(value) > char_limit else value
                        pdf.cell(column_width - 4, 3, truncated_value, ln=True)  # Reduced line height
                        pdf.set_xy(x_position + 2, pdf.get_y())

                entries_in_current_filter += 1  # Increment entries for the current filter set

            # Output PDF to response
            pdf_output = pdf.output(dest='S').encode('latin1')
            return HttpResponse(
                pdf_output,
                content_type="application/pdf",
                headers={"Content-Disposition": 'attachment; filename="subscriber_report.pdf"'},
            )

        except Exception as e:
            # Handle errors gracefully
            return Response({"error": str(e)}, status=500)


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

