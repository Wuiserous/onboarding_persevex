import razorpay
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

# Load .env file into environment
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # This will allow cross-origin requests

# 1. Initialize Razorpay client with your credentials
try:
    client = razorpay.Client(auth=(os.getenv('RAZORPAY_KEY_ID'), os.getenv('RAZORPAY_SECRET')))
except Exception as e:
    print(f"Error initializing Razorpay client: {e}")
    client = None

# 2. (Optional) Identify your app
if client:
    client.set_app_details({"title": "MyApp", "version": "1.0.0"})


def create_payment_link(name, email, contact, amount_rupees,
                        description=None, reference_id=None,
                        expire_by_unix=None, callback_url=None):
    if not client:
        raise Exception("Razorpay client not initialized. Check your environment variables.")

    payload = {
        "amount": int(amount_rupees * 100),  # amount in paise
        "currency": "INR",
        "accept_partial": False,
        "description": description or "Payment",
        "customer": {
            "name": name,
            "email": email,
            "contact": contact
        },
        "notify": {"email": True, "sms": False},
        "reminder_enable": True
    }

    if reference_id:
        payload["reference_id"] = reference_id

    if expire_by_unix:
        payload["expire_by"] = expire_by_unix

    if callback_url:
        payload["callback_url"] = callback_url
        payload["callback_method"] = "get"

    link = client.payment_link.create(payload)
    return link["short_url"], link["id"]


@app.route('/create-payment-link', methods=['POST'])
def handle_create_payment_link():
    data = request.get_json()

    # --- Data Validation ---
    required_fields = ['name', 'email', 'contact', 'amount', 'reference_id']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        url, link_id = create_payment_link(
            name=data['name'],
            email=data['email'],
            contact=data['contact'],
            amount_rupees=float(data['amount']),
            description="Registration Fee",
            reference_id=data['reference_id']
            # You can add callback_url here if needed
            # callback_url="YOUR_CALLBACK_URL"
        )
        return jsonify({"payment_link": url})

    except Exception as e:
        print(f"Error creating payment link: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Use 0.0.0.0 to be accessible on your network
    # Railway will use its own port, but this is good for local testing
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))