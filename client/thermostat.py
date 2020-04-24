import npyscreen, queue, time

from MQTT_Client import MQTT_Client

# for debugging
import logging


# create the queue for received messages:
msgs = queue.Queue()

# create the MQTT client instance with the default
# parameters since we're connecting to a server on the localhost
# and default port

mqtt = MQTT_Client()

user_topic = "user_db"
presence_topic = "event_db"

# set the logging level
logging.basicConfig(level=logging.DEBUG)

# create the UI instance
class ClientApp(npyscreen.NPSAppManaged):
    def onStart(self):
        self.registerForm("MAIN", ThermostatForm())


class ThermostatForm(npyscreen.Form):
    OK_BUTTON_TEXT = "Exit"

    def __init__(self, *args, **kwargs):
        super(ThermostatForm, self).__init__(*args, **kwargs)
        # add a keyboard shortcut to exit
        self.add_handlers({"^C": self.disable_editing})

    def proc_start(self):
        if not self.connect():
            self.btn_start_stop.whenPressed = self.proc_stop
            self.btn_start_stop.value = "Stop Thermostat Process"
        
            time.sleep(0.5)
            if not mqtt.is_connected():
                npyscreen.notify_confirm(
                    "Something wrong with MQTT broker", title="Unknown MQTT error"
                )
                return
            mqtt.subscribe(user_topic)
            time.sleep(0.5)
            mqtt.subscribe(presence_topic)

    def proc_stop(self):
        self.disconnect()
        

    def while_waiting(self):
        """While the user isn't actively moving around the form, update stuff"""
        self.update_log()
        if not mqtt.connected:
            self.disconnect()
            self.display()

    def update_log(self):
        """Update UI elements with new info"""
        try:
            self.users.values.append(" ".join(msgs.get_nowait()))
            self.users.display()
        except queue.Empty:
            pass

    def disable_editing(self, *args, **keywords):
        """Helper to disable editing (quit)"""
        self.editing = False

    def connect(self):
        """Connect to the MQTT broker"""
        self.status.value = "Connecting"
        self.status.display()
        conn = mqtt.connect(msgs)
        if conn == 0:
            self.status.value = "Connection Successful"
            self.status.display()
            return 0
        elif conn == 1:
            self.status.value = "Connection Failed"
            self.status.display()
            npyscreen.notify_confirm(
                "Connection Failed. Check Broker status and then retry.", title="Connection Failed"
            )
            return 1

    def disconnect(self):
        """Disconnect from the MQTT broker"""
        conn = mqtt.disconnect()
        if not conn:
            self.status.value = "Idle"
            self.btn_start_stop.whenPressed = self.proc_start
            self.btn_start_stop.value = "Start Thermostat Process"
        else:
            # potential error case here?
            pass

        self.update_log()
        self.display()

    def subscribe(self):
        if not self.topic.value in ["", " "]:
            mqtt.subscribe([self.topic.value])

    def unsubscribe(self):
        if not self.topic.value in ["", " "]:
            mqtt.unsubscribe([self.topic.value])

    def afterEditing(self):
        """Called when exiting"""
        mqtt.disconnect()
        self.parentApp.setNextForm(None)

    def create(self):
        """Create the UI elements"""
        self.keypress_timeout = 1

        self.add(
            npyscreen.TitleText,
            name="Temperature Management Console",
            editable=False,
            rely=0,
        )

        # add connect button
        self.btn_start_stop = self.add(
            npyscreen.ButtonPress, name="Start Thermostat Process", relx=2, rely=2,
        )

        self.users = self.add(
            npyscreen.BoxTitle,
            name="Known Users",
            editable=False,
            relx=2,
            rely=4,
            max_height=8,
            max_width=40,
        )

        self.nextrely += 5
        self.status = self.add(
            npyscreen.TitleText, name="Status:", value="Idle", editable=False
        )

        self.btn_start_stop.whenPressed = self.proc_start


if __name__ == "__main__":
    TA = ClientApp()
    TA.run()
