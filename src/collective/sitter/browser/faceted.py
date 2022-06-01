from eea.facetednavigation.interfaces import IWidgetFilterBrains
from zope.annotation.interfaces import IAnnotations
from zope.globalrequest import getRequest
from zope.interface import implementer

import logging
import random


log = logging.getLogger(__name__)

SHUFFLE_KEY = 'sitters_shuffled'


@implementer(IWidgetFilterBrains)
class Shuffle:
    def __init__(self, context):
        self.context = context

    def __call__(self, brains, form):
        request = getRequest()
        annotations = IAnnotations(request)
        shuffled = annotations.get(SHUFFLE_KEY, False)
        if not shuffled:
            annotations[SHUFFLE_KEY] = True
            log.info('Shuffling sitters')
            brains = list(brains)
            random.shuffle(brains, self._get_random_key_from_session)

        yield from brains

    def _get_random_key_from_session(self):
        session = self._get_or_create_session()
        if session is None:
            random_key = random.random()
        elif 'random' in session:
            random_key = session['random']
        else:
            random_key = random.random()
            session['random'] = random_key
        return random_key

    def _get_or_create_session(self):
        try:
            sitterfolder = self.context.context
            sdm = sitterfolder.session_data_manager
        except AttributeError:
            # may occur when testing
            return

        session = sdm.getSessionData(create=True)
        return session
