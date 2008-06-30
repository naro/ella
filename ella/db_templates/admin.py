from django.contrib import admin
from django.newforms.models import BaseInlineFormset
from django.newforms.forms import ValidationError, NON_FIELD_ERRORS
from django.utils.translation import ugettext as _

from ella.db_templates.models import DbTemplate, TemplateBlock


class TemplateBlockFormset(BaseInlineFormset):
    "Custom formset enabling us to supply custom validation."

    @staticmethod
    def cmp_by_till(f, t):
        if f[1] is None:
            return 1
        elif t[1] is None:
            return -1
        else:
            return cmp(f[1], t[1])

    def clean(self):
        " Validate that the template's activity don't overlap. "
        if not self.is_valid():
            return

        # check that active_till datetime is greather then active_from
        validation_error = None
        for i,d in ((i,d) for i,d in enumerate(self.cleaned_data) if d):
            # don't bother with empty edit-inlines
            if not d:
                continue
            # both datetimes entered
            if d['active_from'] and d['active_till']:
                if d['active_from'] > d['active_till']:
                    validation_error = ValidationError(_('Block active till must be greather then Block active from'))
                    self.forms[i]._errors['active_till'] = validation_error.messages
        if validation_error:
            raise ValidationError(_('Invalid datetime interval. Block active till must be greather then Block active from'))

        # dictionary of blocks with tuples (active from, active till)
        items = {}
        for i,d in ((i,d) for i,d in enumerate(self.cleaned_data) if d):
            if not items.has_key(d['name']):
                items[d['name']] = [(d['active_from'], d['active_till'])]
            else:
                items[d['name']].append((d['active_from'], d['active_till']))

        # check that intervals are not in colision
        errors = []
        error_message = _('Block active intervals are in colision on %s. Specified interval stops at %s and next interval started at %s.')
        for name, intervals in items.items():
            if len(intervals) > 1:
                intervals.sort(self.cmp_by_till)
                for i in xrange(len(intervals)-1):
                    try:
                        # exact covering allwoved (00:00:00 to 00:00:00)
                        if intervals[i][1] > intervals[i+1][0]:
                            errors.append(error_message % (name, intervals[i][1], intervals[i+1][0]))
                    except TypeError:
                        errors.append(error_message % (name, 'Infinite', intervals[i+1][0]))
        if errors:
            raise ValidationError, errors

        return self.cleaned_data

class TemplateBlockInlineOptions(admin.TabularInline):
    model = TemplateBlock
    extra = 3
    fieldsets = ((None, {'fields' : ('name', 'box_type', 'target_ct', 'target_id', 'active_from', 'active_till', 'text',)}),)
    formset = TemplateBlockFormset

class DbTemplateOptions(admin.ModelAdmin):
    ordering = ('description',)
    inlines = (TemplateBlockInlineOptions,)
    list_display = ('name', 'site', 'extends', 'description',)
    list_filter = ('site',)

admin.site.register(DbTemplate, DbTemplateOptions)

