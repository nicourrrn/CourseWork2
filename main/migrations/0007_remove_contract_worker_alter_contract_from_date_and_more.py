# Generated by Django 4.1.4 on 2023-01-01 16:50

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0006_alter_contract_from_date_alter_contract_to_date_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contract',
            name='worker',
        ),
        migrations.AlterField(
            model_name='contract',
            name='from_date',
            field=models.DateField(default=datetime.date(2023, 1, 1)),
        ),
        migrations.AlterField(
            model_name='contract',
            name='to_date',
            field=models.DateField(default=datetime.date(2023, 1, 15)),
        ),
        migrations.AlterField(
            model_name='worker',
            name='start_work_at',
            field=models.DateField(default=datetime.date(2023, 1, 1)),
        ),
    ]
