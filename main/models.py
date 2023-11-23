import datetime
from datetime import time
from django.db import models
from django.db.models import Model


# Create your models here.


class DocumentType(Model):
    document_type_name = models.CharField(max_length=32, unique=True)

    def __str__(self):
        return f"{self.document_type_name}"


class Client(Model):
    identification_code = models.PositiveBigIntegerField()
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    by_father_name = models.CharField(max_length=64)
    birthday = models.DateField()
    phone = models.PositiveBigIntegerField()
    email = models.CharField(max_length=128)
    document_num = models.CharField(max_length=64)
    document_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.first_name} {self.last_name} {self.by_father_name}"

    @staticmethod
    def get_class():
        return "Client"


class Branch(Model):
    branch_address = models.TextField()
    open_time = models.TimeField()
    close_time = models.TimeField()

    def __str__(self):
        return f"{self.branch_address}"


class Position(Model):
    position_name = models.CharField(max_length=32)
    rank = models.SmallIntegerField()

    def __str__(self):
        return f"{self.position_name}"


class Worker(Model):
    passport_num = models.CharField(max_length=9, unique=True)
    identification_code = models.BigIntegerField(unique=True)
    phone = models.BigIntegerField(unique=True)
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    by_father_name = models.CharField(max_length=64)
    birthday = models.DateField()
    email = models.CharField(max_length=64, unique=True)
    card_num = models.BigIntegerField(unique=True)
    worker_address = models.TextField()
    start_work_at = models.DateField(default=datetime.date.today())
    password = models.CharField(max_length=128, default='123456')
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.first_name} {self.last_name} {self.by_father_name}"

    @staticmethod
    def get_class():
        return "Worker"


class Contract(Model):
    from_date = models.DateField(default=datetime.date.today())
    to_date = models.DateField(default=datetime.date.today() + datetime.timedelta(days=14))
    money_out = models.IntegerField()
    money_in_percent = models.IntegerField(default=3)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)

    def __str__(self):
        return f"№{self.id} {self.client}"


class Material(Model):
    material_name = models.CharField(max_length=32)
    selling_price = models.IntegerField()
    purchase_price = models.IntegerField()

    def __str__(self):
        return f"{self.material_name}"


class ItemType(Model):
    item_type_name = models.CharField(max_length=32)

    def __str__(self):
        return f"{self.item_type_name}"


class Item(Model):
    item_name = models.CharField(max_length=64)
    cost = models.IntegerField()
    weight = models.IntegerField()
    volume = models.IntegerField(null=True)
    description = models.TextField()
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    contract = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True)
    types = models.ManyToManyField(ItemType)
    materials = models.ManyToManyField(Material)

    def __str__(self):
        return f"№{self.id}: {self.item_name}"
