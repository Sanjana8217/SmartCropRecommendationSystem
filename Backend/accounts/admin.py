from django.contrib import admin
from .models import CropPrediction, Feedback

admin.site.register(CropPrediction)
admin.site.register(Feedback)
class CropPredictionAdmin(admin.ModelAdmin):
    list_display = (
        "crop",
        "fertilizer",
        "nitrogen",
        "phosphorus",
        "potassium",
        "created_at",
    )
    search_fields = ("crop", "fertilizer")
    list_filter = ("crop", "created_at")