from django.db import migrations, models
from django.db.models import Q
from django.db.models.functions import Lower


def normalize_and_deduplicate_emails(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    seen = set()

    for user in User.objects.exclude(email="").order_by("id"):
        normalized = user.email.strip().lower()

        if normalized not in seen:
            if user.email != normalized:
                user.email = normalized
                user.save(update_fields=["email"])
            seen.add(normalized)
            continue

        local_part, at, domain = normalized.partition("@")
        candidate = f"{local_part}+dedup{user.id}{at}{domain}" if at else f"{normalized}+dedup{user.id}"

        while User.objects.filter(email__iexact=candidate).exclude(id=user.id).exists():
            candidate = f"{local_part}+dedup{user.id}x{at}{domain}" if at else f"{candidate}x"

        user.email = candidate
        user.save(update_fields=["email"])
        seen.add(candidate.lower())


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_alter_user_role"),
    ]

    operations = [
        migrations.RunPython(normalize_and_deduplicate_emails, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                Lower("email"),
                condition=~Q(email=""),
                name="unique_user_email_ci",
            ),
        ),
    ]
