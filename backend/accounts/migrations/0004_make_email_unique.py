from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_normalize_and_unique_user_email"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="user",
            name="unique_user_email_ci",
        ),
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.EmailField(max_length=254, unique=True),
        ),
    ]
