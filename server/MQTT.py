from Message import *


class MQTT:
    """Class containing methods for MQTT processes"""

    def process_msg(self, msg):
        """Process received message"""
        header, content = msg.split(" ... ", 1)
        msg = list(header, content)
        frame_type = Frame.frame_types[header]

        if frame_type == 1:
            return ConnectFrame(msg)
        elif frame_type == 3:
            return DiscFrame(msg)
        elif frame_type == 4:
            return DataFrame(msg)
