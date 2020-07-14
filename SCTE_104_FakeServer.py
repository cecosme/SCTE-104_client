#!/usr/bin/env python3
'''
	2020-02-25 RJO BR
	SCTE 104 Fake Server
'''

import socket
from time import sleep

host = '127.0.0.1'     # The server's hostname or IP address
port = 5167            # The port used by the server

'''
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.bind((host, port))
    sock.listen()
    conn, addr = sock.accept()
    with conn:
        print('Connected by', addr)
        while True:
            data = conn.recv(1024)
            if not data:
                break
            print('Message Received', data)
            #conn.sendall(data)
'''

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

sock.bind((host, port))

try:
    
    while True:
        sock.listen()
        conn, addr = sock.accept()
        print('Connected by', addr)

        while conn:
            data = conn.recv(1024)
            print(data.hex())

            if data:

                if data[:2] == b'\x00\x01':
                    print('Mensagem recebida = INIT_REQUEST_DATA = ', data)
                    msg = b'\x00\x02\x00\x0d\x00\x64\xff\xff\x00\x00\x69\x00\x00'
                    print('Mensagem enviada = INIT_RESPONSE_DATA = ', msg, '\n')
                    conn.sendall(msg)

                elif data[:2] == b'\x00\x03':
                    print('Mensagem recebida = ALIVE_REQUEST_DATA = ', data)
                    msg = b'\x00\x04\x00\x0d\x00\x64\xff\xff\x00\x00\x69\x00\x00'
                    print('Mensagem enviada = ALIVE_RESPONSE_DATA = ', msg, '\n')
                    conn.sendall(msg)                

                elif (data[:2] == b'\xff\xff') and (data[15] == 1):     #mensagem do tipo MULTIPLE e splice_insert_type = SPLICE START NORMAL = 0x01
                    print('Mensagem recebida = SPLICE_START_NORMAL = ', data)
                    msg = b'\x00\x07\x00\x0e\x00\x64\xff\xff\x00\x00\x73\x00\x00\x01'   #a reposta é uma mensagem do tipo SINGLE
                    print('Mensagem enviada = INJECT_RESPONSE_DATA = ', msg, '\n')
                    conn.sendall(msg)  

                elif (data[:2] == b'\xff\xff') and (data[15] == 3):     #mensagem do tipo MULTIPLE e splice_insert_type = SPLICE END NORMAL = 0x03
                    print('Mensagem recebida = SPLICE_END_NORMAL = ', data)
                    msg = b'\x00\x07\x00\x0e\x00\x64\xff\xff\x00\x00\x73\x00\x00\x02'   #a reposta é uma mensagem do tipo SINGLE
                    print('Mensagem enviada = INJECT_RESPONSE_DATA = ', msg, '\n')
                    conn.sendall(msg) 

                else:
                    pass
        conn.close()

except KeyboardInterrupt:
    pass

finally:
    print('\nPrograma finalizado')


    

