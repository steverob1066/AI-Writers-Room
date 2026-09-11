"""FDX (Final Draft XML) parsing and editing helpers.

Adapted from Steve's existing scripts (descriptionextract.py, editor1.py) so they can be
called from the GUI instead of run as standalone CLIs. The extraction and replacement logic
is unchanged -- only the input()/print()-driven CLI wrapper was removed in favour of return
values the GUI can display. Shared here (rather than inside one tab) since other tabs
(dialog editor, readability editor) will need the same FDX read/write.
"""
import xml.etree.ElementTree as ET
import os
import re
import datetime
from typing import List, Tuple, Dict


def load_fdx(filepath: str):
    """Parse an .fdx file. Raises ET.ParseError / FileNotFoundError -- let the caller
    catch these and show a status message, rather than swallowing them here."""
    tree = ET.parse(filepath)
    root = tree.getroot()
    return tree, root


def extract_action_description_groups(root: ET.Element):
    """Like extract_action_descriptions, but also returns the Paragraph elements that make up
    each merged description block, so a later replace can write back into the same paragraphs
    instead of doing a whole-string text search that can't match text split across paragraphs.
    Returns a list of (merged_text, [Paragraph elements]) tuples.
    """
    groups = []
    buf_texts, buf_elems = [], []
    for para in root.iter("Paragraph"):
        ptype = para.get("Type")
        text = "".join(node.text or "" for node in para.iter("Text")).strip()
        if ptype == "Action" and text:
            buf_texts.append(text)
            buf_elems.append(para)
        else:
            if buf_elems:
                groups.append((" ".join(buf_texts).strip(), buf_elems))
                buf_texts, buf_elems = [], []
    if buf_elems:
        groups.append((" ".join(buf_texts).strip(), buf_elems))
    return groups


def extract_action_descriptions(root: ET.Element) -> List[str]:
    """Extract Action paragraphs (scene descriptions), merging consecutive Action
    paragraphs into a single description block. Same logic as descriptionextract.py.
    """
    return [text for text, _elems in extract_action_description_groups(root)]


def _build_parent_map(root: ET.Element):
    return {child: parent for parent in root.iter() for child in parent}


def _set_paragraph_text(para: ET.Element, text: str) -> bool:
    """Write text into a Paragraph's first <Text> node, clearing any other Text runs
    in that paragraph so nothing duplicates. Returns False if the paragraph has no
    Text node at all (shouldn't normally happen)."""
    text_nodes = list(para.iter("Text"))
    if not text_nodes:
        return False
    text_nodes[0].text = text
    for extra in text_nodes[1:]:
        extra.text = ""
    return True


def replace_paragraph_groups(root: ET.Element, groups: List[list], new_texts: List[str]) -> List[int]:
    """Replace each group of Action paragraphs (as returned by extract_action_description_groups)
    with a single paragraph holding the new text. Any extra paragraphs in a group are removed
    from the tree so no blank lines are left behind -- this is what lets multi-paragraph
    descriptions be replaced instead of just reported as missed.
    Returns the indices of groups that failed to write (no Text node found on the first paragraph).
    """
    parent_map = _build_parent_map(root)
    failed = []
    for i, (group, new_text) in enumerate(zip(groups, new_texts)):
        first, rest = group[0], group[1:]
        if not _set_paragraph_text(first, new_text):
            failed.append(i)
            continue
        for extra_para in rest:
            parent = parent_map.get(extra_para)
            if parent is not None:
                parent.remove(extra_para)
    return failed


def _replace_and_count(s: str, old: str, new: str):
    if not s:
        return s, 0
    count = s.count(old)
    if count:
        s = s.replace(old, new)
    return s, count


def apply_replacements(root: ET.Element, replacements: List[Tuple[str, str]]) -> List[str]:
    """Global find/replace across element text, tail text, and attribute values.
    Same logic as editor1.py. Returns the list of search strings not found anywhere.
    """
    missed = []
    for search_text, replace_text in replacements:
        total = 0
        for elem in root.iter():
            if elem.attrib:
                for k, v in list(elem.attrib.items()):
                    if v:
                        new_v, c = _replace_and_count(v, search_text, replace_text)
                        if c:
                            elem.attrib[k] = new_v
                            total += c
            if elem.text:
                new_text, c = _replace_and_count(elem.text, search_text, replace_text)
                if c:
                    elem.text = new_text
                    total += c
            if elem.tail:
                new_tail, c = _replace_and_count(elem.tail, search_text, replace_text)
                if c:
                    elem.tail = new_tail
                    total += c
        if total == 0:
            missed.append(search_text)
    return missed


def save_fdx(tree: ET.ElementTree, original_filepath: str) -> str:
    """Save to a new _edit_<timestamp>.fdx file alongside the original -- never overwrites it."""
    base, ext = os.path.splitext(original_filepath)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    new_filename = f"{base}_edit_{timestamp}{ext}"
    tree.write(new_filename, encoding="utf-8", xml_declaration=True)
    return new_filename


_CHARACTER_SUFFIX_RE = re.compile(r"\s*\([^)]*\)\s*$")
_WHITESPACE_RE = re.compile(r"\s+")


def _clean_character_name(raw: str) -> str:
    """Strip trailing cues like (CONT'D), (V.O.), (O.S.) from a Character paragraph's text,
    then normalise whitespace and case so the same character isn't split into several dict
    entries by incidental formatting differences -- non-breaking spaces, doubled spaces, a
    trailing colon, or inconsistent capitalisation across the script."""
    name = raw.strip()
    while True:
        stripped = _CHARACTER_SUFFIX_RE.sub("", name).strip()
        if stripped == name:
            break
        name = stripped
    name = name.replace("\xa0", " ")
    name = _WHITESPACE_RE.sub(" ", name).strip()
    name = name.rstrip(":").strip()
    return name.upper()


def extract_character_dialogue(root: ET.Element) -> Dict[str, List[str]]:
    """Walk the script in document order, grouping consecutive Dialogue paragraphs under the
    Character cue that introduces them. A Parenthetical paragraph is skipped but doesn't end
    the speech in progress; any other paragraph type (Action, Scene Heading, Transition, a new
    Character cue) does. Returns {character_name: [speech1, speech2, ...]} in script order,
    one entry per uninterrupted speech.
    """
    result: Dict[str, List[str]] = {}
    current_character = None
    buf: List[str] = []

    def flush():
        nonlocal buf
        if current_character and buf:
            text = " ".join(buf).strip()
            if text:
                result.setdefault(current_character, []).append(text)
        buf = []

    for para in root.iter("Paragraph"):
        ptype = para.get("Type")
        text = "".join(node.text or "" for node in para.iter("Text")).strip()
        if ptype == "Character":
            flush()
            current_character = _clean_character_name(text) if text else None
        elif ptype == "Dialogue":
            if text:
                buf.append(text)
        elif ptype == "Parenthetical":
            continue
        else:
            flush()
            current_character = None

    flush()
    return result


def extract_full_script(root: ET.Element):
    """Render the whole script back into linear text with [SCENE N] markers inserted at each
    Scene Heading, so an AI reading it in one pass can cite reactions by scene number.
    Returns (script_text, {scene_number: heading_text}).
    """
    lines = []
    scene_headings: Dict[int, str] = {}
    scene_num = 0
    for para in root.iter("Paragraph"):
        ptype = para.get("Type")
        text = "".join(node.text or "" for node in para.iter("Text")).strip()
        if not text:
            continue
        if ptype == "Scene Heading":
            scene_num += 1
            scene_headings[scene_num] = text
            lines.append(f"\n[SCENE {scene_num}] {text}")
        elif ptype == "Character":
            lines.append(f"\n{text}")
        elif ptype == "Parenthetical":
            lines.append(text if text.startswith("(") else f"({text})")
        else:  # Action, Dialogue, Transition, and anything else -- append as continuous prose
            lines.append(text)
    return "\n".join(lines), scene_headings


def extract_tagged_script(root: ET.Element):
    """Like extract_full_script, but tags each paragraph with its type -- [ACTION],
    [DIALOGUE:CHARACTER], [CHARACTER], [PARENTHETICAL], [TRANSITION] -- so a task that needs
    to apply different rules to narrative prose versus spoken dialogue (e.g. a grammar
    checker, where dialogue is allowed to be naturally fragmented but action lines are not)
    has an unambiguous signal instead of having to infer paragraph type from formatting.
    A separate function from extract_full_script rather than a modification of it, so the
    four tabs already reading that plain-prose format are completely unaffected.
    Returns (tagged_text, {scene_number: heading_text}).
    """
    lines = []
    scene_headings: Dict[int, str] = {}
    scene_num = 0
    current_character = None
    for para in root.iter("Paragraph"):
        ptype = para.get("Type")
        text = "".join(node.text or "" for node in para.iter("Text")).strip()
        if not text:
            continue
        if ptype == "Scene Heading":
            scene_num += 1
            scene_headings[scene_num] = text
            lines.append(f"\n[SCENE {scene_num}] {text}")
            current_character = None
        elif ptype == "Character":
            current_character = _clean_character_name(text)
            lines.append(f"[CHARACTER] {text}")
        elif ptype == "Parenthetical":
            lines.append(f"[PARENTHETICAL] {text}")
        elif ptype == "Dialogue":
            speaker = current_character or "UNKNOWN"
            lines.append(f"[DIALOGUE:{speaker}] {text}")
        elif ptype == "Action":
            lines.append(f"[ACTION] {text}")
        elif ptype == "Transition":
            lines.append(f"[TRANSITION] {text}")
        else:
            lines.append(f"[{ptype or 'OTHER'}] {text}")
    return "\n".join(lines), scene_headings
