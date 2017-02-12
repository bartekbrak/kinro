from django.db import models


class ColorField(models.CharField):
    """A whole fucking class so that I can change admin widget easily. Thanks Obama."""
