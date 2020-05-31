import ogins as ins
from . import parse_instruction as pi
import time
import json
import sys
import logging
from wss import WebSocketServer, NoMessagesError
import threading

logger = logging.getLogger('openglass.emulator')
#logger.setLevel(logging.DEBUG)


class StackOverflowError(Exception):
    pass


class Stack:
    _list = []
    def __init__(self, limit):
        self.limit = limit

    def pop(self):
        return self._list.pop(0)

    def push(self, value):
        if len(self._list) < self.limit:
            return self._list.insert(0, value)
        else:
            raise StackOverflowError


stack = Stack(1000)
action = None
buttons = {
        "front": False,
        "back": False,
}
server = WebSocketServer(8765)
while not server.clients:
    pass


def handle_commands():
    global action
    while True:
        try:
            logger.debug('checking for messages')
            message = server.first_message.data
            logger.debug(f'got message: {message}')
            message = json.loads(message)
            if message['type'] == 'stop':
                action = 'halt'
            elif message['type'] == 'pause':
                action = 'pause'
            elif message['type'] == 'resume':
                action = 'resume'
            elif message['type'] == 'button':
                buttons[message['button']] = message['status']
        except NoMessagesError:
            logger.debug('no messages')
        time.sleep(1/1000000)


def stringify(opcode, args):
    logger.debug(f'{opcode.name} {" ".join([str(num) for num in args])}')


def main():
    global action
    server.send('{"type":"status", "status":"loading"}')
    with open(sys.argv[1] if len(sys.argv) >= 2 else 'openglass.bin', 'rb') as f:
        bytecode = bytearray(f.read())[5:]
    i=0
    screen_msgs = []
    server.send('{"type":"status", "status":"running"}')
    while True:
        opcode = ins.instructions[bytecode[i]]
        i+=1
        arg_count = pi.length_of_args(opcode)
        args = pi.parse_args(opcode, bytecode[i:i+arg_count])
        i += arg_count
        stringify(opcode, args)
        if opcode is ins.POK:
            bytecode[args[1]] = args[0]
        elif opcode is ins.DEL:
            time.sleep(args[0]/1000)
        elif opcode is ins.LON:
            server.send('{"type":"led", "status":true}')
        elif opcode is ins.LOF:
            server.send('{"type":"led", "status":false}')
        elif opcode is ins.JMP:
            if args[1]: stack.push(i)
            i = args[0]-0
        elif opcode is ins.ADB:
            bytecode[args[0]] = bytecode[args[0]] + args[1]
        elif opcode is ins.SCW:
            screen_msgs.append({'type':'screen', 'status':True, 'x':args[0], 'y':args[1]})
        elif opcode is ins.SCB:
            screen_msgs.append({'type':'screen', 'status':False, 'x':args[0], 'y':args[1]})
        elif opcode is ins.SCF:
            server.send(json.dumps(screen_msgs))
            screen_msgs = []
        elif opcode is ins.JEB:
            if bytecode[args[1]] == args[2]:
                if args[3]: stack.push(i)
                i = args[0]
                logger.debug('jumped')
        elif opcode is ins.JLB:
            if bytecode[args[1]] < args[2]:
                if args[3]: stack.push(i)
                i = args[0]
                logger.debug('jumped')
        elif opcode is ins.JGB:
            if bytecode[args[1]] > args[2]:
                if args[3]: stack.push(i)
                i = args[0]
                logger.debug('jumped')
        elif opcode is ins.HLT:
            server.send('{"type":"status", "status":"stopped", "reason":"instruction"}')
            exit(0)
        elif opcode is ins.SBB:
            bytecode[args[0]] = bytecode[args[0]] - args[1]
        elif opcode is ins.GBD:
            bytecode[args[1]] = 1 if buttons[{2:'front', 0:'back'}[args[0]]] else 0
        elif opcode is ins.RET:
            i = stack.pop()
        elif opcode is ins.REB:
            if bytecode[args[0]] == args[1]:
                i = stack.pop()
        elif opcode is ins.RLB:
            if bytecode[args[0]] < args[1]:
                i = stack.pop()
        elif opcode is ins.RGB:
            if bytecode[args[0]] > args[1]:
                i = stack.pop()
        else:
            logger.debug(f'Fatal error! Cannot interpret {opcode.name}')
            server.send(json.dumps({'type':'status', 'status':'stopped', 'reason':'bad_known_opcode', 'name':opcode.name}))
            exit(0)
        if action == 'halt':
            server.send('{"type":"status", "status":"stopped", "reason":"request"}')
            exit(0)
        elif action == 'pause':
            server.send('{"type":"status", "status":"paused"}')
            while not action == 'resume':
                pass
            server.send('{"type":"status", "status":"running"}')
            action = None
        time.sleep(1/1000000)

threading.Thread(target=main).start()
threading.Thread(target=handle_commands, daemon=True).start()
