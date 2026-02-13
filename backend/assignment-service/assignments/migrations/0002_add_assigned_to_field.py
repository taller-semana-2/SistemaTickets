# Generated manually on 2026-02-13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assignments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticketassignment',
            name='assigned_to',
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text='Referencia lógica al usuario asignado (UUID o ID del users-service)',
                max_length=255,
                null=True
            ),
        ),
    ]
