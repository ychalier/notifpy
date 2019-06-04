import re


def parse(re_start, re_end, text):
    events = [
        ("start", match.start(), match.end())
        for match in re.finditer(re_start, text, re.MULTILINE | re.DOTALL)
    ]
    events += [
        ("end", match.start(), match.end())
        for match in re.finditer(re_end, text, re.MULTILINE | re.DOTALL)
    ]
    events.sort(key=lambda x: x[1])
    tree = {"start": 0, "end": -1, "children": [], "parent": None}
    for event, start, end in events:
        if event == "start":
            tree["children"].append({
                "start": start,
                "parent": tree,
                "children": [],
            })
            tree = tree["children"][-1]
        else:
            tree["end"] = end
            tree = tree["parent"]
    return tree


def replace(string, start, end, value):
    return string[:start] + value + string[end:]


class Renderer:

    CHILD_PLACEHOLDER = "##__CHILD__{index}__##"

    def __init__(self, template):
        self.html = ""
        with open("notifpy/templates/" + template) as file:
            self.html = file.read()

    def cp(self, i):
        return Renderer.CHILD_PLACEHOLDER.format(index=i)

    def placeholder(self, scope):
        def aux(start, end):
            tmp = self.html[start:end]
            offset = 0
            for match in re.finditer("{{ (\w+)\.(\w+) }}", tmp, re.MULTILINE | re.DOTALL):
                variable = match.group(1)
                field = match.group(2)
                tmp = replace(
                    tmp,
                    offset + match.start(),
                    offset + match.end(),
                    self.context[variable][field]
                )
                offset += len(str(self.context[variable][field])) - len(match.group(0))
            return tmp
        html = ""
        start = scope["start"]
        for i, child in enumerate(scope["children"]):
            html += aux(start, child["start"]) + self.cp(i)
            start = child["end"]
        return html + aux(start, scope["end"])

    def loop(self, scope):
        def aux(match=None):
            tmp = self.placeholder(scope)
            if match is not None:
                tmp = tmp[match.end():-12]
            for i, child in enumerate(scope["children"]):
                tmp = tmp.replace(self.cp(i), self.loop(child))
            return tmp
        match = re.search("^{% for (\w+) in (\w+(?:\.\w+)?) %}", self.html[scope["start"]:])
        html = ""
        if match is not None:
            variable = match.group(1)
            iterator = match.group(2)
            if "." in iterator:
                cls, attr = iterator.split(".")
                iterator = self.context[cls][attr]
            else:
                iterator = self.context[iterator]
            for x in iterator:
                self.context[variable] = x
                html += aux(match)
        else:
            html += aux()
        return html

    def render(self, context):
        self.context = context
        scope = parse("{% for \w+ in \w+(?:\.\w+)? %}", "{% endfor %}", self.html)
        return self.loop(scope)
