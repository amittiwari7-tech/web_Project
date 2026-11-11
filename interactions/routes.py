from flask import render_template, request, flash, redirect, url_for
from . import interactions_bp
from core.sheets_service import post_to_sheets

@interactions_bp.route("/custom-order", methods=["GET", "POST"])
def custom_order():
    if request.method == "POST":
        payload = {
            "name": request.form.get("name"),
            "email": request.form.get("email"),
            "service_type": request.form.get("service_type"),
            "phone": request.form.get("phone"),
            "budget": request.form.get("budget"),
            "description": request.form.get("description"),
            "action": 'add_inquiry'
        }
        success = post_to_sheets("add_inquiry", payload)
        if success:
            flash("Your custom requirement has been dispatched! Our team will contact you within 24 hours.", "success")
        else:
            flash("Inquiry queued. We will reach out shortly.", "info")
        return redirect(url_for("interactions.custom_order"))
        
    return render_template("interactions/custom_order.html")

@interactions_bp.route("/feedback", methods=["GET", "POST"])
def feedback():
    if request.method == "POST":
        payload = {
            "name": request.form.get("name"),
            "rating": request.form.get("rating"),
            "message": request.form.get("message"),
            "email": request.form.get("email"),
            "action": 'add_feedback'
        }
        success = post_to_sheets("add_feedback", payload)
        if success:
            flash("Thank you for your valuable feedback!", "success")
        else:
            flash("Feedback recorded. Thank you!", "info")
        return redirect(url_for("interactions.feedback"))
        
    return render_template("interactions/feedback.html")