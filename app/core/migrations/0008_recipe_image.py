# Generated by Django 4.2.5 on 2023-11-06 10:45

import core.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_recipe_ingredients'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to=core.models.recipe_image_file_path),
        ),
    ]