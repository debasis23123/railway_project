from django.shortcuts import render, redirect, get_object_or_404
from .models import Train, Booking, Passenger
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.core.mail import send_mail
from twilio.rest import Client
from django.conf import settings
from .utils import send_sms


def send_sms(phone, message):
    try:
        client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )

        # Format Indian number
        if not phone.startswith("+91"):
            phone = "+91" + phone

        message = client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone
        )

        print("✅ SMS SENT:", message.sid)

    except Exception as e:
        print("❌ SMS FAILED:", e)


#  Home Page
def home(request):
    trains = Train.objects.all()
    return render(request, 'home.html', {'trains': trains})


# Get available seats (IMPORTANT FIX)
def get_available_seats(train):
    booked = Passenger.objects.filter(
        booking__train=train,
        booking__status="CONFIRMED"
    ).count()

    return train.seats - booked


#  Seat Allocation Logic (FIXED)
def allocate_seat(train):
    booked = Passenger.objects.filter(
        booking__train=train,
        booking__status="CONFIRMED"
    ).count()

    if booked < train.seats:
        return f"S{booked + 1}"
    return None  # Waiting


#  Book Ticket
@login_required
def book_ticket(request):
    if request.method == 'POST':

        train_id = request.POST.get('train')
        date = request.POST.get('date')
        count = int(request.POST.get('count'))
        phone = request.POST.get('phone')

        train = get_object_or_404(Train, id=train_id)

        # ✅ Check availability correctly
        available = get_available_seats(train)
        if count > available:
            return HttpResponse("❌ Not enough seats available")

        # ✅ Create booking (temporary status)
        booking = Booking.objects.create(
            user=request.user,
            train=train,
            date=date,
            seats_booked=count,
            status="PENDING",
            phone=phone
        )

        final_status = "CONFIRMED"

        # ✅ Create passengers
        for i in range(1, count + 1):
            seat = allocate_seat(train)

            if not seat:
                final_status = "WAITING"

            Passenger.objects.create(
                booking=booking,
                name=request.POST.get(f'name{i}'),
                age=request.POST.get(f'age{i}'),
                gender=request.POST.get(f'gender{i}'),
                seat_number=seat if seat else "WL"
            )

        # ✅ Update final booking status
        booking.status = final_status
        booking.save()

        messages.success(request, "Proceed to payment 💳")

        return redirect('payment', booking_id=booking.id)

    trains = Train.objects.all()
    return render(request, 'book.html', {'trains': trains})


#  Dashboard
@login_required
def dashboard(request):
    total_trains = Train.objects.count()
    total_bookings = Booking.objects.count()
    confirmed = Booking.objects.filter(status="CONFIRMED").count()
    waiting = Booking.objects.filter(status="WAITING").count()

    user_bookings = Booking.objects.filter(user=request.user)

    return render(request, 'dashboard.html', {
        'trains': total_trains,
        'bookings': total_bookings,
        'confirmed': confirmed,
        'waiting': waiting,
        'user_bookings': user_bookings
    })


#  Booking List
@login_required
def booking_list(request):
    bookings = Booking.objects.select_related('train')
    return render(request, 'booking_list.html', {'bookings': bookings})


# ❌ Cancel Booking (FIXED + SECURE)
@login_required
def cancel_booking(request, id):
    booking = get_object_or_404(Booking, id=id, user=request.user)

    booking.status = "CANCELLED"
    booking.save()

    messages.success(request, "❌ Booking Cancelled Successfully")

    return redirect('booking_list')


# PNR Status
def pnr_status(request):
    booking = None

    if request.method == 'POST':
        pnr = request.POST.get('pnr')
        booking = Booking.objects.filter(pnr=pnr).first()

        if not booking:
            return HttpResponse("❌ Invalid PNR")

    return render(request, 'pnr.html', {'booking': booking})


#  Register
def register(request):
    if request.method == 'POST':
        User.objects.create_user(
            username=request.POST['username'],
            password=request.POST['password']
        )
        return redirect('login')

    return render(request, 'register.html')


# Login
def user_login(request):
    if request.method == 'POST':
        user = authenticate(
            username=request.POST['username'],
            password=request.POST['password']
        )

        if user:
            login(request, user)
            return redirect('home')
        else:
            return HttpResponse("Invalid login ❌")

    return render(request, 'login.html')


# 🚪 Logout
def user_logout(request):
    logout(request)
    return redirect('login')



@login_required
def download_ticket(request, id):
    booking = get_object_or_404(Booking, id=id, user=request.user)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="ticket.pdf"'

    p = canvas.Canvas(response)

    p.drawString(100, 800, "🚆 IRCTC Ticket")
    p.drawString(100, 770, f"PNR: {booking.pnr}")
    p.drawString(100, 740, f"Train: {booking.train.name}")
    p.drawString(100, 710, f"Date: {booking.date}")
    p.drawString(100, 680, f"Status: {booking.status}")
    p.drawString(100, 650, f"Phone: {booking.phone}")

    y = 620
    for passenger in booking.passengers.all():
        p.drawString(
            100, y,
            f"{passenger.name} | Age: {passenger.age} | Seat: {passenger.seat_number}"
        )
        y -= 20

    p.save()
    return response

@login_required
def payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if request.method == "POST":

        # ✅ Allocate seats AFTER payment
        final_status = "CONFIRMED"

        for passenger in booking.passengers.all():
            seat = allocate_seat(booking.train)

            if not seat:
                final_status = "WAITING"
                passenger.seat_number = "WL"
            else:
                passenger.seat_number = seat

            passenger.save()

        booking.status = final_status
        booking.save()

        # 📧 EMAIL (console)
        send_mail(
            subject="🎫 Ticket Confirmed",
            message=f"PNR: {booking.pnr}\nTrain: {booking.train.name}\nStatus: {booking.status}",
            from_email="noreply@railway.com",
            recipient_list=["test@gmail.com"],  # change later
            fail_silently=True,
        )

        # 📱 SMS
        send_sms(
            booking.phone,
            f"Ticket Confirmed! PNR: {booking.pnr}, Train: {booking.train.name}"
        )

        return redirect('payment_success', booking_id=booking.id)

    return render(request, 'payment.html', {'booking': booking})

@login_required
def payment_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    return render(request, 'payment_success.html', {'booking': booking})

def send_all_booking_sms():
    bookings = Booking.objects.exclude(phone__isnull=True).exclude(phone__exact='')

    for booking in bookings:
        message = f"Hello {booking.user.username}, Your PNR {booking.pnr} is {booking.status}"
        send_sms(booking.phone, message)

    print("All SMS sent successfully ✅")