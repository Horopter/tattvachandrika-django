from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AdminUserViewSet, MagazineSubscriberViewSet, SubscriptionViewSet, SubscriptionPlanViewSet, SubscriberCategoryViewSet, SubscriberTypeViewSet, SubscriptionLanguageViewSet, SubscriptionModeViewSet, PaymentModeViewSet

router = DefaultRouter()
router.register(r'subscribers', MagazineSubscriberViewSet, basename='subscriber')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'subscription-plans', SubscriptionPlanViewSet, basename='subscriptionplan')
router.register(r'subscriber-categories', SubscriberCategoryViewSet, basename='subscribercategory')
router.register(r'subscriber-types', SubscriberTypeViewSet, basename='subscribertype')
router.register(r'subscription-languages', SubscriptionLanguageViewSet, basename='subscriptionlanguage')
router.register(r'subscription-modes', SubscriptionModeViewSet, basename='subscriptionmode')
router.register(r'payment-modes', PaymentModeViewSet, basename='paymentmode')
router.register(r'adminusers', AdminUserViewSet, basename='adminuser')

from django.http import HttpResponse

def empty_favicon(request):
    return HttpResponse(status=204)

urlpatterns = [
    path('', include(router.urls)),
    path('favicon.ico', empty_favicon),
]
