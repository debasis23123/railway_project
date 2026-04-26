from twilio.rest import Client
from django.conf import settings

def send_sms(phone, message):
    try:
        client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )

        if not phone.startswith("+91"):
            phone = "+91" + phone

        msg = client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone
        )

        print("SMS SENT:", msg.sid)

    except Exception as e:
        print("SMS FAILED:", e)