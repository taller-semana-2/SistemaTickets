from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ticket_id', models.CharField(max_length=128, db_index=True)),
                ('message', models.TextField(blank=True)),
                ('sent_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
