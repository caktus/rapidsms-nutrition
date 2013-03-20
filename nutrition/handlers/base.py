from __future__ import unicode_literals
import re


__all__ = ['NutritionHandlerBase']


class NutritionHandlerBase(object):
    prefix = 'nutrition'  # Common prefix for all Nutrition messages.
    keyword = None
    form_class = None  # Form used to process data.

    _common_messages = {  # Messages common to most or all Nutrition handlers.
        'form_error': 'Sorry, an error occurred while processing your '\
                'message: {message}',

        'error': 'Sorry, an unexpected error occurred while processing your '\
                'message. Please contact your administrator if this '\
                'continues to occur.',
    }
    _messages = {}  # Handler-specific messages.

    @classmethod
    def _colloquial_keyword(cls):
        """If the class has multiple keyword choices, return the first."""
        return cls.keyword.split('|')[0]

    def _get_form(self, data):
        return self.form_class(data, connection=self.connection)

    @classmethod
    def _keyword(cls):
        """Override the KeywordHandler method to also require prefix."""
        args = (cls.prefix, cls.keyword)
        pattern = r'^\s*(?:%s)\s*(?:%s)(?:[\s,;:]+(.+))?$' % args
        return re.compile(pattern, re.IGNORECASE)

    def _parse(self, raw_text):
        """Tokenize message text and return parsed data.

        Raises ValueError if the message cannot be parsed.
        """
        raise NotImplemented('Subclass must define _parse method.')

    def _process(self, parsed):
        """Validate and act upon parsed message data."""
        raise NotImplemented('Subclass must define _process method.')

    def _respond(self, msg_type, **kwargs):
        """Shortcut to retrieve and format a message."""
        data = {  # Some common data.
            'prefix': self.prefix.upper(),
            'keyword': self._colloquial_keyword().upper(),
        }
        data.update(**kwargs)
        if msg_type in self._messages:
            return self.respond(self._messages[msg_type].format(**data))
        if msg_type in self._common_messages:
            return self.respond(self._common_messages[msg_type].format(**data))
        raise KeyError('Message type {0} not found.'.format(msg_type))

    def handle(self, text):
        """
        Entry point of the handler. This method takes care of a few common
        tasks then calls the subclass-specific process method.
        """
        # The reporter will be determined from the message connection.
        self.connection = self.msg.connection
        self.debug('Received {keyword} message from {connection}.'.format(
                keyword=self._colloquial_keyword(), connection=self.connection))

        # Parse the message into its components.
        try:
            parsed = self._parse(text)
        except ValueError as e:
            self.exception()
            self._respond('format_error')
            return
        else:
            data = ', '.join([': '.join((k, v)) for k, v in parsed.items()])
            self.debug('Parsed {keyword} data: {data}'.format(
                    keyword=self._colloquial_keyword(), data=data))

        self._process(parsed)  # Subclasses must process parsed data.

    def help(self):
        self._respond('help')
