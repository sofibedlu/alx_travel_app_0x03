from rest_framework import routers
from django.urls import path, include
from .views import ListingViewSet, BookingViewSet, PaymentViewSet, PaymentInitiateView, PaymentVerifyView

router = routers.DefaultRouter()
router.register(r'listings', ListingViewSet)
router.register(r'bookings', BookingViewSet)
router.register(r'payment-records', PaymentViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('payments/initiate/', PaymentInitiateView.as_view(), name='payment-initiate'),
    path('payments/verify/', PaymentVerifyView.as_view(), name='payment-verify'),
]