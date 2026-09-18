from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Song",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("song_id", models.CharField(max_length=128, unique=True)),
                ("song", models.CharField(max_length=255)),
                ("idol", models.CharField(max_length=255)),
                ("ask_count", models.IntegerField(default=0)),
                ("lyrics_view", models.IntegerField(default=0)),
                ("youtube_view", models.IntegerField(default=0)),
                ("score", models.FloatField(default=0)),
                ("observed_at", models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Ranking",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("rank", models.IntegerField()),
                ("score", models.FloatField()),
                ("observed_at", models.DateTimeField(auto_now_add=True)),
                ("song", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="catalog.song")),
            ],
        ),
    ]
