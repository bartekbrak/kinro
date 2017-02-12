from django.conf.urls import url
from django.contrib import admin

from core import views

urlpatterns = [
    url(r'^$', views.dashboard),
    # dashboard for a given date, the problem is that navigating in frontend does not change the url
    # value dynamically, this is surprising
    url(r'^(?P<start>[0-9-]+)$', views.dashboard),
    url(r'^start/(?P<title>.+)$', views.start_time_span),
    url(r'^stop/(?P<title>.*)$', views.end_time_span),

    # lists
    url(r'^time_spans/$', views.time_span_list, name='time_spans'),
    url(r'^insight/(?P<start>[0-9-]+)/(?P<end>[0-9-]+)$', views.insight, name='insight'),

    url(r'^admin/', admin.site.urls),
    # experiments
    url(r'^tree/$', views.tree, name='tree'),


]
