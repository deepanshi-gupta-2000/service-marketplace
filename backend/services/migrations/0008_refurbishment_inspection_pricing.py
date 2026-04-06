from django.db import migrations


def set_refurbishment_to_inspection(apps, schema_editor):
    Service = apps.get_model("services", "Service")
    Service.objects.filter(name__iexact="Refurbishment").update(
        pricing_type="inspection",
        starting_price=None,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0007_service_pricing_type_service_starting_price"),
    ]

    operations = [
        migrations.RunPython(set_refurbishment_to_inspection, migrations.RunPython.noop),
    ]
