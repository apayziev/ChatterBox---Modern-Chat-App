# Generated by Django 5.0.7 on 2025-01-13 05:58

import chat.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0003_alter_message_options_message_is_read_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to=chat.models.message_file_path),
        ),
    ]
