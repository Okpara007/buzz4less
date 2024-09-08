# Generated by Django 5.0.7 on 2024-09-08 12:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0004_alter_service_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='plan',
            name='service',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='plans', to='services.service'),
        ),
    ]