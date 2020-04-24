import npyscreen, queue
import json, time
from MQTT_Client import MQTT_Client

# for debugging
import logging


# create the queue for received messages:
msgs = queue.Queue()

# create the MQTT client instance with the default
# parameters since we're connecting to a server on the localhost
# and default port

mqtt = MQTT_Client()
topic = "event_db"

# set the logging level
logging.basicConfig(level=logging.INFO)

presence = []

# create the UI instance
class ClientApp(npyscreen.NPSAppManaged):
    def onStart(self):
        self.registerForm("MAIN", DoorLockerForm())


class DoorLockerForm(npyscreen.Form):
    OK_BUTTON_TEXT = "Exit (Ctrl + C)"

    def __init__(self, *args, **kwargs):
        super(DoorLockerForm, self).__init__(*args, **kwargs)
        # add a keyboard shortcut to exit
        self.add_handlers({"^C": self.disable_editing})

    def while_waiting(self):
        """While the user isn't actively moving around the form, update stuff"""
        # check if connection closed
        if not mqtt.connected:
            self.disconnect()

    def arrives(self):
        """If command is someone arrived"""
        self.submit(0)

    def leaves(self):
        """If command is someone left"""
        self.submit(1)

    def submit(self, instr, name=None):
        """Send the message to the broker"""
        # check connected
        if mqtt.connected:
            # use param or use UI entry fields?
            if not name is None:
                user = name
            else:
                user = self.user.value
            msg = {}
            # check user isn't blank
            if not (user in ["", " "]):
                msg["name"] = user
                # get instruction
                if not instr:
                    msg["instr"] = "arrives"
                else:
                    msg["instr"] = "leaves"
                # publish
                mqtt.publish(topic, json.dumps(msg))
            else:
                # bad input
                npyscreen.notify_confirm("Input is not acceptable", title="Bad Input")
        else:
            # not connected
            npyscreen.notify_confirm(
                "Please connect to broker before submitting",
                title="Can't Submit, Not Connected",
            )

    def load(self):
        """Load a JSON file for testing"""
        # choose file
        file = npyscreen.selectFile(must_exist=True, confirm_if_exists=False)

        # open file
        with open(file, "r") as file:
            # try to get data
            try:
                self.test = json.load(file)["test"]
                # show "start test" button
                self.btn_start.hidden = False
                # update UI
                self.display()

            except (json.JSONDecodeError, KeyError):
                # bad file
                npyscreen.notify_confirm(
                    "Error in JSON file, please fix and retry.", title="JSON Error"
                )
                return

    def start_test(self):
        """Start a test"""
        # check connected
        if mqtt.connected:
            # execute commands
            for cmd in self.test:
                # if delay command
                if cmd[0] == "delay":
                    # verify it is int
                    try:
                        delay = int(cmd[1])
                    except ValueError:
                        # bad data
                        npyscreen.notify_confirm(
                            "Error in JSON file, please fix and retry.",
                            title="JSON Error",
                        )
                        return
                    # set limits on delay length
                    if delay <= 10 and delay >= 1:
                        # delay
                        time.sleep(delay)
                # if arrive or leave
                else:
                    instr = None
                    if cmd[0].lower() == "arrives":
                        instr = False
                    elif cmd[0].lower() == "leaves":
                        instr = True

                    # send data
                    self.submit(instr, cmd[1])
        else:
            # not connected
            npyscreen.notify_confirm(
                "Please connect to broker before starting test",
                title="Can't Start Test, Not Connected",
            )
            return

    def disable_editing(self, *args, **keywords):
        """Helper to disable editing (quit)"""
        self.editing = False

    def connect(self):
        """Connect to the MQTT broker"""
        self.status.value = "Connecting"
        self.display()
        # try to connect
        conn = mqtt.connect(msgs)
        # if successful
        if conn == 0:
            # update UI
            self.status.value = "Connection Successful"
            self.btn_conn.name = "Disconnect"
            self.btn_conn.whenPressed = self.disconnect
            self.display()
            return 0
        # if unsucessful
        elif conn == 1:
            # update UI
            self.status.value = "Connection Failed. Check Broker Status"
            self.display()
            return 1

    def disconnect(self):
        """Disconnect from the MQTT broker"""
        # disconnect
        conn = mqtt.disconnect()
        if not conn:
            # update UI
            self.btn_conn.name = "Connect"
            self.btn_conn.whenPressed = self.connect
            self.status.value = "Disconnected"
            self.display()

    def afterEditing(self):
        """Called when exiting"""
        # disconnect before exiting
        mqtt.disconnect()
        self.parentApp.setNextForm(None)

    def create(self):
        """Create the UI elements"""
        self.keypress_timeout = 1

        # add title text
        self.add(
            npyscreen.TitleText,
            name="Smart Door Locker Console",
            editable=False,
            rely=0,
        )

        # add btn label
        self.label_btn_conn = self.add(
            npyscreen.TitleText,
            name="Connect to broker:",
            editable=False,
            relx=3,
            rely=2,
        )

        # add connect button
        self.btn_conn = self.add(
            npyscreen.ButtonPress,
            name="Connect",
            relx=22,
            rely=self.label_btn_conn.rely,
        )

        # add text asking for name
        self.title_user = self.add(
            npyscreen.TitleText, name="Name:", relx=3, rely=4, editable=False
        )

        # add name entry field
        self.user = self.add(
            npyscreen.Textfield, name="Name", relx=23, rely=self.title_user.rely,
        )

        # add arrive btn
        self.btn_arrive = self.add(
            npyscreen.ButtonPress, name="Arrives", relx=15, rely=self.user.rely + 2,
        )

        # add leave button
        self.btn_leave = self.add(
            npyscreen.ButtonPress, name="Leaves", relx=25, rely=self.btn_arrive.rely,
        )

        self.nextrely += 1
        # add info text
        self.add(
            npyscreen.TitleText,
            name="If you prefer, you can also load a test file and send it "
            "using the button below.",
            editable=False,
        )

        # add load btn
        self.btn_load = self.add(npyscreen.ButtonPress, name="Load Test")
        self.nextrely -= 1
        self.nextrelx += 15
        # add start btn
        self.btn_start = self.add(npyscreen.ButtonPress, name="Start Test", hidden=True)

        # add status text
        self.status = self.add(
            npyscreen.TitleText, name="Status:", value="Idle", editable=False, rely=-3
        )

        # assign button actions
        self.btn_conn.whenPressed = self.connect
        self.btn_arrive.whenPressed = self.arrives
        self.btn_leave.whenPressed = self.leaves

        self.btn_load.whenPressed = self.load
        self.btn_start.whenPressed = self.start_test

        # update UI
        self.display()


if __name__ == "__main__":
    TA = ClientApp()
    TA.run()
