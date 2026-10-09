# StyleSnap AI

StyleSnap AI is a Streamlit-based AI vision and chat app for outfit ideas, color matching, and styling suggestions. It uses Google Gemini for text and image understanding and Twilio WhatsApp to send a conversation summary.

## Requirements
- Python 3.11 or 3.12 recommended
- Gemini API key from https://aistudio.google.com/
- Twilio account and WhatsApp Sandbox access for WhatsApp messaging

## Windows / VS Code setup
Open this folder in VS Code, then use Terminal > New Terminal:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .streamlit\secrets.toml.example .streamlit\secrets.toml
```

Add your real Gemini key to `.streamlit/secrets.toml`. Start with:

```powershell
streamlit run app.py
```

Open the local URL shown by Streamlit, usually http://localhost:8501.

If PowerShell blocks activation, run:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

You can avoid activation and run the virtual environment directly:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\streamlit.exe run app.py
```

## Gemini model
The starter uses `gemini-3.5-flash` to follow the supplied workshop guide. If the API says this model is unavailable, check Google's current model list and change `MODEL_NAME` in `app.py` to a supported model.

## WhatsApp configuration
1. In Twilio Console, open Messaging > Try it out > Send a WhatsApp message.
2. Join the Sandbox from the phone you will test with using the displayed join code.
3. In Messaging > Content Template Builder, create a WhatsApp text template with two variables: `{{1}}` for name and `{{2}}` for the summary.
4. Add the resulting Content SID (starts with HX), Account SID, and Auth Token to `.streamlit/secrets.toml`.
5. Keep `TWILIO_WHATSAPP_FROM` as `whatsapp:+14155238886` for the standard sandbox unless Twilio shows you a different sender.

WhatsApp template approval, sandbox membership, and account permissions depend on Twilio/WhatsApp settings.

## Deploy on Streamlit Community Cloud
1. Push files to GitHub; do not commit `.streamlit/secrets.toml`.
2. Create an app at https://share.streamlit.io/ and choose `app.py`.
3. Add the same credentials under the app's Settings > Secrets.
4. Deploy and test image upload and WhatsApp messaging.

## Test checklist
- [ ] Onboarding accepts a name and valid international phone number.
- [ ] Text styling questions receive responses.
- [ ] JPG, PNG, or WEBP outfit photos receive styling suggestions.
- [ ] Follow-up questions retain context.
- [ ] WhatsApp summary arrives after Twilio setup.
- [ ] Secrets are not committed to Git.
