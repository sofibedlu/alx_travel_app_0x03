from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from listings.models import Booking

@shared_task
def send_booking_confirmation_email(booking_id):
    try:
        booking = Booking.objects.get(booking_id=booking_id)
        subject = 'Booking Confirmation'
        message = f'Your booking for {booking.listing.name} has been confirmed.'
        recipient_list = [booking.user.email]
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
        return "Email sent successfully"
    except Booking.DoesNotExist:
        return "Booking not found."