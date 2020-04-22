# Imports
import socket, select, sys, queue
import logging
import Message

logging.basicConfig(level=logging.INFO)


def client_thread(stop, sock, recv_q, send_q):
    cl = sock
    # TCP loop
    while True:
        if stop():
            if(not cl._closed):
                cl.close()
            # logging.info("Thread closing")
            return 0

        # get lists with sockets that are redy to be worked on
        socks_read, socks_write, socks_err = select.select([cl], [cl], [cl], 0.5)

        # iterate over sockets that are ready to be read
        if socks_read:
            sock = socks_read[0]
            try:
                msg = sock.recv(1024)
                # check if data received
                if msg:
                    # add data to appropriate queue
                    recv_q.put(msg)
                    # logging.info("Message received. Contents: " + msg.decode("utf-8"))
                # if we read 0 bytes, terminate the connection
                else:
                    # close the socket
                    #sock.close()
                    return 1
            except ConnectionResetError:
                pass

        # try to send any/all messages in the queue
        while True:
            if not socks_write:
                break
            sock = socks_write[0]
            try:
                # try to pull a message from the send queue
                message = send_q.get_nowait()
                # if there is a message and that socket is still writeable, send it
                
                sock.sendall(message.encode("utf-8"))
                logging.info("Message being sent.")

            except queue.Empty:
                # if queue is empty, break
                break

        # iterate over sockets with errors
        if socks_err:
            # close the socket
            socks_err[0].close()
            return 1
    if(not cl._closed):
        cl.close()
    return 0
