from flask import render_template
from . import services_bp

SERVICES_CATALOG = [
    {
        "id": "srv_erp",
        "title": "Custom ERP & CRM Architecture",
        "category": "Enterprise Systems",
        "description": "Tailored enterprise resource management software built with Python Flask backends and PostgreSQL databases.",
        "icon": "fa-network-wired",
        "features": ["Role-based access", "Automated invoicing", "Audit logging", "Inventory sync"],
        "price": "Custom Quote"
    },
    {
        "id": "srv_whatsapp",
        "title": "WhatsApp Cloud API & Chatbot Automation",
        "category": "Conversational AI",
        "description": "24/7 automated lead capture, customer support bots, and catalog distribution integrated with Meta Cloud API.",
        "icon": "fa-brands fa-whatsapp",
        "features": ["Webhook handlers", "Media catalog sending", "CRM sync", "Human handoff"],
        "price": "$199 / Setup"
    },
    {
        "id": "srv_sheets",
        "title": "Google Sheets & Apps Script Automation",
        "category": "Workflow Optimization",
        "description": "Transform messy manual spreadsheets into automated business dashboards, PDF dispatchers, and external DB syncs.",
        "icon": "fa-table",
        "features": ["Custom macro scripting", "Email/Drive integrations", "Triggered webhook alerts", "Speed optimization"],
        "price": "$99 / Script"
    }
]

@services_bp.route("/services")
def list_services():
    return render_template("services/services.html", services=SERVICES_CATALOG)