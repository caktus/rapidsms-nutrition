from __future__ import unicode_literals
import re


class NutritionPrefixMixin(object):
    """
    A mixin for KeywordHandlers that requires messages begin with a common
    prefix.
    """
    prefix = 'nutrition'
    messages = {}

    @classmethod
    def _keyword(cls):
        """Override the KeywordHandler method to also look for the prefix."""
        if hasattr(cls, 'keyword'):
            args = (cls.prefix, cls.keyword)
            pattern = r'^\s*(?:%s)\s*(?:%s)(?:[\s,;:]+(.+))?$' % args
            return re.compile(pattern, re.IGNORECASE)

    def _respond(self, msg_type, data=None):
        """Retrieve and format a message from self.messages."""
        data = data or {}
        msg = self.messages[msg_type]
        return self.respond(msg.format(**data))

    @property
    def _help_data(self):
        """Fill in help text with the keyword and prefix used by the class."""
        data = {
            'prefix': self.prefix.upper(),
            'keyword': self.keyword.split('|')[0].upper(),
        }
        return data

    def help(self):
        self._respond('help', self._help_data)
