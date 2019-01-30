#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Extracts the properties of a JSON Schema converting them into terms of a JSON-LD @Context
"""

import sys
import json
import ntpath
import os

# Here the aggregated @context will be stored
aggregated_context = {
}


def read_json(infile):
    with open(infile) as data_file:
        data = json.loads(data_file.read())

    return data


def write_json(data, outfile):
    with open(outfile, 'w') as data_file:
        data_file.write(json.dumps(data))
        data_file.write("\n")

# Finds a node in a JSON Schema
# (previously parsed as a Python dictionary)


def find_node(schema, node_name):
    result = None

    if isinstance(schema, list):
        for instance in schema:
            res = find_node(instance, node_name)
            if res is not None:
                result = res
                break
    elif isinstance(schema, dict):
        for member in schema:
            if member == node_name:
                result = schema[member]
                break
            else:
                res = find_node(schema[member], node_name)
                if res is not None:
                    result = res
                    break

    return result


# extracts the properties dictionary
def extract_properties(schema):
    properties = find_node(schema, 'properties')

    out = []

    if properties is None:
        return out

    for p in properties:
        if p != "type":
            out.append(p)

    return out

 # extracts the entity type


def extract_entity_type(schema):
    out = None

    properties = find_node(schema, 'properties')

    if properties is not None and 'type' in properties:
        type_node = properties['type']

        out = type_node['enum'][0]

    return out


# extracts the enumerations
def extract_enumerations(schema):
    return []

# Generates the LD @context for a list of properties with the URI prefix


def generate_ld_context(properties, uri_prefix):
    context = {}

    if properties is None:
        return context

    for p in properties:
        if p.startswith('ref'):
            context[p] = {
                '@type': '@id',
                '@id': uri_prefix + '/' + p
            }
        elif p.startswith('date'):
            context[p] = {
                '@type': 'http://uri.etsi.org/ngsi-ld/DateTime',
                '@id': uri_prefix + '/' + p
            }
        else:
            context[p] = uri_prefix + '/' + p

    return context


# Extracts from the schema the relevant JSON-LD @context
def schema_2_ld_context(schema, uri_prefix):
    properties = extract_properties(schema)
    entity_type = extract_entity_type(schema)
    enumerations = extract_enumerations(schema)

    if (entity_type is not None):
        properties.append(entity_type)

    ld_context = generate_ld_context(properties, uri_prefix)

    return ld_context


def process_file(input_file, uri_prefix):
    if (os.path.isfile(input_file) and input_file.endswith('schema.json')):
        print input_file

        aggregate_ld_context(input_file, uri_prefix)
    elif os.path.isdir(input_file):
        for f in (os.listdir(input_file)):
            process_file(os.path.join(input_file, f), uri_prefix)


def aggregate_ld_context(f, uri_prefix):
    global aggregated_context

    schema = read_json(f)
    ld_context = schema_2_ld_context(schema, uri_prefix)

    for p in ld_context:
        aggregated_context[p] = ld_context[p]


def write_context_file():
    print 'writing'

    ld_context = {
        '@context': aggregated_context
    }

    write_json(ld_context, 'context.jsonld')


def main(args):
    uri_prefix = args[2]
    process_file(args[1], uri_prefix)

    write_context_file()


# Entry point
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: schema_2_ldcontext [folder] [URI prefix]")
        exit(-1)

    main(sys.argv)