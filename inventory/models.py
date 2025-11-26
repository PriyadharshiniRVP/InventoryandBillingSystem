import barcode
from barcode.writer import ImageWriter
from io import BytesIO
from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    barcode_image = models.ImageField(upload_to='barcodes/', blank=True, null=True)
    barcode_value = models.CharField(max_length=32, blank=True, null=True)  # Add unique=True after data is ready

    def save(self, *args, **kwargs):
        creating = self.pk is None
        super().save(*args, **kwargs)  # Ensure pk exists

        # Always ensure barcode_value is set
        if not self.barcode_value:
            self.barcode_value = f'PROD{self.pk}'
            super().save(update_fields=['barcode_value'])

        # Always generate barcode image from barcode_value if missing
        if not self.barcode_image:
            CODE128 = barcode.get_barcode_class('code128')
            bar_img = CODE128(self.barcode_value, writer=ImageWriter())
            buffer = BytesIO()
            bar_img.write(buffer)
            buffer.seek(0)
            self.barcode_image.save(f'barcode_{self.pk}.png', ContentFile(buffer.getvalue()), save=False)
            buffer.close()
            super().save(update_fields=['barcode_image'])

    def __str__(self):
        return self.name




class TeamMember(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Bill(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    customer_name = models.CharField(max_length=100, default='Unknown')
    customer_mobile = models.CharField(max_length=15, default='Unknown')
    customer_address = models.TextField(default='Unknown')
    project_manager = models.CharField(max_length=200, default="Unknown")

    def __str__(self):
        return f'Bill #{self.id} - {self.created_at.strftime("%Y-%m-%d %H:%M:%S")}'


class BillItem(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def get_cost(self):
        return self.price * self.quantity
class Supplier(models.Model):
    name = models.CharField(max_length=200)
    contact = models.CharField(max_length=100, blank=True)
    project_name = models.CharField(max_length=200)
    product = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_budget = models.DecimalField(max_digits=12, decimal_places=2)
    def __str__(self):
        return f"{self.name} - {self.project_name}"

