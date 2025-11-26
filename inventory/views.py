from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import HTML
import os
import csv

from .models import Product, Bill, BillItem, Supplier


# ------------------- Dashboard -------------------
def dashboard(request):
    products = Product.objects.all()
    bills = Bill.objects.all().order_by('-created_at')

    # Add Product
    if request.method == "POST" and 'product_submit' in request.POST:
        name = request.POST.get('name')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        if name and price and stock:
            Product.objects.create(name=name, price=price, stock=stock)
            messages.success(request, 'Product added.')
            return redirect('dashboard')

    # Edit Product
    if request.method == "POST" and 'edit_submit' in request.POST:
        pk = request.POST.get('edit_product_id')
        product = Product.objects.get(pk=pk)
        product.name = request.POST.get('edit_name')
        product.price = request.POST.get('edit_price')
        product.stock = request.POST.get('edit_stock')
        product.save()
        messages.success(request, 'Product updated.')
        return redirect('dashboard')

    # Delete Product
    if request.method == "POST" and 'delete_submit' in request.POST:
        pk = request.POST.get('delete_product_id')
        product = Product.objects.get(pk=pk)
        product.delete()
        messages.success(request, 'Product deleted.')
        return redirect('dashboard')

    # Billing
    if request.method == "POST" and 'billing_submit' in request.POST:
        product_ids = request.POST.getlist('product')
        quantities = request.POST.getlist('quantity')
        customer_name = request.POST.get('customer_name')
        customer_mobile = request.POST.get('customer_mobile')
        customer_address = request.POST.get('customer_address')
        project_manager = request.POST.get('project_manager')

        total_amount = 0
        bill = Bill.objects.create(
            total_amount=0,
            customer_name=customer_name,
            customer_mobile=customer_mobile,
            customer_address=customer_address,
            project_manager=project_manager,
        )

        for prod_id, qty in zip(product_ids, quantities):
            product = Product.objects.get(pk=prod_id)
            qty = int(qty)

            if product.stock < qty:
                bill.delete()
                messages.error(request, f'Insufficient stock for {product.name}.')
                return redirect('dashboard')

            price = product.price
            total_amount += price * qty
            product.stock -= qty
            product.save()

            BillItem.objects.create(bill=bill, product=product, quantity=qty, price=price)

        bill.total_amount = total_amount
        bill.save()

    # Stats
    sales_per_product = BillItem.objects.values('product__name').annotate(
        total_sold=Sum('quantity')
    ).order_by('-total_sold')[:10]

    total_sales = Bill.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    total_stock = Product.objects.aggregate(total=Sum('stock'))['total'] or 0

    # Add Supplier
    if request.method == "POST" and 'supplier_submit' in request.POST:
        Supplier.objects.create(
            name=request.POST.get('supplier_name'),
            contact=request.POST.get('supplier_contact'),
            project_name=request.POST.get('project_name'),
            product=request.POST.get('product'),
            quantity=request.POST.get('quantity'),
            amount=request.POST.get('amount'),
            total_budget=request.POST.get('total_budget'),
        )
        messages.success(request, 'Supplier added.')
        return redirect('dashboard')

    suppliers = Supplier.objects.all().order_by('-id')

    context = {
        'products': products,
        'bills': bills,
        'sales_per_product': sales_per_product,
        'total_sales': total_sales,
        'total_stock': total_stock,
        'suppliers': suppliers,
    }
    return render(request, 'inventory/dashboard.html', context)


# ------------------- PDF Generation -------------------
from weasyprint import HTML
import base64

def image_to_base64(path):
    with open(path, "rb") as img:
        return base64.b64encode(img.read()).decode("utf-8")

def generate_bill_pdf(request, bill_id):
    bill = get_object_or_404(Bill, pk=bill_id)
    items = bill.items.all()

    logo_path = "/home/priyadharshiniRV/inventory_app/inventory/static/inventory/logo.png"
    logo_base64 = image_to_base64(logo_path)

    html_string = render_to_string('inventory/bill_pdf.html', {
        'bill': bill,
        'items': items,
        'logo_base64': logo_base64,
    })

    html = HTML(string=html_string)
    pdf_bytes = html.write_pdf()

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="bill_{bill_id}.pdf"'
    return response




# ------------------- Bill Views -------------------
def bill_list(request):
    bills = Bill.objects.all().order_by('-created_at')
    return render(request, 'inventory/bill_list.html', {'bills': bills})


def bill_detail(request, bill_id):
    bill = get_object_or_404(Bill, pk=bill_id)
    items = bill.items.all()
    return render(request, 'inventory/bill_detail.html', {'bill': bill, 'items': items})


# ------------------- CSV Exports -------------------
def export_products_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="products.csv"'
    writer = csv.writer(response)
    writer.writerow(['Name', 'Price', 'Stock'])

    for product in Product.objects.all():
        writer.writerow([product.name, product.price, product.stock])
    return response


def export_bills_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="bills.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Customer', 'Mobile', 'Total', 'Date'])

    for bill in Bill.objects.all():
        writer.writerow([bill.id, bill.customer_name, bill.customer_mobile,
                         bill.total_amount, bill.created_at])
    return response


def export_suppliers_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="suppliers.csv"'
    writer = csv.writer(response)
    writer.writerow(['Name', 'Contact', 'Project', 'Product', 'Qty', 'Amount', 'Budget'])

    for s in Supplier.objects.all():
        writer.writerow([s.name, s.contact, s.project_name, s.product,
                         s.quantity, s.amount, s.total_budget])
    return response


# ------------------- Barcode API -------------------
def get_product_by_barcode(request):
    code = request.GET.get('code')

    if not code:
        return JsonResponse({'error': 'Missing barcode'}, status=400)

    try:
        product = Product.objects.get(barcode_value=code)
        return JsonResponse({
            'id': product.id,
            'name': product.name,
            'price': str(product.price),
            'stock': product.stock,
        })
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)


# ------------------- Print Label -------------------
def print_product_label(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    logo_url = request.build_absolute_uri('/static/inventory/logo.png')

    return render(request, "inventory/print_label.html", {
        'product': product,
        'logo_url': logo_url,
    })
