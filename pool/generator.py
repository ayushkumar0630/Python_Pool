"""
# Problem 2: Garbled Circuit Generator (20 points)
"""

import circuit
from circuit import BooleanCircuit
import json
from util import specialDecryption, specialEncryption, generate_key
import os
import random

"""
## Problem 2.01: implement a random shuffling routine (5 points)
Hint: use knuth-fischer-yates shuffling

    Use util.random_bytes for randomness.

    http://www.i-programmer.info/programming/theory/2744-how-not-to-shuffle-the-kunth-fisher-yates-algorithm.html

    Note: random.shuffle() from python stdlib does not count!
"""
def shuffle(a):
    assert type(a) is list
    # TODO: sort a in place, and return None
    n = len(a)
    i = 0
    temp = n
    while temp != 0:
        temp  = temp/16
        i = i+1
    for idx in range(n):
        rand = int(os.urandom(i).encode('hex'), 16)
        while idx+rand >= n:
            rand = int(os.urandom(i).encode('hex'), 16)
        a[idx], a[rand+idx] = a[rand+idx], a[idx]

"""
## Problem 2: Garbled Circuit Generator (15 points)
"""

class GarbledCircuitGenerator(BooleanCircuit):
    def __init__(self, from_json=None):
        # The superclass constructor initializes the gates and topological sorting
        super(GarbledCircuitGenerator,self).__init__(from_json=from_json)

    def garble(self):
        
        # Generate new wire labels
        self.wire_labels = {} # maps wire id to {"0":label0 ,"1": label1}

        # TODO: your code goes here
        for wid in self.wires:
            key_0 = generate_key().encode('hex')
            key_1 = generate_key().encode('hex')
            self.wire_labels[wid] = [key_0, key_1]

        # Generate garble tables
        self.garble_table = {}

        # TODO: your code goes here
        index = [[0, 0], [0, 1], [1, 0], [1, 1]]
        for gid in self.gates:
            gate = self.gates[gid]
            inp = gate["inp"]
            wid = gate["out"][0]
            table = gate["table"]
            garble_table = []
            for i in range(4):
                key_0 = self.wire_labels[inp[0]]
                key_1 = self.wire_labels[inp[1]]
                label_0 = key_0[index[i][0]].decode('hex')
                label_1 = key_1[index[i][1]].decode('hex')
                msg = self.wire_labels[wid][table[i]].decode('hex')
                cipher = specialEncryption(label_0, specialEncryption(label_1, msg)).encode('hex')
                garble_table.append(cipher)
                shuffle(garble_table)
            self.garble_table[gid] = garble_table



    def output(self, outfile, inputs=None, debug=True):
        # Save as a JSON file, with wire lables for debugging
        obj = {}
        gates = {}
        for gid,gate in self.gates.iteritems():
            gates[gid] = gate.copy() # Copy the gate object directly
            gates[gid]["garble_table"] = self.garble_table[gid]
        obj["gates"] = gates

        # Output wire labels in debug mode
        if debug: 
            obj["wire_labels"] = self.wire_labels

        if inputs is not None:
            print 'Input available'
            assert len(inputs) == len(self.input_wires)
            input_labels = {}
            for wid,v in inputs.iteritems():
                assert v in (0,1)
                input_labels[wid] = self.wire_labels[wid][v]
                obj["inputs"] = input_labels

        with open(outfile,"w") as f:
            json.dump(obj, f, indent=4)
        print 'Wrote garbled circuit', outfile

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print "usage: python generator.py <circuit.json> <outfile.json>"
        sys.exit(1)

    filename = sys.argv[1]
    obj = json.load(open(filename))

    # Circuit
    c = GarbledCircuitGenerator(from_json=obj)
    print 'Circuit loaded: %d gates, %d input wires, %d output_wires, %d total' \
        % (len(c.gates), len(c.input_wires), len(c.output_wires), len(c.wires))
    
    # Generate the circuit
    c.garble()

    # Load the inputs
    inputs = obj["inputs"]

    # Write the output
    outfile = sys.argv[2]
    c.output(outfile, inputs)
