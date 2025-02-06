from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Listing, Booking, Payment
from .serializers import ListingSerializer, BookingSerializer, PaymentSerializer
import requests, os
import uuid

class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

class PaymentInitiateView(APIView):
    """
    Initiate a payment via Chapa API.
    Expected request data includes booking_id and amount.
    """

    def post(self, request):
        booking_id = request.data.get("booking_id")
        amount = request.data.get("amount")
        try:
            booking = Booking.objects.get(booking_id=booking_id)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found"}, status=status.HTTP_404_NOT_FOUND)

        # Generate a unique transaction reference
        tx_ref = f"tx-{uuid.uuid4()}"

        # Prepare payload for Chapa including required fields
        payload = {
            "amount": str(amount),
            "currency": "ETB",
            "email": booking.user.email,
            "first_name": booking.user.first_name if hasattr(booking.user, 'first_name') else "Guest",
            "last_name": booking.user.last_name if hasattr(booking.user, 'last_name') else "User",
            "phone_number": "0000000000",  # Override with an actual number if available
            "tx_ref": tx_ref,
            "callback_url": "http://localhost:8000/api/payments/verify",
            #"return_url": "http://localhost:3000/payment-success",  # or any return url for UI
            "customization": {
                "title": f"Payment",
                "description": "Payment for your travel booking",
                "logo": None
            }
        }

        chapa_secret_key = os.environ.get("CHAPA_SECRET_KEY")
        headers = {
            "Authorization": f"Bearer {chapa_secret_key}",
            "Content-Type": "application/json",
        }
        # Call Chapa API to initialize the transaction
        response = requests.post("https://api.chapa.co/v1/transaction/initialize", json=payload, headers=headers)
        if response.status_code != 200:
            return Response({"error": "Failed to initiate payment"}, status=status.HTTP_400_BAD_REQUEST)

        resp_data = response.json()
        checkout_url = resp_data.get("data", {}).get("checkout_url")
        if not checkout_url:
            return Response({"error": "No checkout URL returned"}, status=status.HTTP_400_BAD_REQUEST)

        # Create a Payment record storing the tx_ref in transaction_id for later verification.
        payment = Payment.objects.create(
            booking=booking,
            transaction_id=tx_ref,
            amount=amount,
            status="pending"
        )

        return Response({
            "message": "Payment initiated",
            "payment_id": payment.id,
            "checkout_url": checkout_url,
            "tx_ref": tx_ref
        }, status=status.HTTP_200_OK)

class PaymentVerifyView(APIView):
    """
    Verify the payment status with Chapa.
    Expects callback data including 'tx_ref'.
    """

    def post(self, request):
        tx_ref = request.data.get("tx_ref")
        if not tx_ref:
            return Response({"error": "tx_ref is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Make a GET request to the Chapa verify endpoint using the tx_ref.
        chapa_secret_key = os.environ.get("CHAPA_SECRET_KEY")
        headers = {
            "Authorization": f"Bearer {chapa_secret_key}",
            "Content-Type": "application/json",
        }
        verify_url = f"https://api.chapa.co/v1/transaction/verify/{tx_ref}"
        response = requests.get(verify_url, headers=headers)
        if response.status_code != 200:
            return Response({"error": "Verification failed"}, status=status.HTTP_400_BAD_REQUEST)

        resp_data = response.json()
        status_from_api = resp_data.get("data", {}).get("status")
        # Set the new status based on the API response. In this sample, 'success' means the payment succeeded.
        new_status = "completed" if status_from_api == "success" else "failed"

        try:
            # Retrieve Payment record via the stored tx_ref (in transaction_id)
            payment = Payment.objects.get(transaction_id=tx_ref)
            payment.status = new_status
            payment.save()
        except Payment.DoesNotExist:
            return Response({"error": "Payment record not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "message": "Payment verified",
            "new_status": new_status,
            "tx_ref": tx_ref
        }, status=status.HTTP_200_OK)