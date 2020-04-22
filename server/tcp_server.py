# Imports
import socket, select, sys, queue
import logging

from Message import PublishFrame, AckFrame

# create the socket
srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# set socket to non-blocking
srv.setblocking(0)
# bind to localhost at port 8888
srv.bind(("localhost", 8888))
# accept up to 5 connections
srv.listen(5)

re = [srv]
wr = []

quit = False

logging.basicConfig(level=logging.INFO)

def c_receive(sock):
    parts = []
    bytes_rec = 0
    while bytes_rec < 1024:
        part = sock.recv(min(1024 - bytes_rec, 1024))
        if part == b"":
            return -1
        parts.append(part)
        bytes_rec += len(part)
    return b"".join(parts)

def c_send(msg, sock):
    total = 0
    while total < msg:
        sent = sock.send(msg[total:])
        if sent == 0:
            return -1
        total += sent
    return 0


def server_thread(conn_q, send_q):
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
        socks_read, socks_write, socks_err = select.select(re, wr, re, 0.5)

        # iterate over sockets that are ready to be read
        for sock in socks_read:
            # if the server socket is in the list, a new connection req was received
            if sock is srv:
                logging.info("New Connection")
                # accept the new conn
                new_conn, addr = sock.accept()
                # set conn to non-blocking
                new_conn.setblocking(0)
                # append conn to socket list
                re.append(new_conn)
                # wr.append(new_conn)
            # for non-server sockets in the list
            else:
                # receive 1024 bits from socket
                msg = sock.recv(2048)
                # check if data received
                if msg:
                    # add data to appripriate queue
                    conn_q.put((sock, msg))
                    logging.info("message received")
                    # logging.info("Message received. Contents: " + msg.decode("utf-8"))
                    # if the socket isn't in the writable list, add it
                    if sock not in wr:
                        wr.append(sock)
                # if we read 0 bytes, terminate the connection
                else:
                    logging.info("removing")
                    # remove socket from writeable list if it's there
                    if sock in wr:
                        wr.remove(sock)
                    # remove socket from readable list
                    re.remove(sock)
                    # close the socket
                    sock.close()

        # try to send any/all messages in the queue
        while True:
            if not socks_write:
                break
            try:
                # try to pull a messag-e from the send queue
                (sock, message) = send_q.get_nowait()
                # if there is a message and that socket is still writeable, send it
                if sock in socks_write:
                    sock.sendall(message.encode("utf-8"))
                    logging.info(f"Message being sent: {message}")
                else:
                    send_q.put((sock, message))
            except queue.Empty:
                # if queue is empty, break
                break


        # iterate over sockets with errors
        for sock in socks_err:
            logging.info("error, removing")
            # remove socket from writeable list if it is there
            if sock in wr:
                wr.remove(sock)
            # remove socket from readable list
            re.remove(sock)
            # close the socket
            sock.close()

    return
