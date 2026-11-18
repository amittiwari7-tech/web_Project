import os
import re
import uuid
import requests
import traceback
import urllib.parse
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


@recharge_bp.route('/create-cashfree-order/<string:type>', methods=['POST'])
def create_cashfree_order(type):
    try:
        if not session.get('status'):
            return jsonify({
                "status": "error", 
                "message": "Session expired or user not logged in."
            }), 401

        data = request.get_json(silent=True) or {}
        print(f"Received data for Cashfree order creation: {data}")

        # 1. Sabse pehle tagName yahan define karein taaki error na aaye
        tagName = str(data.get('tag_name') or "").strip()
        safe_tag_name = urllib.parse.quote(tagName)
        safe_product_Id = urllib.parse.quote(str(data.get('product_id') or 'N/A').strip())

        # 2. Sanitize & parse Amount
        raw_amount = data.get('amount', 199)
        if isinstance(raw_amount, str):
            raw_amount = re.sub(r'[^\d.]', '', raw_amount)
        try:
            order_amount = round(float(raw_amount), 2)
            if order_amount <= 0:
                order_amount = 1.00
        except (ValueError, TypeError):
            order_amount = 199.00

        product_name = str(data.get('product_name') or 'Tech Gyan Amit Digital License')[:40]
        order_id = f"ORDER_{uuid.uuid4().hex[:10].upper()}"
        
        # Safe duration parsing supporting string or number
        try:
            recharge_Duration = int(float(data.get('recharge_Duration', 1)))
        except (ValueError, TypeError):
            recharge_Duration = 1

        # 3. Format customer details
        customer_id = session.get('user_id') or 7217
        customer_name = str(session.get('user_name') or 'Developer')[:50]
        customer_email = str(session.get('email') or 'developer@nexus.local').strip()
        if '@' not in customer_email:
            customer_email = "developer@nexus.local"

        # 4. Clean 10-digit phone
        raw_phone = str(session.get('phone') or data.get('phone') or '9999999999')
        digits = re.sub(r'\D', '', raw_phone)
        customer_phone = digits[-10:] if len(digits) >= 10 else "9999999999"

        # 5. Callback URL (Encoded safe_tag_name ke sath)
        try:
            return_url = f"{request.host_url.rstrip('/')}{url_for('recharge.payment_callback')}?order_id={order_id}&type={type}&duration={recharge_Duration}&tag_name={safe_tag_name}&product_id={safe_product_Id}"
        except Exception:
            return_url = f"{request.host_url.rstrip('/')}/recharge/payment-callback?order_id={order_id}&type={type}&duration={recharge_Duration}&tag_name={safe_tag_name}&product_id={safe_product_Id}"

        # 6. Build Cashfree Headers & Payload
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
            "order_Type": type,
            "duration_month": recharge_Duration,
            "customer_details": {
                "customer_id": customer_id,
                "customer_name": customer_name,
                "customer_email": customer_email,
                "customer_phone": customer_phone
            },
            "order_meta": {
                "return_url": return_url
            },
            "order_note": f"{product_name}"[:40],
            "tag_name": tagName,
            "product_Id": safe_product_Id
        }
        
        print("Payload for Cashfree Order Creation:", payload)

        # 7. Execute API request
        response = requests.post(CASHFREE_BASE_URL, json=payload, headers=headers, timeout=12)
        
        if not response.text or response.text.strip() == "":
            return jsonify({
                "status": "error",
                "message": f"Payment Gateway returned an empty response (Status: {response.status_code})"
            }), 400

        try:
            res_data = response.json()
        except Exception as json_err:
            return jsonify({
                "status": "error",
                "message": "Invalid response received from Payment Gateway."
            }), 500

        if response.status_code == 200 and isinstance(res_data, dict) and "payment_session_id" in res_data:
            return jsonify({
                "status": "success",
                "payment_session_id": res_data["payment_session_id"],
                "order_id": order_id,
                "order_Type": type,
                "tag_name": tagName
            })
        else:
            err_msg = "Payment session creation failed."
            if isinstance(res_data, dict):
                err_msg = res_data.get("message") or res_data.get("sub_code") or err_msg
            
            return jsonify({
                "status": "error",
                "message": err_msg
            }), 400

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "status": "error", 
            "message": f"Server Error: {str(e)}"
        }), 500


@recharge_bp.route('/payment-callback', methods=['GET'])
def payment_callback():
    order_id = request.args.get('order_id', 'UNKNOWN')
    order_type = request.args.get('type', 'Productrecharge')
    duration = request.args.get('duration', 1)
    tag_name = request.args.get('tag_name', '')

    headers = {
        "accept": "application/json",
        "x-api-version": "2023-08-01",
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET_KEY
    }

    verified_data = {}

    try:
        # Cashfree se order ka status check karne ki request (Verify Order Status)
        status_url = f"{CASHFREE_BASE_URL.rstrip('/')}/{order_id}"
        response = requests.get(status_url, headers=headers, timeout=10)

        if response.status_code == 200:
            res_json = response.json()
            order_status = res_json.get("order_status")
           
            # Check karein ki payment 100% successful hui hai ya nahi
            if order_status == "PAID":
                res_json["order_Type"] = order_type
                res_json["recharge_duration"] = duration
                res_json["tag_name"] = tag_name
                res_json["product_Id"] = request.args.get('product_id', 'N/A')
                
                # 🟢 Sirf SUCCESS / PAID hone par hi Google Sheet par data save hoga!
                post_to_sheets('appSubscription', res_json)
                verified_data = res_json
            else:
                print(f"Order {order_id} status is {order_status}, not saved to sheet.")
    except Exception as err:
        print(f"Error verifying payment status for {order_id}: {err}")

    return render_template('recharge/success.html', order_id=order_id)


@recharge_bp.route('/activate-trial/<string:type>', methods=['POST'])
def activate_trial(type):
    if not session.get('status'):
        return jsonify({"status": "error", "message": "User not authenticated. Please log in first."}), 401

    data = request.get_json(silent=True) or {}
    product_name = str(data.get('product_name') or 'Tech Gyan Amit Digital License')
    tagName = str(data.get('tag_name') or 'trial')

    customer_id = str(session.get('user_id') or '7217')
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
        'Order Note': f"{product_name}",
        "order_Type": type,
        "tag_name": tagName,
        "product_Id":data.get('product_id', 'N/A'),
    }
    
    print(trial_data)
    success, message = post_to_sheets('trial', {
        'username': trial_data
    })
    
    print(f"Trial registration response from Google Sheets: {success}, {message}")

    # Agar Google sheet se success True aaya hai, tabhi 'success' bhejein, warna 'error'
    status_str = "success" if success else "error"

    return jsonify({
        "status": status_str,
        "message": message,  # Yahan Google Sheet ka actual message (jaise "Data Already Exist...") jayega
        "order_id": order_id,
        "sheets_result": {
            "success": success,
            "message": message
        }
    })