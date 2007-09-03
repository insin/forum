import StringIO
import urllib

from django import newforms as forms
from django.template.defaultfilters import filesizeformat

from forum import app_settings
from PIL import ImageFile

class ForumProfileBaseForm(forms.BaseForm):
    """
    Implements overkill validation of user avatars.
    """
    def clean_avatar(self):
        if 'avatar' in self.cleaned_data and \
           (app_settings.MAX_AVATAR_FILESIZE is not None or \
            app_settings.ALLOWED_AVATAR_FORMATS is not None or \
            app_settings.MAX_AVATAR_DIMENSIONS is not None):
            try:
                filesize, dimensions, format = self._get_avatar_details(self.cleaned_data['avatar'])
                if (app_settings.ALLOWED_AVATAR_FORMATS is not None and format is None) or \
                   (app_settings.MAX_AVATAR_DIMENSIONS is not None and dimensions is None):
                    raise forms.ValidationError(u'The specified avatar could not be found or was not a valid image.')
                if app_settings.MAX_AVATAR_FILESIZE is not None and \
                   filesize > app_settings.MAX_AVATAR_FILESIZE:
                        raise forms.ValidationError(u'Avatars may not be larger than %s.' \
                                                    % filesizeformat(app_settings.MAX_AVATAR_FILESIZE))
                if app_settings.ALLOWED_AVATAR_FORMATS is not None and \
                   format not in app_settings.ALLOWED_AVATAR_FORMATS:
                    raise forms.ValidationError(u'%s avatars are not permitted - the following image formats may be used: %s' \
                                % (format, u', '.join(app_settings.ALLOWED_AVATAR_FORMATS)))
                if app_settings.MAX_AVATAR_DIMENSIONS is not None and \
                   dimensions > app_settings.MAX_AVATAR_DIMENSIONS:
                        raise forms.ValidationError(u'Avatars may not be greater than %spx wide or %spx tall.' \
                                                    % app_settings.MAX_AVATAR_DIMENSIONS)
            except IOError, e:
                raise forms.ValidationError(u'The specified avatar could not be found or was not a valid image.')
        return self.cleaned_data['avatar']

    def _get_avatar_details(self, url):
        """
        Returns a 3-tuple of (file size, image dimensions, image format)
        for the image at the given url.
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
