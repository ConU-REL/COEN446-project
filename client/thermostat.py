import npyscreen, queue, time, json

from MQTT_Client import MQTT_Client

# for debugging
import logging


# create the queue for received messages:
msgs = queue.Queue()

# create the MQTT client instance with the default
# parameters since we're connecting to a server on the localhost
# and default port

mqtt = MQTT_Client()

topic_user = "user_db"
topic_event = "event_db"

known_users = {}
home_occupancy = []
prefs_set_by = None
temp = 15

temp_min = 10
temp_max = 25

# set the logging level
logging.basicConfig(level=logging.DEBUG)

# create the UI instance
class ClientApp(npyscreen.NPSAppManaged):
    def onStart(self):
        self.registerForm("MAIN", ThermostatForm())


class ThermostatForm(npyscreen.Form):
    OK_BUTTON_TEXT = "Exit (Ctrl + C)"

    def __init__(self, *args, **kwargs):
        super(ThermostatForm, self).__init__(*args, **kwargs)
        # add a keyboard shortcut to exit
        self.add_handlers({"^C": self.disable_editing})

    def proc_start(self):
        if not self.connect():

            time.sleep(0.5)
            if not mqtt.is_connected():
                npyscreen.notify_confirm(
                    "Something wrong with MQTT broker", title="Unknown MQTT error"
                )
                return
            mqtt.subscribe(topic_user)
            time.sleep(0.5)
            mqtt.subscribe(topic_event)

    def proc_stop(self):
        self.disconnect()

    def while_waiting(self):
        """While the user isn't actively moving around the form, update stuff"""
        if not mqtt.connected:
            self.disconnect()
            self.display()
        else:
            self.update_log()
            global prefs_set_by
            global home_occupancy
            if home_occupancy:
                if prefs_set_by != home_occupancy[0]:
                    prefs_set_by = home_occupancy[0]
                    temp = known_users[home_occupancy[0]]
                    self.temp_changes.values = [
                        (f"Temp set to {temp} because {prefs_set_by} has priority.")
                    ] + self.temp_changes.values
            elif not home_occupancy and prefs_set_by != None:
                prefs_set_by = None
                temp = 15
                self.temp_changes.values = [
                    (f"Temp set to 15 because the house is empty.")
                ] + self.temp_changes.values

            self.display()

    def update_log(self):
        """Update UI elements with new info"""
        try:
            topic, content = msgs.get_nowait()
            logging.info(content)

            if topic == topic_user:
                try:
                    content = dict(json.loads(content))
                    name = content["name"].lower()
                    temp = content["temp"]
                    temp = temp if temp >= temp_min else temp_min
                    temp = temp if temp <= temp_max else temp_max
                except (json.JSONDecodeError, KeyError):
                    pass

                known_users[name] = temp
                self.users.values = []
                for person in known_users:
                    self.users.values.append(f"{person}, {known_users[person]} deg")
                self.users.display()
            elif topic == topic_event:
                try:
                    content = dict(json.loads(content))
                    name = content["name"].lower()
                    action = content["instr"]
                except (json.JSONDecodeError, KeyError):
                    pass

                if action == "arrives":
                    if not name in home_occupancy and name in known_users:
                        home_occupancy.append(name)
                    elif not name in home_occupancy:
                        self.temp_changes.values = [
                            f"A user has arrived but their temperature preference is unknown."
                        ] + self.temp_changes.values
                elif action == "leaves":
                    if name in home_occupancy:
                        home_occupancy.remove(name)
                self.events.values = home_occupancy
                self.events.display()

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
            self.btn_start_stop.whenPressed = self.proc_stop
            self.btn_start_stop.name = "Stop Thermostat Process"
            self.status.value = "Connection Successful"
            self.display()
            return 0
        elif conn == 1:
            self.status.value = "Connection Failed"
            self.status.display()
            npyscreen.notify_confirm(
                "Connection Failed. Check Broker status and then retry.",
                title="Connection Failed",
            )
            return 1

    def disconnect(self):
        """Disconnect from the MQTT broker"""
        conn = mqtt.disconnect()
        if not conn:
            self.status.value = "Idle"
            self.btn_start_stop.whenPressed = self.proc_start
            self.btn_start_stop.name = "Start Thermostat Process"
        else:
            # potential error case here?
            pass

        self.update_log()
        self.display()

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

        self.temp_changes = self.add(
            npyscreen.BoxTitle,
            name="Temperature Changes",
            editable=False,
            relx=2,
            rely=4,
            max_height=8,
        )

        self.users = self.add(
            npyscreen.BoxTitle,
            name="Known Users",
            editable=False,
            relx=2,
            rely=12,
            max_height=8,
            max_width=int(self.temp_changes.width / 2),
        )

        self.events = self.add(
            npyscreen.BoxTitle,
            name="Door Events",
            editable=False,
            relx=self.users.width + 3,
            rely=12,
            max_height=8,
            max_width=self.users.max_width,
        )
        self.add(npyscreen.TitleText, name="Min Temp:", value=temp_min, editable=False, rely=-6)
        self.add(npyscreen.TitleText, name="Max Temp:", value=temp_max, editable=False, rely=-5)

        self.status = self.add(
            npyscreen.TitleText, name="Status:", value="Idle", editable=False, rely=-3
        )

        self.btn_start_stop.whenPressed = self.proc_start
        self.temp_changes.values = [f"Startup. Temperature set to 15 deg"]


if __name__ == "__main__":
    TA = ClientApp()
    TA.run()
