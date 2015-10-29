#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

class ZuoraError(Exception):
    pass


def generate_select_list(field_list=[]):
    """
    Generate the select list based on the fields provided.  Automatically inserts Id.

    :param field_list: List of Zuora fields to be added to the select_list
    :return: select_list

    Ex ZOQL: SELECT {select_list} FROM {z_object_type} WHERE {search_conditions}
    """
    field_set = set(field_list)
    field_set.add('Id')
    return ", ".join(["%s" % f for f in field_set])


def generate_search_conditions(field_name='Id', field_is_string=True, operator='OR', values=[]):
    """
    Generate the search conditions based on the fields provided.  More complex search conditions
    (with more than one field name and operator should be done manually).

    :param field_name: The field to be searched by (ed. Id)
    :param field_is_string:  Is this field a string
    :param operator: The operator
    :param values: The, for example, Ids to be queried

    :return: search_conditions

    Ex ZOQL: SELECT {select_list} FROM {z_object_type} WHERE {search_conditions}
    """
    search_condition = ""
    where = "{column_name}="
    if field_is_string:
        where += '\'{value}\''
    else:
        where += "{value}"

    for value in values:
        if search_condition != "":
            search_condition += " {operator} ".format(operator=operator)
        search_condition += where.format(column_name=field_name, value=value)
    return search_condition