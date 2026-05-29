from django.shortcuts import render, redirect, get_object_or_404
from .models import Train, Booking, Passenger
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from io import BytesIO
from django.core.mail import EmailMessage
import qrcode
from reportlab.lib.utils import ImageReader
from django.core.mail import send_mail
from django.utils.timezone import now


#-------- HOME ----------------
def home(request):
    trains = Train.objects.all()
    return render(request, 'home.html', {'trains': trains})


# ---------------- SEAT LOGIC ----------------
def get_available_seats(train, date):
    booked = Passenger.objects.filter(
        booking__train=train,
        booking__date=date,
        booking__status="CONFIRMED"
    ).count()

    return train.seats - booked


def allocate_seat_and_coach(train, date):
    booked = Passenger.objects.filter(
        booking__train=train,
        booking__date=date,
        booking__status="CONFIRMED"
    ).count()

    seat_no = booked + 1

    coach_number = (seat_no - 1) // 72 + 1
    seat_in_coach = (seat_no - 1) % 72 + 1

    coach = f"S{coach_number}"

    return coach, str(seat_in_coach)

# ---------------- BOOK TICKET ----------------
@login_required
def book_ticket(request):
    if request.method == 'POST':

        train_id = request.POST.get('train')
        date = request.POST.get('date')
        count = int(request.POST.get('count'))
        phone = request.POST.get('phone')
        email = request.POST.get('email')

        train = get_object_or_404(Train, id=train_id)

        available = get_available_seats(train, date)
        if count > available:
            return HttpResponse("Not enough seats available")
        total_price = train.distance * train.price_per_km * count

        # Create booking (NO seat allocation here)
        booking = Booking.objects.create(
            user=request.user,
            train=train,
            date=date,
            seats_booked=count,
            status="PENDING",
            phone=phone,
            email=email,
            total_price=total_price,
        )

        # Create passengers (NO seats yet)
        for i in range(1, count + 1):
            Passenger.objects.create(
                booking=booking,
                name=request.POST.get(f'name{i}'),
                age=request.POST.get(f'age{i}'),
                gender=request.POST.get(f'gender{i}'),
                seat_number="PENDING"

           )
        if booking.status == "CONFIRMED":
            message = "Your ticket is CONFIRMED."
        elif booking.status == "PENDING":
            message = "Your ticket is WAITING. Proceed to payment."
        else:
            message = "Your booking status updated."

        send_mail(
            "Booking Status",
            message,
            "debasissamal433@gmail.com",
            [booking.email],  # better than request.user.email
        )



        messages.success(request, "Proceed to payment ")
        return redirect('payment', booking_id=booking.id)

    trains = Train.objects.all()
    return render(request, 'book.html', {'trains': trains})


# ---------------- PAYMENT ----------------
@login_required
def payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if request.method == "POST":

        with transaction.atomic():

            final_status = "CONFIRMED"

            for passenger in booking.passengers.all():
                coach, seat = allocate_seat_and_coach(booking.train, booking.date)

                if not seat:
                    final_status = "WAITING"
                    passenger.seat_number = "WL"
                else:
                    passenger.seat_number = seat
                    passenger.coach= coach


                passenger.save()

            booking.status = final_status
            booking.save()

        # -------- PDF GENERATION --------
        buffer = BytesIO()
        p = canvas.Canvas(buffer)

        p.drawString(100, 800, "IRCTC Ticket")
        p.drawString(100, 770, f"PNR: {booking.pnr}")
        p.drawString(100, 740, f"Train: {booking.train.name}")
        p.drawString(100, 710, f"Date: {booking.date}")
        p.drawString(100, 680, f"Status: {booking.status}")
        p.drawString(100, 650, f"Total Fare: ₹{booking.total_price}")



        y = 650
        for passenger in booking.passengers.all():
            p.drawString(
                100, y,
                f"{passenger.name} | Age: {passenger.age} | Seat: {passenger.seat_number}|coach:{passenger.coach}"
            )
            y -= 20

        # -------- QR CODE --------
        qr_data = f"""
        PNR: {booking.pnr}
        Train: {booking.train.name}
        Date: {booking.date}
        Status: {booking.status}
        """

        qr = qrcode.make(qr_data)

        qr_buffer = BytesIO()
        qr.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)

        qr_image = ImageReader(qr_buffer)
        p.drawImage(qr_image, 400, 650, width=120, height=120)

        p.save()
        buffer.seek(0)

        # -------- EMAIL --------
        try:
            email = EmailMessage(
                subject="Your Train Ticket",
                body=f"Hello {booking.user.username},\n\nYour ticket is attached.\nPNR: {booking.pnr}",
                from_email="yourgmail@gmail.com",
                to=[booking.email],
            )

            email.attach(
                f"ticket_{booking.pnr}.pdf",
                buffer.read(),
                "application/pdf"
            )

            email.send(fail_silently=False)
            print(" Email sent successfully")

        except Exception as e:
            print(" Email failed:", e)

        return redirect('payment_success', booking_id=booking.id)

    return render(request, 'payment.html', {'booking': booking})




# ---------------- DASHBOARD ----------------
@login_required
def dashboard(request):
    today = now().date()

    bookings_today = Booking.objects.filter(date__gte=today)

    return render(request, 'dashboard.html', {
        'trains': Train.objects.count(),
        'bookings': bookings_today.count(),
        'confirmed': bookings_today.filter(status="CONFIRMED").count(),
        'waiting': bookings_today.filter(status="WAITING").count(),
        'user_bookings': bookings_today.filter(user=request.user)
    })


# ---------------- CANCEL ----------------
@login_required
def cancel_booking(request, id):
    booking = get_object_or_404(Booking, id=id, user=request.user)

    booking.status = "CANCELLED"
    booking.save()

    messages.success(request, " Booking Cancelled")
    return redirect('booking_list')


# ---------------- AUTH ----------------
def register(request):
    if request.method == 'POST':

        if User.objects.filter(username=request.POST['username']).exists():
            return HttpResponse("User already exists ")

        User.objects.create_user(
            username=request.POST['username'],
            password=request.POST['password']
        )
        return redirect('login')

    return render(request, 'register.html')


def user_login(request):
    if request.method == 'POST':
        user = authenticate(
            username=request.POST['username'],
            password=request.POST['password']
        )

        if user:
            login(request, user)
            return redirect('home')

        return HttpResponse("Invalid login ")

    return render(request, 'login.html')


def user_logout(request):
    logout(request)
    return redirect('login')


@login_required
def booking_list(request):
    bookings = Booking.objects.filter(user=request.user).select_related('train')
    return render(request, 'booking_list.html', {'bookings': bookings})

def pnr_status(request):
    booking = None

    if request.method == 'POST':
        pnr = request.POST.get('pnr')
        booking = Booking.objects.filter(pnr=pnr).first()

        if not booking:
            return HttpResponse("Invalid PNR")

    return render(request, 'pnr.html', {'booking': booking})

@login_required
def download_ticket(request, id):
    booking = get_object_or_404(Booking, id=id, user=request.user)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="ticket_{booking.pnr}.pdf"'

    p = canvas.Canvas(response)

    p.drawString(100, 800, "IRCTC Ticket")
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
def payment_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    return render(request, 'payment_success.html', {'booking': booking})

def success(request):
    return render(request, "success.html")