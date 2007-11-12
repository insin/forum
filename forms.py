import datetime
import operator
import urllib

from django import newforms as forms
from django.db.models.query import Q, QNot
from django.template.defaultfilters import filesizeformat
from django.utils.text import capfirst, get_text_list, smart_split

from forum import app_settings
from forum.models import Post, Section
from PIL import ImageFile

#########
# Forms #
#########

class SectionForm(forms.Form):
    name    = forms.CharField(max_length=100)
    section = forms.ChoiceField(required=False)

    def __init__(self, sections, *args, **kwargs):
        super(SectionForm, self).__init__(*args, **kwargs)
        self.sections = sections
        self.fields['section'].choices = [(u'', u'----------')] + \
            [(section.id, section.name) for section in sections]

    def clean_name(self):
        for section in self.sections:
            if self.cleaned_data['name'] == section.name:
                raise forms.ValidationError(
                    u'A Section with this name already exists.')
        return self.cleaned_data['name']

class EditSectionBaseForm(forms.BaseForm):
    def clean_name(self):
        if self.fields['name'].initial != self.cleaned_data['name']:
            try:
                Section.objects.get(name=self.cleaned_data['name'])
                raise forms.ValidationError(
                    u'A Section with this name already exists.')
            except Section.DoesNotExist:
                pass
        return self.cleaned_data['name']

class ForumForm(forms.Form):
    name        = forms.CharField(max_length=100)
    description = forms.CharField(max_length=100, required=False, widget=forms.Textarea())
    forum       = forms.ChoiceField(required=False)

    def __init__(self, forums, *args, **kwargs):
        super(ForumForm, self).__init__(*args, **kwargs)
        self.fields['forum'].choices = [(u'', u'----------')] + \
            [(forum.id, forum.name) for forum in forums]

class SearchPostsForm(forms.Form):
    """
    Provides criteria for searching Posts and creates QuerySets based on
    selected criteria.
    """
    SEARCH_ALL_FORUMS = 'A'
    SEARCH_IN_SECTION = 'S'
    SEARCH_IN_FORUM   = 'F'

    SEARCH_ALL_POSTS     = 'A'
    SEARCH_REGULAR_POSTS = 'R'
    SEARCH_METAPOSTS     = 'M'
    SEARCH_POST_TYPE_CHOICES = (
        (SEARCH_ALL_POSTS, 'All Posts'),
        (SEARCH_REGULAR_POSTS, 'Regular Posts'),
        (SEARCH_METAPOSTS, 'Metaposts'),
    )

    SEARCH_FROM_TODAY = 'T'
    SEARCH_ANY_DATE   = 'A'
    SEARCH_FROM_CHOICES = (
        (SEARCH_FROM_TODAY, 'Today and...'),
        (7, '7 days ago and...'),
        (30, '30 days ago and...'),
        (60, '60 days ago and...'),
        (90, '90 days ago and...'),
        (180, '180 days ago and...'),
        (365, '365 days ago and...'),
        (SEARCH_ANY_DATE, 'Any date'),
    )

    SEARCH_OLDER = 'O'
    SEARCH_NEWER = 'N'
    SEARCH_WHEN_CHOICES = (
        (SEARCH_OLDER, 'Older'),
        (SEARCH_NEWER, 'Newer'),
    )
    SEARCH_WHEN_LOOKUP = {
        SEARCH_OLDER: 'lte',
        SEARCH_NEWER: 'gte',
    }

    SORT_DESCENDING = 'D'
    SORT_ASCENDING  = 'A'
    SORT_DIRECTION_CHOICES = (
        (SORT_DESCENDING, 'Descending'),
        (SORT_ASCENDING, 'Ascending'),
    )
    SORT_DIRECTION_FLAG = {
        SORT_DESCENDING: '-',
        SORT_ASCENDING: '',
    }

    USERNAME_LOOKUP = {True: '', False: '__icontains'}

    keywords       = forms.CharField()
    username       = forms.CharField(required=False)
    exact_username = forms.BooleanField(required=False, initial=True, label=u'Match exact username')
    post_type      = forms.ChoiceField(choices=SEARCH_POST_TYPE_CHOICES, initial=SEARCH_ALL_POSTS, widget=forms.RadioSelect)
    search_in      = forms.MultipleChoiceField(required=False, initial=[SEARCH_ALL_FORUMS])
    search_from    = forms.ChoiceField(choices=SEARCH_FROM_CHOICES)
    search_when    = forms.ChoiceField(choices=SEARCH_WHEN_CHOICES, initial=SEARCH_OLDER, widget=forms.RadioSelect)
    sort_direction = forms.ChoiceField(choices=SORT_DIRECTION_CHOICES, initial=SORT_DESCENDING, widget=forms.RadioSelect)

    def __init__(self, *args, **kwargs):
        super(SearchPostsForm, self).__init__(*args, **kwargs)
        choices = [(self.SEARCH_ALL_FORUMS, u'All Forums')]
        for section, forums in Section.objects.get_forums_by_section():
            choices.append(('%s.%s' % (self.SEARCH_IN_SECTION, section.pk),
                            section.name))
            choices.extend([('%s.%s' % (self.SEARCH_IN_FORUM, forum.pk),
                            u'|-- %s' % forum.name) \
                            for forum in forums])
        self.fields['search_in'].choices = choices
        self.fields['search_in'].widget.attrs['size'] = 10

    def clean_keywords(self):
        """
        Validates that no search keyword is shorter than 3 characters.
        """
        for keyword in smart_split(self.cleaned_data['keywords']):
            keyword_len = len(keyword)
            if keyword[0] in ('+', '-'):
                keyword_len = keyword_len - 1
            elif keyword[0] == '"' and keyword[-1] == '"' or \
                 keyword[0] == "'" and keyword[-1] == "'":
                keyword_len = keyword_len - 2
            if keyword_len < 3:
                raise forms.ValidationError('Keywords must be a minimun of 3 characters long.')
        return self.cleaned_data['keywords']

    def get_queryset(self):
        """
        Creates a ``QuerySet`` based on the search criteria specified in
        this form.

        Returns ``None`` if the form doesn't appear to have been
        validated.
        """
        if not hasattr(self, 'cleaned_data'):
            return None

        filters = []

        search_in = {}
        if len(self.cleaned_data['search_in']) and \
           self.SEARCH_ALL_FORUMS not in self.cleaned_data['search_in']:
            for item in self.cleaned_data['search_in']:
                bits = item.split('.')
                search_in.setdefault(bits[0], []).append(bits[1])

        from_date = None
        if self.cleaned_data['search_from'] != self.SEARCH_ANY_DATE:
            from_date = datetime.date.today()
            if self.cleaned_data['search_from'] != self.SEARCH_FROM_TODAY:
                days_ago = int(self.cleaned_data['search_from'])
                from_date = from_date - datetime.timedelta(days=days_ago)

        if self.cleaned_data['post_type'] != self.SEARCH_ALL_POSTS:
            meta = self.cleaned_data['post_type'] == self.SEARCH_METAPOSTS
            filters.append(Q(meta=meta))

        if self.SEARCH_IN_SECTION in search_in and \
           self.SEARCH_IN_FORUM in search_in:
            filters.append(Q(topic__forum__section__in=\
                             search_in[self.SEARCH_IN_SECTION]) | \
                           Q(topic__forum__in=search_in[self.SEARCH_IN_FORUM]))
        elif self.SEARCH_IN_SECTION in search_in:
            filters.append(Q(topic__forum__section__in=\
                             search_in[self.SEARCH_IN_SECTION]))
        elif self.SEARCH_IN_FORUM in search_in:
            filters.append(Q(topic__forum__in=search_in[self.SEARCH_IN_FORUM]))

        if from_date is not None:
            lookup_type = self.SEARCH_WHEN_LOOKUP[self.cleaned_data['search_when']]
            filters.append(Q(**{'posted_at__%s' % lookup_type: from_date}))

        if self.cleaned_data['username']:
            lookup_type = self.USERNAME_LOOKUP[self.cleaned_data['exact_username']]
            filters.append(Q(**{'user__username%s' % lookup_type: \
                                self.cleaned_data['username']}))

        one_of_filters = []
        phrase_filters = []
        for keyword in smart_split(self.cleaned_data['keywords']):
            if keyword[0] == '+':
                filters.append(Q(body__icontains=keyword[1:]))
            elif keyword[0] == '-':
                filters.append(QNot(Q(body__icontains=keyword[1:])))
            elif keyword[0] == '"' and keyword[-1] == '"' or \
                 keyword[0] == "'" and keyword[-1] == "'":
                phrase_filters.append(Q(body__icontains=keyword[1:-1]))
            else:
                one_of_filters.append(Q(body__icontains=keyword))
        if one_of_filters:
            filters.append(reduce(operator.or_, one_of_filters))
        if phrase_filters:
            filters.append(reduce(operator.or_, phrase_filters))

        # Apply filters and perform ordering
        qs = Post.objects.all()
        if len(filters):
            qs = qs.filter(reduce(operator.and_, filters))
        sort_direction_flag = \
            self.SORT_DIRECTION_FLAG[self.cleaned_data['sort_direction']]
        return qs.order_by('%sposted_at' % sort_direction_flag,
                           '%sid' % sort_direction_flag)

#######################
# Formfield Callbacks #
#######################

def topic_formfield_callback(field, **kwargs):
    """
    Callback for Post form field creation.

    Customises the size of the widgets used to edit topic details.
    """
    if field.name in ['title', 'description']:
        formfield = field.formfield(**kwargs)
        formfield.widget.attrs['size'] = 50
        return formfield
    else:
        return field.formfield(**kwargs)

def post_formfield_callback(field, **kwargs):
    """
    Callback for Post form field creation.

    Customises the widget used to edit posts.
    """
    if field.name == 'body':
        formfield = field.formfield(**kwargs)
        formfield.widget.attrs['rows'] = 14
        formfield.widget.attrs['cols'] = 70
        return formfield
    else:
        return field.formfield(**kwargs)

def forum_profile_formfield_callback(field, **kwargs):
    """
    Callback for forum profile form field creation.

    Generates an ``ImageURLField`` for the ``avatar`` field and default
    fields for all others.
    """
    if field.name == 'avatar':
        args = {
            'verify_exists': field.verify_exists,
            'max_length': field.max_length,
            'required': not field.blank,
            'label': capfirst(field.verbose_name),
            'help_text': field.help_text,
        }
        if app_settings.MAX_AVATAR_FILESIZE is not None:
            args['max_filesize'] = app_settings.MAX_AVATAR_FILESIZE
        if app_settings.ALLOWED_AVATAR_FORMATS is not None:
            args['image_formats'] = app_settings.ALLOWED_AVATAR_FORMATS
        if app_settings.MAX_AVATAR_DIMENSIONS is not None:
            args['max_width'] = app_settings.MAX_AVATAR_DIMENSIONS[0]
            args['max_height'] = app_settings.MAX_AVATAR_DIMENSIONS[1]
        args.update(kwargs)
        return ImageURLField(**args)
    else:
        return field.formfield(**kwargs)

class ImageURLField(forms.URLField):
    """
    A URL field specifically for images, which can validate details
    about the filesize, dimensions and format of an image at a given
    URL.

    Specifying any of the following arguments will result in the
    appropriate validation of image details, retrieved from the URL
    specified in this field:

    max/min_filesize
        An integer specifying an image filesize limit, in bytes.

    max/min_width
        An integer specifying an image width limit, in pixels.

    max/min_height
        An integer specifying an image height limit, in pixels.

    image_formats
        A list of image formats to be accepted, specified as uppercase
        strings.

        For a list of valid image formats, see the "Image File Formats"
        section of the `Python Imaging Library Handbook`_.

    .. _`Python Imaging Library Handbook`: http://www.pythonware.com/library/pil/handbook/
    """
    def __init__(self, max_filesize=None, min_filesize=None, max_width=None,
        min_width=None, max_height=None, min_height=None, image_formats=None,
        *args, **kwargs):
        super(ImageURLField, self).__init__(*args, **kwargs)
        self.max_filesize, self.min_filesize = max_filesize, min_filesize
        self.max_width, self.min_width = max_width, min_width
        self.max_height, self.min_height = max_height, min_height
        self.image_formats = image_formats
        self.validate_image = \
            max_filesize is not None or min_filesize is not None or \
            max_width is not None or min_width is not None or \
            max_height is not None or min_height is not None or \
            image_formats is not None

    def clean(self, value):
        value = super(ImageURLField, self).clean(value)
        if value == u'' or not self.validate_image:
            return value
        try:
            filesize, dimensions, format = self._get_image_details(value)
            if dimensions is None or format is None:
                raise forms.ValidationError(
                    'Could not retrieve image details from this URL.')
            if self.max_filesize is not None and filesize > self.max_filesize:
                raise forms.ValidationError(
                    u'The image at this URL is %s large - it must be at most %s.' % (
                        filesizeformat(filesize), filesizeformat(self.max_filesize)))
            if self.min_filesize is not None and filesize < self.min_filesize:
                raise forms.ValidationError(
                    u'The image at this URL is %s large - it must be at least %s.' % (
                        filesizeformat(filesize), filesizeformat(self.min_filesize)))
            if self.max_width is not None and dimensions[0] > self.max_width:
                raise forms.ValidationError(
                    u'The image at this URL is %s pixels wide - it must be at most %s pixels.' % (
                        dimensions[0], self.max_width))
            if self.min_width is not None and dimensions[0] < self.min_width:
                raise forms.ValidationError(
                    u'The image at this URL is %s pixels wide - it must be at least %s pixels.' % (
                        dimensions[0], self.min_width))
            if self.max_height is not None and dimensions[1] > self.max_height:
                raise forms.ValidationError(
                    u'The image at this URL is %s pixels high - it must be at most %s pixels.' % (
                        dimensions[1], self.max_height))
            if self.min_height is not None and dimensions[1] < self.min_height:
                raise forms.ValidationError(
                    u'The image at this URL is %s pixels high - it must be at least %s pixels.' % (
                        dimensions[1], self.min_height))
            if self.image_formats is not None and format not in self.image_formats:
                raise forms.ValidationError(
                    u'The image at this URL is in %s format - %s %s.' % (
                        format,
                        len(self.image_formats) == 1 and u'the only accepted format is' or 'accepted formats are',
                        get_text_list(self.image_formats)))
        except IOError:
            raise forms.ValidationError(u'Could not load an image from this URL.')
        return value

    def _get_image_details(self, url):
        """
        Retrieves details about the image accessible at the given URL,
        returning a 3-tuple of (filesize, image dimensions (width,
        height) and image format), or (filesize, ``None``, ``None``) if
        image details could not be determined.

        The Python Imaging Library is used to parse the image in chunks
        in order to determine its dimension and format details without
        having to load the entire image into memory.

        Adapted from http://effbot.org/zone/pil-image-size.htm
        """
        file = urllib.urlopen(url)
        filesize = file.headers.get('content-length')
        if filesize: filesize = int(filesize)
        p = ImageFile.Parser()
        while 1:
            data = file.read(1024)
            if not data:
                break
            p.feed(data)
            if p.image:
                return filesize, p.image.size, p.image.format
                break
        file.close()
        return filesize, None, None
