import logging


log = logging.getLogger(__name__)


def registerBehavior_patched(self, **kwargs):
    log.info(f'Dynajet patch: No behavior registered for {self.title}')
    return
