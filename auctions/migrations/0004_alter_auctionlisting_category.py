# Generated by Django 4.2.14 on 2024-07-28 15:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("auctions", "0003_category_auctionlisting"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auctionlisting",
            name="category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="category",
                to="auctions.category",
            ),
        ),
    ]
