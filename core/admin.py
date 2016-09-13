from django.contrib import admin

from core.models import Bucket, Client, Comment, Day, TimeSpan
from core.utils import to_human_readable_in_hours


class TimeSpanAdmin(admin.ModelAdmin):
    list_display = ('display', 'bucket', 'comment')

    def display(self, obj):
        return '{obj.day.date:%A, %d-%m}, {obj.start:%H:%M}-{end}'.format(
            obj=obj, end='{:%H:%M}'.format(obj.end) if obj.end else '??:??'
        )


class BucketAdmin(admin.ModelAdmin):
    list_display = (
        'tag', 'title', 'display_color', 'type', 'estimate', 'client', 'total', 'time_span_count')
    ordering = ('-last_started',)

    def total(self, obj):
        return to_human_readable_in_hours(obj.timespan_set.summed())

    def display_color(self, obj):
        """Color box as a column."""
        return (
            '<span style="'
            'width:50px;height:15px;background-color:%s;display:block;border:1px solid black'
            '"></span>' % obj.color
        )
    display_color.short_description = 'See Color'
    display_color.allow_tags = True

    def time_span_count(self, obj):
        return obj.timespan_set.count()


class DayAdmin(admin.ModelAdmin):
    list_display = ('day_of_week', 'date', 'worked_hours', 'planned_delta')
    ordering = ('-date',)

    def worked_hours(self, obj):
        return to_human_readable_in_hours(obj.worked or 0)

    def day_of_week(self, obj):
        return obj.date.strftime('%A')


class ClientAdmin(admin.ModelAdmin):
    pass

admin.site.register(Day, DayAdmin)
admin.site.register(TimeSpan, TimeSpanAdmin)
admin.site.register(Bucket, BucketAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(Comment)
