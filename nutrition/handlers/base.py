from __future__ import unicode_literals

import re


class NutritionPrefixMixin(object):
    """A mixin for KeywordHandlers that requires messages begin with a common prefix."""
    prefix = 'nutrition'

    @classmethod
    def _keyword(cls):
        if hasattr(cls, 'keyword'):
            pattern = r'^\s*(?:%s)\s*(?:%s)(?:[\s,;:]+(.+))?$' % (cls.prefix, cls.keyword)
            return re.compile(pattern, re.IGNORECASE)

    @property
    def _help_text(self):
        """Fill in help text with the keyword and prefix used by the class."""
        kwargs = {
            'prefix': self.prefix.upper(),
            'keyword': self.keyword.split('|')[0].upper(),
        }
        return self.help_text.format(**kwargs)

    def help(self):
        self.respond(self._help_text)
