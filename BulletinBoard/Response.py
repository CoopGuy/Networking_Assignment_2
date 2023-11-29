class Response:
    statusCodes = {
        0: "OK",
        1: "Failed"
    }
        
    OK = 0
    FAILED = 1
    
    def __init__(self, status, msg = None):
        self.status = status
        if msg == None:
            self.msg = self.statusCodes[status]
        else:
            self.msg = msg
    
    def is_OK(self):
        return self.status == 0