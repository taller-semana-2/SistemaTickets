"""
Migration: 0003_seed_admin

Inserta el usuario administrador inicial en la base de datos.
Se ejecuta automáticamente al correr `python manage.py migrate`.

Usa get_or_create para ser idempotente: si el usuario ya existe no falla
ni crea duplicados.

Credenciales del admin:
  - username : admin
  - email    : admin@sofkau.com
  - password : Admin@SofkaU_2026!   (hash SHA-256, igual que usa el servicio)
"""

import hashlib
import uuid

from django.db import migrations


ADMIN_UUID = "0ba1c571-5131-4001-af89-deb9aebcd735"
ADMIN_EMAIL = "admin@sofkau.com"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Admin@SofkaU_2026!"


def _hash_password(password: str) -> str:
    """SHA-256, idéntico al método usado en users/application/use_cases.py."""
    return hashlib.sha256(password.encode()).hexdigest()


def seed_admin(apps, schema_editor):
    """Crea el usuario admin si no existe todavía."""
    User = apps.get_model("users", "User")

    User.objects.get_or_create(
        username=ADMIN_USERNAME,
        defaults={
            "id": ADMIN_UUID,
            "email": ADMIN_EMAIL,
            "password_hash": _hash_password(ADMIN_PASSWORD),
            "is_active": True,
            "role": "ADMIN",
        },
    )


def remove_admin(apps, schema_editor):
    """Revierte la migración eliminando el usuario admin."""
    User = apps.get_model("users", "User")
    User.objects.filter(username=ADMIN_USERNAME).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_user_role"),
    ]

    operations = [
        migrations.RunPython(seed_admin, reverse_code=remove_admin),
    ]
