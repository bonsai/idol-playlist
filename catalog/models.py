from django.db import models

class Song(models.Model):
    song_id = models.CharField(max_length=128, unique=True)
    song = models.CharField(max_length=255)
    idol = models.CharField(max_length=255)
    ask_count = models.IntegerField(default=0)
    lyrics_view = models.IntegerField(default=0)
    youtube_view = models.IntegerField(default=0)
    score = models.FloatField(default=0)
    observed_at = models.DateTimeField(null=True, blank=True)

class Ranking(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    rank = models.IntegerField()
    score = models.FloatField()
    observed_at = models.DateTimeField(auto_now_add=True)
