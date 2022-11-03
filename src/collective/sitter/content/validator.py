from .. import _
from plone.namedfile.interfaces import INamedBlobImageField
from z3c.form import validator
from z3c.form.interfaces import NOT_CHANGED
from zope.interface import Invalid


# https://widerin.net/blog/image-filesize-validator-for-dexterity-content-types-in-plone

# 2 MB size limit
MAXSIZE = 1024 * 1024 * 2


class ImageFileSizeValidator(validator.FileUploadValidator):
    def validate(self, value):
        super().validate(value)

        if value not in (None, NOT_CHANGED) and value.getSize() > MAXSIZE:
            msg = self.context.translate(
                _(
                    'Image is too large - it must be lower than ${size}MB',
                    mapping=dict(size=MAXSIZE / 1024 / 1024),
                )
            )
            raise Invalid(msg)


validator.WidgetValidatorDiscriminators(
    ImageFileSizeValidator, field=INamedBlobImageField
)
