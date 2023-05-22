""" Contenstore API v1 URLs. """

from django.urls import re_path

from openedx.core.constants import COURSE_ID_PATTERN

from .views import proctored_exam_settings

app_name = 'v1'

urlpatterns = [
    re_path(
        fr'^proctored_exam_settings/{COURSE_ID_PATTERN}$',
        proctored_exam_settings.ProctoredExamSettingsView.as_view(),
        name="proctored_exam_settings"
    ),
]
