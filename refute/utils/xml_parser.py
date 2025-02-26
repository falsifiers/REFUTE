import xml.etree.ElementTree as ET
import re


def wrap_cdata(tag, content):
    """Wraps the content inside CDATA for a given XML tag."""
    return re.sub(
        fr"<{tag}>(.*?)</{tag}>",
        fr"<{tag}><![CDATA[\1]]></{tag}>",
        content,
        flags=re.DOTALL
    )


def sanitize_xml(output):
    # delete any content between <thoughts> and </thoughts>
    output = re.sub(r"<thoughts>.*</thoughts>", "", output, flags=re.DOTALL)

    if "<reason>" in output and "</reason>" in output:
        output = re.search(r"<reason>.*</action>", output, re.DOTALL).group(0)
    else:
        output = re.search(r"<action>.*</action>", output, re.DOTALL).group(0)

    return wrap_cdata("code", wrap_cdata("reason", output))


def parse_multiple_actions(output):
    output = sanitize_xml(output)
    wrapped_xml = f"<root>{output}</root>"

    try:
        root = ET.fromstring(wrapped_xml)
        actions = {}

        for action_elem in root.findall("action"):
            name = action_elem.find("name").text.strip()
            all_found = action_elem.findall("*")
            actions[name] = {
                el.tag: el.text.strip() for el in all_found if el.tag != "name"
            }

        return actions
    except ET.ParseError as e:
        return None
