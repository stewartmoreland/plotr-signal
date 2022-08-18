#!/usr/bin/env python3

"""
Marshmallow schema for the plotr_signal package.
"""

from marshmallow import Schema, fields, pre_load, post_load, missing

class BaseSchema(Schema):
    """
    Base schema for all schemas

    This schema is used for all schemas that are used in the API.
    """
    def on_bind_field(self, field_name, field_obj):
        """
        Override the default on_bind_field to add the pre_load and post_load
        """
        if field_obj.missing == missing:
            field_obj.missing = None
