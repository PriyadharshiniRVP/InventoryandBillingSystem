import urllib.parse
from django import template

register = template.Library()

@register.filter
def get_bill_message(bill):
    # Build bill details text for WhatsApp
    lines = [f"Best Chennai Interiors - Bill #{bill.id}"]
    lines.append(f"Customer: {bill.customer_name}")
    lines.append(f"Mobile: {bill.customer_mobile}")
    lines.append(f"Date: {bill.created_at.strftime('%d-%b-%Y %I:%M%p')}")
    lines.append("Items:")
    for item in bill.items.all():
        lines.append(f"- {item.product.name}: {item.quantity} x {item.price} = {item.get_cost()}")
    lines.append(f"Total: Rs. {bill.total_amount}")
    # Also show managers, one per line
    lines.append("Managers:")
    for manager in split_managers_filter(bill.project_manager):
        lines.append(f"  • {manager}")
    lines.append("Thank you for choosing Best Interiors!")
    message = "\n".join(lines)
    return urllib.parse.quote(message)

# Split managers for use in templates
@register.filter
def split_managers(manager_string):
    # Returns a list of names, stripped
    return [m.strip() for m in manager_string.split(",") if m.strip()]

# This function allows the filter to be used in Python code too:
def split_managers_filter(manager_string):
    return [m.strip() for m in manager_string.split(",") if m.strip()]
