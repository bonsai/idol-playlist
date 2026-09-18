from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="song",
            name="youtube_video_id",
            field=models.CharField(blank=True, max_length=32),
        ),
    ]
