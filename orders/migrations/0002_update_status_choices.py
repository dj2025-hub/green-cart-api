from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("PENDING", "En attente"),
                    ("PROCESSING", "En préparation"),
                    ("READY", "Prête"),
                    ("SHIPPED", "Expédiée"),
                    ("DELIVERED", "Livrée"),
                    ("CANCELLED", "Annulée"),
                ],
                default="PENDING",
                help_text="Statut actuel de la commande",
                max_length=20,
                verbose_name="Statut",
            ),
        ),
        migrations.AlterField(
            model_name="orderstatushistory",
            name="old_status",
            field=models.CharField(
                blank=True,
                choices=[
                    ("PENDING", "En attente"),
                    ("PROCESSING", "En préparation"),
                    ("READY", "Prête"),
                    ("SHIPPED", "Expédiée"),
                    ("DELIVERED", "Livrée"),
                    ("CANCELLED", "Annulée"),
                ],
                max_length=20,
                verbose_name="Ancien statut",
            ),
        ),
        migrations.AlterField(
            model_name="orderstatushistory",
            name="new_status",
            field=models.CharField(
                choices=[
                    ("PENDING", "En attente"),
                    ("PROCESSING", "En préparation"),
                    ("READY", "Prête"),
                    ("SHIPPED", "Expédiée"),
                    ("DELIVERED", "Livrée"),
                    ("CANCELLED", "Annulée"),
                ],
                max_length=20,
                verbose_name="Nouveau statut",
            ),
        ),
    ]


