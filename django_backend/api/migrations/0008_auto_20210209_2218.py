# Generated by Django 3.1.4 on 2021-02-09 16:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_auto_20210209_1555'),
    ]

    operations = [
        migrations.AddField(
            model_name='blocks',
            name='user_id',
            field=models.TextField(default='user1'),
        ),
        migrations.AddField(
            model_name='ngspicecode',
            name='user_id',
            field=models.TextField(default='user1'),
        ),
        migrations.AddField(
            model_name='outputplot',
            name='user_id',
            field=models.TextField(default='user1'),
        ),
    ]