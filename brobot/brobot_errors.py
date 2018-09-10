class CantDoThatDave(Exception):

    def __init__(self, d_message):
        self.d_message = d_message
