import urllib

from django import newforms as forms
from django.template.defaultfilters import filesizeformat
from django.utils.text import capfirst, get_text_list

from forum import app_settings
from PIL import ImageFile

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
