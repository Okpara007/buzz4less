# Generated by Django 5.0.7 on 2024-09-22 18:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_profile'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Profile',
        ),
    ]