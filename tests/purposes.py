from dateutil.relativedelta import relativedelta

from gdpr.purposes.default import AbstractPurpose

# SLUG can be any length up to 100 characters
FIRST_AND_LAST_NAME_SLUG = "FNL"


class FirstNLastNamePurpose(AbstractPurpose):
    """Store First & Last name for 10 years."""
    name = "retain due to internet archive"
    slug = FIRST_AND_LAST_NAME_SLUG
    expiration_timedelta = relativedelta(years=10)
    fields = ("first_name", "last_name")
