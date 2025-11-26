from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('bills/', views.bill_list, name='bill_list'),
    path('bill/<int:bill_id>/', views.bill_detail, name='bill_detail'),
    path('bill/<int:bill_id>/pdf/', views.generate_bill_pdf, name='generate_bill_pdf'),
    path('backup/products/', views.export_products_csv, name='export_products_csv'),
    path('backup/bills/', views.export_bills_csv, name='export_bills_csv'),
    path('export-suppliers-csv/', views.export_suppliers_csv, name='export_suppliers_csv'),
    path('api/get-product-by-barcode/', views.get_product_by_barcode, name='get_product_by_barcode'),
    path('product/<int:product_id>/print_label/', views.print_product_label, name='print_product_label'),


]
