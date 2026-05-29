from django.db import models
from django.contrib.auth.models import User
import uuid


# 🚆 Train Model
class Train(models.Model):
    name = models.CharField(max_length=100)
    source = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    seats = models.IntegerField()
    distance = models.IntegerField(default=1000)
    price_per_km= models.FloatField(default=2.0)

    def __str__(self):
        return self.name


# 🎟️ Booking Model
class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    train = models.ForeignKey(Train, on_delete=models.CASCADE)
    date = models.DateField()
    seats_booked = models.IntegerField()
    status = models.CharField(max_length=20, default='CONFIRMED')
    phone = models.CharField(max_length=15)
    email = models.EmailField(null=True, blank=True)
    total_price = models.FloatField(default=0)

    pnr = models.CharField(max_length=12, unique=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.pnr:
            self.pnr = str(uuid.uuid4()).replace("-", "")[:10].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.pnr


# 👤 Passenger Model (MULTIPLE per booking)
class Passenger(models.Model):
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="passengers"
    )
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    gender = models.CharField(max_length=10)
    seat_number = models.CharField(max_length=100, null=True, blank=True)
    coach= models.CharField(max_length=10,default='')

    def __str__(self):
        return self.name

