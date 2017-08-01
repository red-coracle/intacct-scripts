import csv
import requests
from config import sender_id, sender_password
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
# from collections import defaultdict

xml_base = '''<?xml version="1.0" encoding="utf-8"?>
<request>
  <control>
    <senderid></senderid>
    <password></password>
    <controlid>ControlIdHere</controlid>
    <uniqueid>false</uniqueid>
    <dtdversion>3.0</dtdversion>
  </control>
  <operation>
    <authentication>
      <sessionid></sessionid>
    </authentication>
    <content />
  </operation>
</request>
'''
root = ET.fromstring(xml_base)


def parse_and_log_errors(response):
    ignore_errors = []
    with open('debug.log', 'a') as log:
        try:
            response = ET.fromstring(response)
            for error in response.findall('.//error'):
                errorno = error.find('.//errorno').text
                if errorno not in ignore_errors:
                    description = error.find('.//description').text
                    description2 = error.find('.//description2').text
                    correction = error.find('.//correction').text
                    message = ','.join(str(i) for i in [errorno, description, description2, correction])
                    log.write('{}\n'.format(message))
        except BaseException as e:
            log.write('{}\n'.format(e))


def csv_to_dict(source):
    with open(source, 'r') as f:
        reader = csv.DictReader(f, dialect="excel")
        return [{column: row[column] for column in row} for row in reader]


def dict_to_xml(dct, root_title):
    root = ET.Element(root_title)
    for item in dct:
        if type(dct[item]) == dict:
            root.append(dict_to_xml(dct[item], item))
        else:
            root.append(ET.fromstring(f'<{item}>{escape(dct[item])}</{item}>'))
    return root


if __name__ == '__main__':
    # Could change these prompts.
    filename = input('Filename: ')
    root[0][0].text = sender_id
    root[0][1].text = sender_password
    root[1][0][0].text = input('Session ID: ')
    details = [dict_to_xml(detail, 'create_taxdetail') for detail in csv_to_dict(filename)]
    content = root[1][1]
    for detail in details:
        function = ET.Element('function', attrib={'controlid': 'tax_upload'})
        function.append(detail)
        content.append(function)
    r = requests.post("https://api.intacct.com/ia/xml/xmlgw.phtml",
                      headers={'Content-Type': 'x-intacct-xml-request'},
                      data=ET.tostring(root))
    parse_and_log_errors(r.text)
