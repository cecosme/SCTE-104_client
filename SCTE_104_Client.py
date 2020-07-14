#!/usr/bin/python3
'''
	2020-02-25 RJO MTL
	API SCTE-104 for HD492 iCap
'''

import asyncio
import socket
import sys
from time import sleep, gmtime

#[SCTE-104 PARAMETROS]#########################################################

#Parametros Globais Mutáveis
opID = b'\x00\x00'                      #0x0000
messageSize = b'\x00\x00'               #0x0000
message_number = b'\x00'                #0x00

data_length = b'\x00'                   #0x00
splice_insert_type = b'\x00'            #0x00
splice_event_id = b'\x00\x00\x00\x00'   #0x00000000
unique_program_id = b'\x00'             #0x00
break_duration = b'\x00\x00'            #0x0000

#Parametros Globais Imutáveis
result = b'\xff\xff'                    #0xffff
result_extension = b'\xff\xff'          #0xffff
protocol_version = b'\x00'              #0x00
AS_index = b'\x00'                      #0x00
DPI_PID_index = b'\x00\x00'             #0x0000

Reserved = b'\xff\xff'                  #0xffff
SCTE35_protocol_version = b'\x00'       #0x00
timestamp = b'\x00'                     #0x00
num_ops = b'\x01'                       #0x01
pre_roll_time = b'\x75\x30'             #0x7530 = 30000 decimal = 30s
avail_num = b'\x00'                     #0x00
avails_expected = b'\x00'               #0x00
auto_return_flag = b'\x01'              #0x01

#[SCTE-104 PARAMETROS]#########################################################

#[PARAMETROS DA CONEXAO]#######################################################

injc_ip = '127.0.0.1'
injc_port = 5167

#[PARAMETROS DA CONEXAO]#######################################################

#[FUNCTIONS]###################################################################

def incrementar_one_byte(val_hex):

    if val_hex == b'\xff':
        return b'\x00'
    
    else:
        val_int = (int.from_bytes(val_hex, byteorder='big') ) + 1
        return val_int.to_bytes(1, byteorder='big')

def incrementar_dois_bytes(val_hex):

    if val_hex == b'\xff\xff':
        return b'\x00\x00'
    
    else:
        val_int = (int.from_bytes(val_hex, byteorder='big') ) + 1
        return val_int.to_bytes(2, byteorder='big')

def incrementar_quatro_bytes(val_hex):

    if val_hex == b'\xff\xff\xff\xff':
        return b'\x00\x00\x00\x00'
    
    else:
        val_int = (int.from_bytes(val_hex, byteorder='big') ) + 1
        return val_int.to_bytes(4, byteorder='big')

async def keep_alive(sock):
    while True:
        #Mensagem ALIVE_REQUEST_DATA
        opID = b'\x00\x03'
        messageSize = b'\x00\x00'
        global message_number
        message_number = incrementar_one_byte(message_number)
        message = opID + messageSize + result + result_extension + protocol_version + AS_index + message_number + DPI_PID_index     #falta calcular o messageSize
        messageSize = len(message).to_bytes(2, byteorder='big')
        message = opID + messageSize + result + result_extension + protocol_version + AS_index + message_number + DPI_PID_index     #mensagem final concluída
        print('Mensagem enviada ALIVE_REQUEST_DATA = ', message.hex())

        try:
            sock.sendall(message)
            data = sock.recv(256)
            if data[:2] == b'\x00\x04':
                print('Mensagem recebida ALIVE_RESPONSE_DATA = ', data.hex() , '\n')
                #talvez aqui implementar um decoder de mensagens

        except socket.timeout as e:
            print('Timeout ALIVE_REQUEST_DATA: ', e, '\n') 

        finally:
            #Enviando keep alive a cada 40s
            await asyncio.sleep(40) 

async def cmd_splice(sock):

    print('Conectando com o Deck ...')
    sock02 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock02.settimeout(3)
    sock02.connect((injc_ip, injc_port))
    data = sock02.recv(256)
    print('Conectado ao Deck. \n', data.decode('ascii'))

    #Parar o clip
    message = 'stop' + '\r\n'
    print('Comando enviado: ', message)
    sock02.sendall(message.encode('ascii'))
    data = sock02.recv(256)
    print('Resposta recebida: \n', data.decode('ascii'))

    #Posicionar no inicio do clip
    message = 'goto: timeline: start' + '\r\n'
    print('Comando enviado: ', message)
    sock02.sendall(message.encode('ascii'))
    data = sock02.recv(256)
    print('Resposta recebida: \n', data.decode('ascii'))



    while True:
        # preciso acessar essas variaveis globais
        global message_number
        global splice_event_id
        global unique_program_id
        # vamos fazer splicing CUE OUT em todo segundo 20 e splicing CUE IN em todo segundo 35. Sinalizarei com 15s de antecedencia um Ad de 10s.
        if gmtime().tm_sec == 5:
            #do splicing CUE OUT
            print('TIME TO CUE OUT')


            opID = b'\x01\x01'
            splice_insert_type = b'\x01'
            messageSize = b'\x00\x00'
            message_number = incrementar_one_byte(message_number)
            splice_event_id = incrementar_quatro_bytes(splice_event_id)
            unique_program_id = incrementar_dois_bytes(unique_program_id) #ESTOU USANDO DOIS BYTES. NA CAPTURA ERA UM BYTE!!!
            pre_roll_time = b'\x3a\x98'
            break_duration = b'\x00\x96'    # 150 = 15s de Ad
            avail_num =  b'\x00'
            avails_expected =  b'\x00'
            auto_return_flag = b'\x01'

            timestamp = b'\x00'
            #preparar o pacote de dados e calcular seu tamanho. ESTOU LIMITANDO O DATA_LENGTH EM 0xff BYTES.
            datapackage = splice_insert_type + splice_event_id + unique_program_id + pre_roll_time + break_duration + avail_num + avails_expected + auto_return_flag
            data_length = len(datapackage).to_bytes(2, byteorder='big')
            #anexar a pacote de dados ao cabeçalho criando a mensagem
            message = Reserved + messageSize + protocol_version + AS_index + message_number + DPI_PID_index + SCTE35_protocol_version + timestamp + num_ops + opID + data_length + datapackage
            #calcular o tamanho da mensagem antes de enviar
            messageSize = len(message).to_bytes(2, byteorder='big')
            #mensagem final concluída
            message = Reserved + messageSize + protocol_version + AS_index + message_number + DPI_PID_index + SCTE35_protocol_version + timestamp + num_ops + opID + data_length + datapackage


            print('Mensagem enviada SPLICE_START_NORMAL = ', message.hex())

            try:
                sock.sendall(message)
                data = sock.recv(256)
                if data[:2] == b'\x00\x07':
                    print('Mensagem recebida INJECT_RESPONSE_DATA = ', data.hex() , '\n')
                    #talvez aqui implementar um decoder de mensagens

            except socket.timeout as e:
                print('Timeout ALIVE_REQUEST_DATA: ', e, '\n')
                #escrever o que fazer quando ocorrer timeout 

            finally:
                await asyncio.sleep(1)  #importante para pular o segundo ja capturado     

        elif gmtime().tm_sec == 30:
            #do splicing CUE IN
            print('TIME TO CUE IN')

            opID = b'\x01\x01'
            splice_insert_type = b'\x03'
            messageSize = b'\x00\x00'
            message_number = incrementar_one_byte(message_number)
            splice_event_id = incrementar_quatro_bytes(splice_event_id)
            #unique_program_id = incrementar_dois_bytes(unique_program_id) #ESTOU USANDO DOIS BYTES. NA CAPTURA ERA UM BYTE!!!
            pre_roll_time = b'\x13\x88'
            break_duration = b'\x00\x00'
            avail_num = b'\x00'
            avails_expected = b'\x00' 
            auto_return_flag = b'\x01'

            timestamp = b'\x00'
            print(timestamp)
            #preparar o pacote de dados e calcular seu tamanho. ESTOU LIMITANDO O DATA_LENGTH EM 0xff BYTES.
            datapackage = splice_insert_type + splice_event_id + unique_program_id + pre_roll_time + break_duration + avail_num + avails_expected + auto_return_flag
            data_length = len(datapackage).to_bytes(2, byteorder='big')
            #anexar a pacote de dados ao cabeçalho criando a mensagem
            message = Reserved + messageSize + protocol_version + AS_index + message_number + DPI_PID_index + SCTE35_protocol_version + timestamp + num_ops + opID + data_length + datapackage
            #calcular o tamanho da mensagem antes de enviar
            messageSize = len(message).to_bytes(2, byteorder='big')
            #mensagem final concluída
            message = Reserved + messageSize + protocol_version + AS_index + message_number + DPI_PID_index + SCTE35_protocol_version + timestamp + num_ops + opID + data_length + datapackage


            print('Mensagem enviada SPLICE_END_NORMAL = ', message.hex())

            try:
                sock.sendall(message)
                data = sock.recv(256)
                if data[:2] == b'\x00\x07':
                    print('Mensagem recebida INJECT_RESPONSE_DATA = ', data.hex() , '\n')
                    #talvez aqui implementar um decoder de mensagens

            except socket.timeout as e:
                print('Timeout ALIVE_REQUEST_DATA: ', e, '\n')
                #escrever o que fazer quando ocorrer timeout 

            finally:
                await asyncio.sleep(1)  #importante para pular o segundo ja capturado  
        
        else:
            await asyncio.sleep(0.3)    #para manter esta coroutine ocupada verificando se ja é o segundo desejado

#[FUNCTIONS]###################################################################



# Create a socket [TCP = socket.SOCK_STREAM  UDP = socket.SOCK_DGRAM]
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    
    print('Iniciando conexão...')
    sock.settimeout(3)
    sock.connect((injc_ip, injc_port))
    #sock.settimeout(None)

#Tratar ausencia do servidor
except ConnectionRefusedError as e:
    print ('Conexao recusada: ' , e, '\n')

#Tratar possivel nao resposta do servidor
except socket.timeout as e:
    print('Timeout: ', e, '\n')

#Tratar tds outras possibilidades de erro
except Exception as e:
    print('Erro: ', e, '\n')

#Socket TCP conectado. Iniciar fase de Handshaking SCTE-104
else:
    
    #Mensagem INIT_REQUEST_DATA
    opID = b'\x00\x01'
    messageSize = b'\x00\x00'
    message_number = incrementar_one_byte(message_number)
    message = opID + messageSize + result + result_extension + protocol_version + AS_index + message_number + DPI_PID_index     #falta calcular o messageSize
    messageSize = len(message).to_bytes(2, byteorder='big')
    message = opID + messageSize + result + result_extension + protocol_version + AS_index + message_number + DPI_PID_index     #mensagem final concluída
    #sleep(1)
    sock.sendall(message)
    print('Mensagem enviada INIT_REQUEST_DATA = ', message.hex())

    #Aguardar em até 3s resposta do servidor SCTE-104
    try:
        data = sock.recv(256)
        #apenas para debug
        #print('Mensagem recebida:', data.hex())
        #print('OpID = ', (data[:2]).hex(), '\n')
    
    #Tratar timeout pela ausencia da reposta
    except socket.timeout as e:
        print('Não recebido mensgem INIT_RESPONSE_DATA: ', e, '\n')
    
    #Tratar resposta enviada pela servidor SCTE-104
    else:
        #Analisar reposta recebida durante a fase de Handshaking
        if data[:2] == b'\x00\x02':
            print('Mensagem recebida INIT_RESPONSE_DATA = ', data.hex() , '\n')
            #talvez aqui implementar um decoder de mensagens

            try:
                #Iniciar a criação de CoRoutines
                event_loop = asyncio.get_event_loop()

                asyncio.ensure_future(keep_alive(sock))
                asyncio.ensure_future(cmd_splice(sock))
                event_loop.run_forever()

            except KeyboardInterrupt:
                pass

            finally:
                print('\nFinalizando Event Loop')
                event_loop.close()

        else:
            print('Recebido msg desconhecida: ', data.hex(), '\n')
        
finally:
    print('Closing socket')
    sock.close()
    sleep(1)
