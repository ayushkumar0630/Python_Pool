"""
# Problem 1: Garbled Circuit Evaluator (10 points)
"""

import circuit
import util
import json
from circuit import BooleanCircuit
from util import specialDecryption, specialEncryption


class GarbledCircuitEvaluator(BooleanCircuit):
    def __init__(self, from_json=None):
        # The superclass constructor initializes the gates and topological sorting
        super(GarbledCircuitEvaluator,self).__init__(from_json=from_json)

        # What remains is for us to load the garbling tables
        if from_json is not None:
            
            # Load the garbled tables
            gates = from_json["gates"]

            # TODO: your code goes here
            garbled_tables = {}
            input_labels = from_json["inputs"]

            for gid in self.sorted_gates:
                gate = gates[gid]
                table = gate["garble_table"]
                garbled_tables[gid] = table

            self.garbled_tables = garbled_tables
            self.input_labels = input_labels
            


    def garbled_evaluate(self, inp):
        # Precondition: initialized, topologically sorted
        #               has garbled tables
        #               inp is a mapping of wire labels for each input wire
        # Postcondition: self.wire_labels takes on labels resulting from this evaluation
        assert len(inp) == len(self.input_wires)
        self.wire_labels = {}

        # Set the wire labels for all the input wires
        for wid in self.input_wires:
            assert wid in inp, "Must provide a label for each wire"
            label = inp[wid]
            assert len(label) == 2 * 16  # Labels are keys, 16 bytes in hex
            self.wire_labels[wid] = label

        # TODO: Your code goes here
        # table_types = ["AND", "XOR", "OR"]
        for gid in self.sorted_gates:
            gate = self.gates[gid]

            # Two input wires
            inp = gate["inp"]
            wid = gate["out"][0]
            garbled_table = self.garbled_tables[gid]

            #inputs
            wire_label_0 = self.wire_labels[inp[0]]
            wire_label_1 = self.wire_labels[inp[1]]
            key_0 = wire_label_0.decode('hex')
            key_1 = wire_label_1.decode('hex')

            for c in garbled_table:
                cipher = c.decode('hex')
                if specialDecryption(key_0, cipher) == None:
                    continue
                k = specialDecryption(key_0, cipher)
                if specialDecryption(key_1, k) == None:
                    continue
                m = specialDecryption(key_1, k)
                label = m.encode('hex')
                self.wire_labels[wid] = label

        return dict((wid,self.wire_labels[wid]) for wid in self.output_wires)

        
if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print "usage: python evaluator.py <circuit.json>"
        sys.exit(1)

    filename = sys.argv[1]
    obj = json.load(open(filename))

    # Circuit
    c = GarbledCircuitEvaluator(from_json=obj)
    print >> sys.stderr, 'Garbled circuit loaded: %d gates, %d input wires, %d output_wires, %d total' \
        % (len(c.gates), len(c.input_wires), len(c.output_wires), len(c.wires))

    # Evaluate the circuit
    inputs = obj["inputs"]
    json.dump(c.garbled_evaluate(inputs), sys.stdout, indent=4)
    print '' # end the line
