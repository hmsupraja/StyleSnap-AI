import streamlit as st
from twilio.rest import Client

client = Client(
    st.secrets["TWILIO_ACCOUNT_SID"],
    st.secrets["TWILIO_AUTH_TOKEN"]
)

try:
    response = client.request(
        "GET",
        "https://content.twilio.com/v1/Content"
    )

    print(response.text)

except Exception as error:
    print("Error:", error)