import json
import logging


class Frame:
    """Frame superclass used to define all message frames"""

    header = "base"

    def __init__(self, message):
        try:
            self.message = dict(json.loads(message))
            # logging.info(f"Message dumped: {self.message}")
            self.header = self.message["header"]
        except json.JSONDecodeError:
            # logging.info(f"JSON error")
            self.header = "error"

    def __str__(self):
        return f"Base (or malformed) Frame"


class ConnectFrame(Frame):
    """Connect frame sent by the client to the broker"""

    def __init__(self, message=None):
        if message is None:
            self.header = "CONNECT"
            self.message = {"header": self.header}
        else:
            super(ConnectFrame, self).__init__(message)

    def __str__(self):
        return f"CONNECT Frame"

    def encode(self):
        return json.dumps(self.message)


class AckFrame(Frame):
    """All the different types of acknowledge frames sent by the broker"""

    def __init__(self, message=None):
        if not message is None:
            super(AckFrame, self).__init__(message)
            try:
                self.content = self.message["content"]
            except json.JSONDecodeError:
                pass

    def compose(self, type, topics=None):
        if type == "connack":
            self.ack_type = "connack"
            self.header = "ACK"
            self.content = ""
            self.message = {"header": self.header, "content": self.content}
        elif type == "suback":
            self.ack_type = "suback"
            self.header = "ACK"
            self.content = "SUB"
            if topics:
                self.topics_return = topics
                self.message = {
                    "header": self.header,
                    "content": self.content,
                    "return": self.topics_return,
                }
            else:
                self.header = "error"
        elif type == "unsuback":
            self.ack_type = "unsuback"
            self.header = "ACK"
            self.content = "UNSUB"
            self.message = {"header": self.header, "content": self.content}

        return self

    def __str__(self):
        return f"ACK Frame of type {self.ack_type}"

    def encode(self):
        return json.dumps(self.message)


class PublishFrame(Frame):
    """Contains data that has been sent to the broker or that is to be sent to subscribers"""

    def __init__(self, message):
        super(PublishFrame, self).__init__(message)
        try:
            self.topic = self.message["topic"]
            self.qos = self.message["qos"]
            self.retain = self.message["retain"]
            self.content = self.message["content"]
        except json.JSONDecodeError:
            self.header = "error"

    def __str__(self):
        return f"Publish Frame. Topic: {self.topic}, Payload: {self.content}"

    def encode(self):
        """Restructure the message for rebroadcasting"""
        self.message = {
            "header": self.header,
            "topic": self.topic,
            "content": self.content,
        }

        return json.dumps(self.message)


class SubscribeFrame(Frame):
    """Subscribe frame used sent to broker by client when it wants to subscribe to topic(s)"""

    def __init__(self, message):
        super(SubscribeFrame, self).__init__(message)
        try:
            self.topics = list(self.message["topics"])
        except json.JSONDecodeError:
            self.header = "error"

    def __str__(self):
        return f"Subscribe Frame. Topics requested: {self.topics}"

    def encode(self):
        return json.dumps(self.message)


class UnsubscribeFrame(Frame):
    """Unsubscribe Frame sent to broker by client when it wants to unsubscribe"""

    def __init__(self, message):
        super(UnsubscribeFrame, self).__init__(message)
        try:
            self.topics = self.message["topic"]
        except json.JSONDecodeError:
            self.header = "error"

    def __str__(self):
        return f"Unsubscribe Frame. Topics requested: {self.topics}"


class DisconnectFrame(Frame):
    """Disconnect Frame sent by client to broker"""

    def __init__(self, message=None):
        if not message is None:
            super(DisconnectFrame, self).__init__(message)
        else:
            self.header = "DISCONNECT"
            self.content = ""
            self.message = {"header":self.header, "content":self.content}

    def __str__(self):
        return f"DISCONNECT Frame"

    def encode(self):
        return json.dumps(self.message)
