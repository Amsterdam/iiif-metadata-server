class MockResponse:
    def __init__(self, json_data, status_code, *, content=None, headers=None):
        super().__init__()
        self.json_data = json_data
        self.status_code = status_code
        self.content = content
        self.headers = headers

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if self.status_code != 200:
            raise Exception("Error")