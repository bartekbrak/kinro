from django.conf.urls import url
from django.contrib import admin

from core import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.dashboard),
    url(r'^start/(?P<tag>.+)$', views.start_time_span),
    # call it end_focused_task
    url(r'^stop/(?P<tag>.*)$', views.end_time_span),

    url(r'^time_spans/$', views.time_span_list, name='time_spans'),
    url(r'^work_hours/$', views.day_span_list, name='work_hours'),
    url(r'^comments/$', views.fake_comments, name='comments'),

    url(r'^insight/(?P<start>[0-9-]+)/(?P<end>[0-9-]+)$',
        views.insight, name='balainsightnce_so_far'),
]
