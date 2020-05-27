import ogins as instructions 
def length_of_args(instruction):
    return sum([arg.type.length for arg in instruction.args])

def parse_args(instruction, args):
    lengths = [ arg.type.length for arg in instruction.args ]
    return tuple( int.from_bytes(bytearray([ args.pop(0) for _ in range(0, length) ]), 'big') for length in lengths )
