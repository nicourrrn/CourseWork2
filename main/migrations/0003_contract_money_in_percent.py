# Generated by Django 4.1.3 on 2022-12-18 17:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_rename_birtsday_client_birthday'),
    ]

    operations = [
        migrations.AddField(
            model_name='contract',
            name='money_in_percent',
            field=models.IntegerField(default=3),
        ),
    ]