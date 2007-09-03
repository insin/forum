import StringIO
import urllib

from django import newforms as forms

from forum import app_settings
from PIL import Image

class ForumProfileBaseForm(forms.BaseForm):
    def clean_avatar(self):
        if 'avatar' in self.cleaned_data and \
           (app_settings.MAX_AVATAR_DIMENSIONS is not None or \
            app_settings.ALLOWED_AVATAR_FORMATS is not None):
            try:
                image_data = urllib.urlopen(self.cleaned_data['avatar']).read()
            except IOError, e:
                raise forms.ValidationError(u'The specified avatar could not be found: %s' % e)
            else:
                try:
                    image = Image.open(StringIO.StringIO(image_data))
                    if app_settings.ALLOWED_AVATAR_FORMATS is not None and \
                       image.format not in app_settings.ALLOWED_AVATAR_FORMATS:
                        raise forms.ValidationError(u'%s avatars are not permitted - the following image formats may be used: %s' \
                            % (image.format, u', '.join(app_settings.ALLOWED_AVATAR_FORMATS)))
                    if app_settings.MAX_AVATAR_DIMENSIONS is not None:
                        if image.size > app_settings.MAX_AVATAR_DIMENSIONS:
                            raise forms.ValidationError(u'Avatars may not be greater than %spx wide or %spx tall.' \
                                                        % app_settings.MAX_AVATAR_DIMENSIONS)
                except IOError, e:
                    raise forms.ValidationError(u'The specified avatar was not a valid image.')
        return self.cleaned_data['avatar']
