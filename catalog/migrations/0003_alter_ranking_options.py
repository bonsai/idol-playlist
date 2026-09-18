from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0002_song_youtube_video_id"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="ranking",
            options={"ordering": ("rank",)},
        ),
    ]
