
import streamlit as st
from twilio.rest import Client

client = Client(
    st.secrets["TWILIO_ACCOUNT_SID"],
    st.secrets["TWILIO_AUTH_TOKEN"],
)

to_number = input("Enter your joined WhatsApp number (+country code): ").strip()

try:
    message = client.messages.create(
        from_=st.secrets["TWILIO_WHATSAPP_FROM"],
        to=f"whatsapp:{to_number}",
        content_sid="HX_REPLACE_WITH_REAL_TEMPLATE_SID",
        content_variables='{"1":"shoes","2":"1 pair","3":"tomorrow","4":"StyleSnap AI"}',
    )

    print("Message SID:", message.sid)
    print("Status:", message.status)

except Exception as error:
    print("Twilio error:", error)
