# Generated by Django 3.1.4 on 2021-03-16 13:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0009_blocks_formlist'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='blocks',
            name='formlist',
        ),
    ]
