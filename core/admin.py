"""
I treat admin like part of the application, some things you can only do there.
"""
from django.contrib import admin
from django.utils.safestring import mark_safe

from django.contrib.auth.models import Group, User
from django.db import models
from django.forms import Textarea, TextInput, fields, ModelForm, CharField
from mptt.admin import DraggableMPTTAdmin

from core.fields import ColorField
from core.models import Bucket, DailyTarget, TimeSpan
from core.utils import draw_progress_bar, to_human_readable_in_hours
from pytimeparse import parse as to_seconds


class TimeSpanAdmin(admin.ModelAdmin):
    list_display = ('day_of_week', 'display', 'bucket', 'comment')
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    }

    def display(self, obj):
        return '{obj.start:%Y:%m-%d %H:%M}-{end}'.format(
            obj=obj, end='{:%H:%M}'.format(obj.end) if obj.end else '??:??'
        )

    def day_of_week(self, obj):
        return obj.start.strftime('%A')


class TimeSpanInline(admin.TabularInline):
    # What I really want here is just a list of objects with a 'change' link, they are changed
    # rarely, more work needed
    model = TimeSpan
    extra = 0
    show_change_link = True
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    }


class BucketAdmin(DraggableMPTTAdmin):
    mptt_level_indent = 20
    mptt_indent_field = "title"
    list_display = (
        'tree_actions', 'indented_title',
        'display_color',
        'progress_bar',
        'type',
        'estimate',
        'local_total',
        'display_family_merged',
        # 'timespans'  # DEBUG
    )
    list_display_links = (
        'indented_title',
    )
    formfield_overrides = {
        ColorField: {'widget': TextInput(attrs={'type':'color'})},
    }
    inlines = [
        TimeSpanInline,
    ]

    def local_total(self, obj):
        count = obj.timespan_set.count()
        if not count:
            return ''
        merged = obj.timespan_set.merged_total()
        return '%s (%s)' % (to_human_readable_in_hours(merged), count)

    def display_color(self, obj):
        """Color box as a column."""
        return (
            '<div style="'
            'width:50px;background-color:%s;position:relative;height:1.5em'
            '"></div>' % obj.color
        )
    display_color.short_description = ''
    display_color.allow_tags = True

    def display_family_merged(self, obj):
        """Merged time of all timespans in this and all descendants."""
        family = obj.family_time_spans_q()
        return '%s (%s)' % (to_human_readable_in_hours(family.merged_total()), family.count())

    def progress_bar(self, obj):
        estimate = obj.estimate
        if not estimate:
            return ''
        merged = obj.timespan_set.merged_total()
        return draw_progress_bar(merged, obj.estimate)

    progress_bar.allow_tags = True

    def get_queryset(self, request):
        qs = super(BucketAdmin, self).get_queryset(request)
        return qs.prefetch_related('timespan_set')

    def timespans(self, obj):
        # performance killer, debug only
        return '<br>'.join('%s - %s' % (s.strftime('%m.%d %H:%M'), e.strftime('%m.%d %H:%M')) for s, e in obj.timespan_set.all().values_list('start', 'end'))
    timespans.allow_tags = True



class DailyTargetAdminForm(ModelForm):
    amount = CharField(
        help_text=mark_safe(
            'Many <a href="https://github.com/wroberts/pytimeparse">formats</a> are possible, '
            '8hrs, 4h 20m, 2h32m, etc.'
        ),
        max_length=20
    )
    # TODO, change back to human readable
    # str(datetime.timedelta(seconds=138016))

    def clean_amount(self):
        return to_seconds(self.cleaned_data["amount"])


class DailyTargetAdmin(admin.ModelAdmin):
    list_display = ('bucket', 'date', 'display_amount', 'fresh_start')
    ordering = ('-date', )
    form = DailyTargetAdminForm

    def display_amount(self, obj):
        return to_human_readable_in_hours(obj.amount)
    display_amount.short_description = 'target'

admin.site.register(TimeSpan, TimeSpanAdmin)
admin.site.register(Bucket, BucketAdmin)
admin.site.register(DailyTarget, DailyTargetAdmin)
admin.site.unregister(User)
admin.site.unregister(Group)
