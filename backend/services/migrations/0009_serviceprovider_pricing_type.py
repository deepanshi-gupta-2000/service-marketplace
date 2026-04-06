from django.db import migrations, models


def copy_service_pricing_to_provider(apps, schema_editor):
    ServiceProvider = apps.get_model("services", "ServiceProvider")

    for provider in ServiceProvider.objects.select_related("service").all():
        provider.pricing_type = provider.service.pricing_type or "fixed"
        provider.save(update_fields=["pricing_type"])


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0008_refurbishment_inspection_pricing"),
    ]

    operations = [
        migrations.AddField(
            model_name="serviceprovider",
            name="pricing_type",
            field=models.CharField(
                choices=[
                    ("fixed", "Fixed Price"),
                    ("starting_from", "Starting From"),
                    ("inspection", "Inspection Required"),
                    ("custom_quote", "Custom Quote"),
                ],
                default="fixed",
                max_length=20,
            ),
        ),
        migrations.RunPython(copy_service_pricing_to_provider, migrations.RunPython.noop),
    ]
