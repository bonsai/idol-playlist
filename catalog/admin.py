from django.contrib import admin

from .models import Ranking, Song


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ("song_id", "song", "idol", "score", "ask_count", "observed_at")
    search_fields = ("song_id", "song", "idol")
    ordering = ("-score",)


@admin.register(Ranking)
class RankingAdmin(admin.ModelAdmin):
    list_display = ("rank", "song", "score", "observed_at")
    list_filter = ("observed_at",)
    ordering = ("rank",)
