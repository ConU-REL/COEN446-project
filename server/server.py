# Imports
import socket, select, sys, queue
import threading
import logging
import npyscreen

# create the socket
srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# set socket to non-blocking
srv.setblocking(0)
# bind to localhost at port 8888
srv.bind(('localhost', 8888))
# accept up to 5 connections
srv.listen(5)

re = [srv]
wr = []
conn_q = {}
send_q = {}

quit = False

logging.basicConfig(level=logging.INFO)

def main():
    # TCP loop
    while True:
        # exit if requested (threading)
        if quit:
            logging.info(quit)
            # close all sockets when exiting
            for sock in re:
                sock.close()
            for sock in wr:
                sock.close()
            logging.info("Sockets closed, exiting listen thread")
            break

        # get lists with sockets that are redy to be worked on
        socks_read, socks_write, socks_err = select.select(
            re, wr, re
        )

        # iterate over sockets that are ready to be read
        for sock in socks_read:
            # if the server socket is in the list, a new connection req was received
            if sock is srv:
                # accept the new conn
                new_conn, addr = sock.accept()
                # set conn to non-blocking
                new_conn.setblocking(0)
                # append conn to socket list
                re.append(new_conn)
                # create a matching queue in the queue dict
                conn_q[new_conn] = queue.Queue()
            # for non-server sockets in the list
            else:
                # receive 1024 bits from socket
                msg = sock.recv(1024)
                # check if data received
                if msg:
                    # add data to appripriate queue
                    conn_q[sock].put(msg)
                    logging.info('Message received. Contents: ' + msg.decode('utf-8'))
                    # if the socket isn't in the writable list, add it
                    if sock not in wr:
                        wr.append(sock)
                # if we read 0 bytes, terminate the connection
                else:
                    # remove socket from writeable list if it's there
                    if sock in wr:
                        wr.remove(sock)
                    # remove socket from readable list
                    re.remove(sock)
                    # close the socket
                    sock.close()
                    # delete the queue associated with that socket
                    del conn_q[sock]
                    # delete the send queue associated with that socket
                    if sock in send_q:
                        del send_q[sock]

        # iterate over sockets that are ready to be written to
        for sock in socks_write:
            # check if there is a send queue for the socket
            if sock in send_q:
                try:
                    # try to pull a message from the send queue
                    msg = send_q[sock].get_nowait()
                except queue.Empty:
                    # if the send queue is empty, delete the queue
                    del send_q[sock]
                    # delete the send queue associated with that socket
                    if sock in send_q:
                        del send_q[sock]
                else:
                    # send any messages that are ready for that connection
                    srv.sendall(msg.encode('utf-8'))
        
        #iterate over sockets with errors
        for sock in socks_err:
            # remove socket from writeable list if it is there
            if sock in wr:
                wr.remove(sock)
            # remove socket from readable list
            re.remove(sock)
            # close the socket
            sock.close()
            # delete the queue associated with that socket
            del conn_q[sock]
            # delete the send queue associated with that socket
            if sock in send_q:
                del send_q[sock]

    return

class ServerApp(npyscreen.NPSAppManaged):
    tcp_thread = threading.Thread(target=main, daemon=True)
    def onStart(self):
        self.value = None
        self.tcp_thread.start()
        logging.info("Thread Started")
        self.addForm("MAIN", MainForm)


class MainForm(npyscreen.Form):
    OK_BUTTON_TEXT = "Exit"

    def create(self):
        self.keypress_timeout = 1
        # self.keypress_timeout_default = 5
        self.recv_log = self.add(npyscreen.Pager, name="Received Message Log", editable=False)
        # btn_ = npyscreen.ButtonPress
        # btn_send.whenPressed = self.send_msg
        # self.add(btn_send, name="Send Message")

    def update_log(self, msg=None):
        self.max_size = 10
        if(len(self.recv_log.values) >= self.max_size):
            self.recv_log.values.pop()
        self.recv_log.values = [msg] + self.recv_log.values
        self.recv_log.display()
        logging.info("List updated")
    
    def while_waiting(self):
        for sock in conn_q:
            try:
                msg = conn_q[sock].get_nowait()
            except queue.Empty:
                continue

            self.update_log(msg.decode('utf-8'))


    # called when exit button is pressed
    def afterEditing(self):
        logging.info("After Editing")
        global quit
        #quit = True
        self.parentApp.setNextForm(None)


if __name__ == "__main__":
    TA = ServerApp()
    TA.run()