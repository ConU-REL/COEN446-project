class Frame():
    """Frame superclass used to define all message frames"""

    frame_type = "base"
    def __init__(self, message):
        self.header, self.content = message.split(" ... ", 1)


class ConnectFrame(Frame):
    """Connect Frame subclass, sent by client to broker when connection"""
    
    def __init__(self, message):
        super(ConnectFrame, self).__init__(self, message)

        self.frame_type = "connect"
        self.conn_type = self.content.split(" ... ", 1)


class ConnAckFrame(Frame):
    """Connection Acknowledge Frame, sent to client by broker 
    upon successful connection"""

    def __init__(self, conn_type):
        self.message = "ACK ... " + conn_type
        self.frame_type = "connack"

    def encode(self):
        return self.message.encode('utf-8')


class DiscFrame(Frame):
    """Disconnect Frame sent by client to broker"""

    def __init__(self, message):
        super(DiscFrame, self).__init__(self, message)

        self.frame_type = "disconnect"


class DataFrame(Frame):
    """Data Frame used to transmit data unilaterally 
    between client and broker"""

    def __init__(self, message):
        super(DataFrame, self).__init__(self, message)

        self.frame_type = "data"