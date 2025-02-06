from rest_framework import serializers
from .models import Listing, Booking
from .models import Payment

class ListingSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = [
            'property_id',
            'name',
            'description',
            'location',
            'price_per_night',
            'created_at',
            'updated_at',
            'average_rating',
        ]

    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews.exists():
            return round(sum(review.rating for review in reviews) / reviews.count(), 2)
        return None

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'