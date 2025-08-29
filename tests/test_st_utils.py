
import os
import re

TRACE_PATTERN = re.compile(r'\s*at\s+([\w\.$]+)\(([\w\.]+):(\d+)\)')


def test_st_pattern():
    cwd = os.getcwd()
    st_txt = os.path.join(cwd, "tests/mocks/st_01.txt")

    target = ('org.apache.commons.lang.WordUtils.abbreviate', 'WordUtils.java', '629')

    with open(st_txt, "r") as f:
        content = f.read()

    exists = 0
    
    for line in content.splitlines():
        match = TRACE_PATTERN.search(line)
        if match:
            if match.groups() == target:
                exists += 1

    assert exists == 1