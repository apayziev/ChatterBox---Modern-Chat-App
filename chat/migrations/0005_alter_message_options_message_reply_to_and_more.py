# Generated by Django 5.0.7 on 2025-01-13 08:19

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0004_alter_message_file'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='message',
            options={'ordering': ['timestamp']},
        ),
        migrations.AddField(
            model_name='message',
            name='reply_to',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='replies', to='chat.message'),
        ),
        migrations.AlterField(
            model_name='message',
            name='content',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='message',
            name='room',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='chat.room'),
        ),
        migrations.AlterField(
            model_name='room',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='room',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='room',
            name='title',
            field=models.CharField(max_length=255),
        ),
    ]
