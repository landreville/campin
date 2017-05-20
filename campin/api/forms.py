from datetime import datetime

from formencode import Schema, FancyValidator, Invalid
from formencode.validators import Int, UnicodeString


class DateValidator(FancyValidator):
    """Convert value to datetime."""
    format = '%Y-%m-%d'

    def to_python(self, value, state):
        try:
            date_value = datetime.strptime(value, self.format)
        except ValueError:
            # This depends on format class attribute.
            raise Invalid('Date must be in format YYYY-MM-DD.', value, state)
        return date_value


class DateAfterDateValidator(FancyValidator):
    """Ensure that a date in one field is after a date in another field."""

    def __init__(self, before_date_field, after_date_field, *args, **kwargs):
        """
        :param before_date_field: Name of earlier date field. 
        :param after_date_field: Name of later date field.
        """
        super().__init__(*args, **kwargs)
        self._before_date_field = before_date_field
        self._after_date_field = after_date_field

    def validate_python(self, value_dict, state):
        before_field = value_dict[self._before_date_field]
        after_field = value_dict[self._after_date_field]

        if after_field < before_field:
            raise Invalid(
                '{} must be a date after {}.'.format(
                    self._after_date_field,
                    self._before_date_field
                ),
                value_dict,
                state,
            )


class SearchSchema(Schema):
    """Search schema for searching campsites and parks."""
    start_date = DateValidator(not_empty=True)
    end_date = DateValidator(not_empty=True)
    drive_hours = Int(if_missing=0)
    from_place = UnicodeString(if_missing=None)

    chained_validators = [DateAfterDateValidator('start_date', 'end_date')]
