"""Untrusted BPMN must not be parsed with an entity-expanding parser.

stdlib ElementTree expands internal entities with no limit, so a few hundred
bytes of nested declarations expands to gigabytes and OOM-kills the process.
Both parse sites go through defusedxml instead; these tests pin that down so a
future `from xml.etree import ElementTree` doesn't quietly undo it.
"""

import pytest
from defusedxml.common import EntitiesForbidden

from bpmn.bpmn import get_bpmn
from utils import get_elements_by_type

# ~2000x amplification at this size, and every extra ~45 bytes multiplies it by
# ten again -- well past available memory long before the 2 MB body cap bites.
BILLION_LAUGHS = """<?xml version="1.0"?>
<!DOCTYPE bpmn:definitions [
<!ENTITY a "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA">
<!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;">
<!ENTITY c "&b;&b;&b;&b;&b;&b;&b;&b;&b;&b;">
<!ENTITY d "&c;&c;&c;&c;&c;&c;&c;&c;&c;&c;">
]>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">&d;</bpmn:definitions>"""

EXTERNAL_ENTITY = """<?xml version="1.0"?>
<!DOCTYPE bpmn:definitions [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">&xxe;</bpmn:definitions>"""


@pytest.mark.parametrize("payload", [BILLION_LAUGHS, EXTERNAL_ENTITY])
def test_get_elements_by_type_rejects_entity_declarations(payload):
    with pytest.raises(EntitiesForbidden):
        get_elements_by_type(payload, "process")


@pytest.mark.parametrize("payload", [BILLION_LAUGHS, EXTERNAL_ENTITY])
def test_get_bpmn_rejects_entity_declarations(payload):
    with pytest.raises(EntitiesForbidden):
        get_bpmn(payload)


def test_ordinary_bpmn_still_parses():
    """The guard must not reject documents that merely declare namespaces."""
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">'
        '<bpmn:process id="p1"><bpmn:task id="t1" name="Ship order"/></bpmn:process>'
        "</bpmn:definitions>"
    )
    assert get_elements_by_type(xml, "task") == [("ship order", "t1")]
