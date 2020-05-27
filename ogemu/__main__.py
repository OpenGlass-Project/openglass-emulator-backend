import ogins as ins
from . import parse_instruction as pi
import time
import asyncio
import websockets
import json
import sys


async def main(websocket, path):
    with open(sys.argv[1] if len(sys.argv) >= 2 else 'openglass.bin', 'rb') as f:
        bytecode = bytearray(f.read())[5:]
    i=0
    screen_msgs = []
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
            await asyncio.sleep(args[0]/1000)
        elif opcode is ins.LON:
            print(f'LON')
            await websocket.send('{"type":"led", "status":true}')
        elif opcode is ins.LOF:
            print(f'LOF')
            await websocket.send('{"type":"led", "status":false}')
        elif opcode is ins.JMP:
            print(f'JMP {args[0]}')
            i = args[0]-0
        elif opcode is ins.ADB:
            print(f'ADB {args[0]} {args[1]}')
            bytecode[args[0]] = bytecode[args[0]] + args[1]
        elif opcode is ins.SCW:
            print(f'SCW {args[0]} {args[1]}')
            screen_msgs.append(json.dumps({'type':'screen', 'status':True, 'x':args[0], 'y':args[1]}))
        elif opcode is ins.SCB:
            print(f'SCB {args[0]} {args[1]}')
            screen_msgs.append(json.dumps({'type':'screen', 'status':False, 'x':args[0], 'y':args[1]}))
        elif opcode is ins.SCF:
            print(f'SCF')
            for screen_msg in screen_msgs:
                await websocket.send(screen_msg)
        elif opcode is ins.JEB:
            print(f'JEB {args[0]} {args[1]} {args[2]}')
            if bytecode[args[1]] == args[2]:
                i = args[0]
                print('jumped')
        elif opcode is ins.HLT:
            print(f'HLT')
            break
        else:
            print(f'Fatal error! Cannot interpret {opcode.name}')
            break


start_server = websockets.serve(main, "0.0.0.0", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()

