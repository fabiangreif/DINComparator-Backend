# Generated by Django 4.0.1 on 2022-03-15 20:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hello', '0004_remove_searchrequest_keywords'),
    ]

    operations = [
        migrations.AddField(
            model_name='searchrequest',
            name='keywords',
            field=models.TextField(default=''),
        ),
    ]
