from django.urls import path
from . import views


urlpatterns = [
    path("", views.manager_dashboard, name="manager_dashboard"),
    path("team-lead/", views.team_lead_dashboard, name="team_lead_dashboard"),
    path("kpi/", views.kpi_dashboard, name="kpi_dashboard"),
    path("report/", views.report_completed_tasks, name="report_completed_tasks"),
    path("heatmap/", views.productivity_heatmap_view, name="productivity_heatmap"),
]
