import ogins as ins
from . import parse_instruction as pi
import time
import json
import sys
import logging
from websocket_server import WebsocketServer
import threading

action = None
client = False
current_client = None
server = WebsocketServer(8765, host='localhost')


def new_client(nclient, server):
    global client
    global action
    global current_client
#    if client:
 #       return
  #  else:
   #     client = True
    current_client = nclient
    thread = threading.Thread(target=main)
    thread.start()

server.set_fn_new_client(new_client)


def on_command(nclient, server, message):
    global action
    print(message)
    message = json.loads(message)
    if message['type'] == 'stop':
        action = 'halt'
    elif method['type'] == 'pause':
        action = 'pause'
    elif method['type'] == 'resume':
        action = 'resume'
server.set_fn_message_received(on_command)


#def client_left(nclient, server):
 #   global current_client
  #  global client
   # global action
    #if nclient is current_client:
     #   client = False
      #  current_client = None
       # action = 'halt'
        #exit(0)

#server.set_fn_client_left(client_left)

def main():
    global action
    server.send_message_to_all('{"type":"status", "status":"loading"}')
    with open(sys.argv[1] if len(sys.argv) >= 2 else 'openglass.bin', 'rb') as f:
        bytecode = bytearray(f.read())[5:]
    i=0
    screen_msgs = []
    server.send_message_to_all('{"type":"status", "status":"running"}')
    while True:
        opcode = ins.instructions[bytecode[i]]
        i+=1
        arg_count = pi.length_of_args(opcode)
        args = pi.parse_args(opcode, bytecode[i:i+arg_count])
        i += arg_count
        if opcode is ins.POK:
            print(f'POK {args[0]} {args[1]}')
            bytecode[args[1]] = args[0]
        elif opcode is ins.DEL:
            print(f'DEL {args[0]}')
            time.sleep(args[0]/1000)
        elif opcode is ins.LON:
            print(f'LON')
            server.send_message_to_all('{"type":"led", "status":true}')
        elif opcode is ins.LOF:
            print(f'LOF')
            server.send_message_to_all('{"type":"led", "status":false}')
        elif opcode is ins.JMP:
            print(f'JMP {args[0]}')
            i = args[0]-0
        elif opcode is ins.ADB:
            print(f'ADB {args[0]} {args[1]}')
            bytecode[args[0]] = bytecode[args[0]] + args[1]
        elif opcode is ins.SCW:
            print(f'SCW {args[0]} {args[1]}')
            screen_msgs.append(threading.Thread(target=server.send_message_to_all, args=(json.dumps({'type':'screen', 'status':True, 'x':args[0], 'y':args[1]}),)))
        elif opcode is ins.SCB:
            print(f'SCB {args[0]} {args[1]}')
            screen_msgs.append(threading.Thread(target=server.send_message_to_all, args=(json.dumps({'type':'screen', 'status':False, 'x':args[0], 'y':args[1]}),)))
        elif opcode is ins.SCF:
            print(f'SCF')
            for thread in screen_msgs:
                thread.start()
            screen_msgs = []
        elif opcode is ins.JEB:
            print(f'JEB {args[0]} {args[1]} {args[2]}')
            if bytecode[args[1]] == args[2]:
                i = args[0]
                print('jumped')
        elif opcode is ins.HLT:
            print(f'HLT')
            server.send_message_to_all('{"type":"status", "status":"stopped", "reason":"instruction"}')
            exit(0)
        else:
            print(f'Fatal error! Cannot interpret {opcode.name}')
            server.send_message_to_all(json.dumps({'type':'status', 'status':'stopped', 'reason':'bad_known_opcode', 'name':opcode.name}))
            exit(0)
        if action == 'halt':
            server.send_message_to_all('{"type":"status", "status":"stopped", "reason":"request"}')
            exit(0)
        elif action == 'pause':
            while not action == 'resume':
                pass
            action = None


server.run_forever()
