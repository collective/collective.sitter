from ..sitterstate import SitterState


class SitterStateView(SitterState):
    def __init__(self, context, request):
        super().__init__(context)
