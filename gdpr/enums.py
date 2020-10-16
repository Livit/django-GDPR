from __future__ import absolute_import
from enum import IntEnum


class LegalReasonState(IntEnum):
    ACTIVE = 1
    EXPIRED = 2
    DEACTIVATED = 3
