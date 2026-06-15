from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.overview, name="overview"),
    path("election-outcome/", views.election_outcome, name="election_outcome"),
    path("twitter-analytics/", views.twitter_analytics, name="twitter_analytics"),
    path("network-science/", views.network_science, name="network_science"),
    path("online-vs-votes/", views.online_vs_votes, name="online_vs_votes"),
    path("geography/", views.geography, name="geography"),
    path("storytelling/", views.storytelling, name="storytelling"),
    path("interpretation/", views.interpretation, name="interpretation"),
    path("artifact/<path:artifact_path>", views.artifact, name="artifact"),
]
