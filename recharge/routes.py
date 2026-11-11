import os
import re
import uuid
import requests
import traceback
from flask import request, jsonify, render_template, session, url_for
from . import recharge_bp
from core.sheets_service import post_to_sheets

# Cashfree Sandbox / Production Credentials
CASHFREE_APP_ID = os.environ.get("CASHFREE_APP_ID", "").strip()
CASHFREE_SECRET_KEY = os.environ.get("CASHFREE_SECRET_KEY", "").strip()
CASHFREE_BASE_URL = os.environ.get(
    "CASHFREE_BASE_URL", 
    "https://sandbox.cashfree.com/pg/orders"
).strip()


@recharge_bp.route('/create-cashfree-order', methods=['POST'])
def create_cashfree_order():
    try:
        if not session.get('status'):
            return jsonify({
                "status": "error", 
                "message": "Session expired or user not logged in."
            }), 401

        data = request.get_json(silent=True) or {}

        # 1. Sanitize & parse Amount
        raw_amount = data.get('amount', 199)
        if isinstance(raw_amount, str):
            raw_amount = re.sub(r'[^\d.]', '', raw_amount)
        try:
            order_amount = round(float(raw_amount), 2)
            if order_amount <= 0:
                order_amount = 1.00
        except (ValueError, TypeError):
            order_amount = 199.00

        product_name = str(data.get('product_name') or 'NEXUS Digital License')[:40]
        order_id = f"ORDER_{uuid.uuid4().hex[:10].upper()}"

        # 2. Format customer details
        raw_uid = session.get('user_id') or session.get('user_name') or '7217'
        customer_id = f"CUST_{re.sub(r'[^a-zA-Z0-9_-]', '_', str(raw_uid))}"[:50]
        customer_name = str(session.get('user_name') or 'Developer')[:50]

        customer_email = str(session.get('email') or 'developer@nexus.local').strip()
        if '@' not in customer_email:
            customer_email = "developer@nexus.local"

        # 3. Clean 10-digit phone
        raw_phone = str(session.get('phone') or data.get('phone') or '9999999999')
        digits = re.sub(r'\D', '', raw_phone)
        customer_phone = digits[-10:] if len(digits) >= 10 else "9999999999"

        # 4. Callback URL (Fixed f-string interpolation)
        try:
            return_url = f"{request.host_url.rstrip('/')}{url_for('recharge.payment_callback')}?order_id={order_id}"
        except Exception:
            return_url = f"{request.host_url.rstrip('/')}/recharge/payment-callback?order_id={order_id}"

        # 5. Build Cashfree Headers & Payload
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-api-version": "2023-08-01",
            "x-client-id": CASHFREE_APP_ID,
            "x-client-secret": CASHFREE_SECRET_KEY
        }

        payload = {
            "order_id": order_id,
            "order_amount": order_amount,
            "order_currency": "INR",
            "customer_details": {
                "customer_id": customer_id,
                "customer_name": customer_name,
                "customer_email": customer_email,
                "customer_phone": customer_phone
            },
            "order_meta": {
                "return_url": return_url
            },
            "order_note": f"Payment for {product_name}"[:40]
        }

        # 6. Execute API request
        response = requests.post(CASHFREE_BASE_URL, json=payload, headers=headers, timeout=12)
        print(response.status_code, response.text, response)  # Debugging output
        res_data = response.json()
        post_to_sheets('appSubscription', res_data)

        if response.status_code == 200 and "payment_session_id" in res_data:
            return jsonify({
                "status": "success",
                "payment_session_id": res_data["payment_session_id"],
                "order_id": order_id
            })
        else:
            print("\n" + "="*50)
            print(f"[CASHFREE REJECTED {response.status_code}]: {res_data}")
            print(f"Payload sent: {payload}")
            print("="*50 + "\n")
            
            err_msg = res_data.get("message") or res_data.get("sub_code") or "Payment session creation failed."
            return jsonify({
                "status": "error",
                "message": err_msg
            }), 400

    except Exception as e:
        print("\n" + "!"*50)
        print("[CRITICAL EXCEPTION IN create_cashfree_order]:")
        traceback.print_exc()
        print("!"*50 + "\n")
        return jsonify({
            "status": "error", 
            "message": f"Server Error: {str(e)}"
        }), 500


@recharge_bp.route('/payment-callback', methods=['GET'])
def payment_callback():
    order_id = request.args.get('order_id', 'UNKNOWN')
    return render_template('recharge/success.html', order_id=order_id)


@recharge_bp.route('/activate-trial', methods=['POST'])
def activate_trial():
    if not session.get('status'):
        return jsonify({"status": "error", "message": "User not authenticated. Please log in first."}), 401

    data = request.get_json(silent=True) or {}
    product_name = str(data.get('product_name') or 'NEXUS Digital License')

    customer_id = str(session.get('user_id') or session.get('user_name') or '7217')
    customer_name = str(session.get('user_name') or 'Developer')
    customer_email = str(session.get('email') or 'developer@nexus.local')
    customer_phone = str(session.get('phone') or '9999999999')

    order_id = f"TRIAL_{uuid.uuid4().hex[:10].upper()}"

    trial_data = {
        'Order Id': order_id,
        'Cashfree Order Id': 'TRIAL_NO_PG',
        'Customer Id': customer_id,
        'Customer Name': customer_name,
        'Email': customer_email,
        'Phone': customer_phone,
        'Amount': '0',
        'Currency': 'INR',
        'Order Status': 'trial',
        'Created At': '',
        'Order Note': f"3-Day Evaluation for {product_name}"
    }
    
    print(trial_data)

    sheets_response = post_to_sheets('trial', {
        'username': trial_data
    })

    return jsonify({
        "status": "success",
        "message": "Trial registered successfully",
        "order_id": order_id,
        "sheets_result": sheets_response
    })