
from pywikibot import family

class Family(family.Family):
    name = 'metakgp'
    langs = {
        'en': 'wiki.metakgp.org',
    }

    def scriptpath(self, code):
        return '/w'

    def protocol(self, code):
        return 'https'
