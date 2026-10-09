from social_django.strategy import DjangoStrategy


class DRFStrategy(DjangoStrategy):
    def __init__(self, storage, request=None, tpl=None):
        self.request = request
        self.session = {}
        super(DjangoStrategy, self).__init__(storage, tpl)

    def get_request_data(self, merge=True):
        if not self.request:
            return {}
        return self.request.data
