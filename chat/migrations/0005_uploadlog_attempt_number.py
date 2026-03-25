from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0004_uploadlog_alter_documentchunk_table"),
    ]

    operations = [
        migrations.AddField(
            model_name="uploadlog",
            name="attempt_number",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
