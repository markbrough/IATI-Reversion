#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Conversion from v2.01 to v1.05 of the IATI Standard
# Copyright Mark Brough 2015, released under MIT License

from lxml import etree
import unicodecsv
import sys, os

narrative_els = ['title', 'description', 'participating-org']
codelist_updates = [
    {
        'path': 'participating-org',
        'attrib': 'role',
        'codelist': 'OrganisationRole'
    },
    {
        'path': 'activity-date',
        'attrib': 'type',
        'codelist': 'ActivityDateType'
    },
    {
        'path': 'transaction/transaction-type',
        'attrib': 'code',
        'codelist': 'TransactionType'
    }
]

def load_codelists():
    """Load codelists in that need to be changed"""

    def filter_csv(filename):
        if filename.endswith(".csv"):
            return True
        return False

    cl = filter(filter_csv, os.listdir("codelists"))
    codelists = {}
    for c in cl:
        csv = unicodecsv.DictReader(
                    open(os.path.join("codelists", c), "rb")
                    )
        codelist_name = c.split(".")[0]
        codelists[codelist_name] = {}
        for row in csv:
            codelists[codelist_name][row['2.01']] = row['1.0x']
    return codelists

codelist_conversions = load_codelists()

def convert_narrative(activity_in, element_name):

    """Restructure all narrative elements"""

    elements = activity_in.findall("%s/narrative" % element_name)
    for element in elements:
        new_el = etree.Element(element_name)
        new_el.text = element.text
        
        el_attribs = dict(map(lambda x: (x[0], x[1]), element.getparent().attrib.items()))
        parent_attribs = dict(map(lambda x: (x[0], x[1]), element.attrib.items()))
        
        attribs = dict(parent_attribs, **el_attribs)
        for k, v in attribs.items():
            new_el.set(k, v)
        # We don't care about ordering for 1.05
        activity_in.append(new_el)

    for element in elements:
        try:
            activity_in.remove(element.getparent())
        except ValueError:
            pass
    return activity_in

def convert_codelists(activity_in):
    """Change codelist values"""

    for cu in codelist_updates:
        els = activity_in.xpath(cu['path'])
        for el in els:
            current = el.get(cu['attrib'])
            try:
                new = codelist_conversions[cu['codelist']][current]
            except KeyError:
                iatiid = activity_in.find("iati-identifier").text
                #print "Codelist conversion not found for codelist %s and value %s in activity %s" % (cu['codelist'], current, iatiid)
                continue
            el.set(cu['attrib'], new)
    return activity_in        

def convert_activity(activity_in, activities_out):
    """Convert for a particular activity"""

    for el in narrative_els:
        convert_narrative(activity_in, el)
    convert_codelists(activity_in)
    return activities_out.append(activity_in)

def reversion(doc):
    """Main function which takes a file in 2.01 format and converts to 1.05"""

    activities_in = doc.xpath("//iati-activity")
    activities_out = doc.getroot()
    activities_out.set("version", "1.05")
    # Clear existing activities
    for obj in activities_out:
        activities_out.remove(obj)
    # Convert activities
    for activity in activities_in:
        convert_activity(activity, activities_out)
    return activities_out

if __name__ == "__main__":
    args = sys.argv
    args.pop(0)
    filename = args[0]
    doc = etree.parse(filename)
    converted = reversion(doc)
    print etree.tostring(converted, pretty_print = True)