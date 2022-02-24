import logging


log = logging.getLogger(__name__)


def registerBehavior_patched(self, **kwargs):
    log.info(f'Patch: No behavior registered for {self.title}')
    return
