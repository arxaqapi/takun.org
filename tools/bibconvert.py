#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "bibtexparser>=1.4.4",
#     "tomlkit>=0.15.0",
# ]
# ///
"""
Convert between publications.toml and publications.bib.

Round-trip: standard bibliographic fields plus the custom `preprint` field
survive bib -> toml -> bib. Each bib entry maps to exactly one publication (in
file order); a preprint is just a `preprint = {url}` field on the same entry, not
a separate @misc. Website-only fields (tags, code, materials) don't exist in
bibtex, so they're omitted from the export; `to-toml` preserves any it finds in
an existing publications.toml (matched by `key`), so re-importing never wipes
hand-added tags/links.

Deps: `to-toml` needs bibtexparser; writing TOML needs tomli-w. (`to-bib` writes
bibtex by hand and only reads TOML, so it needs neither.)
"""

import re
from pathlib import Path
import argparse

import tomlkit
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import author as split_author, convert_to_unicode


# Standard bibtex fields, in the order they're written. `author` comes from the
# TOML `authors` list; everything else maps 1:1.
BIB_FIELDS = [
    "title",
    "author",
    "year",
    "booktitle",
    "journal",
    "publisher",
    "address",
    "pages",
    "volume",
    "number",
    "doi",
    "issn",
    "isbn",
    "editor",
    "month",
    "preprint",
]
# TOML keys that must never be written to bibtex (structural or website-only).
WEBSITE_ONLY = ["tags", "code", "materials"]
NON_FIELD = {"key", "type", "authors"} | set(WEBSITE_ONLY)

# order the publication dict is written to TOML
TOML_ORDER = ["key", "type"] + [f for f in BIB_FIELDS if f != "author"]
TOML_ORDER.insert(TOML_ORDER.index("title") + 1, "authors")


# --------------------------------------------------------------------- shared
def full_name(name):
    """'Last, First' -> 'First Last'; leave 'First Last' untouched."""
    if "," in name:
        last, first = (p.strip() for p in name.split(",", 1))
        return f"{first} {last}".strip()
    return re.sub(r"\s+", " ", name).strip()


def clean_doi(value):
    if not value or "arxiv.org" in value:
        return None
    return value.replace("https://doi.org/", "").strip()


# ------------------------------------------------------------------- to-bib
def emit_entry(pub):
    fields = {}
    if pub.get("authors"):
        fields["author"] = " and ".join(pub["authors"])
    for f in BIB_FIELDS:
        if f == "author":
            continue
        v = pub.get(f)
        if v not in (None, ""):
            fields[f] = str(v)
    width = max((len(f) for f in fields), default=0)
    lines = [f"@{pub.get('type', 'misc')}{{{pub['key']},"]
    for f in BIB_FIELDS:
        if f in fields:
            lines.append(f"    {f.ljust(width)} = {{{fields[f]}}},")
    lines.append("}")
    return "\n".join(lines)


def to_bib(
    tomlfile: Path,
    bibfile: Path,
):
    pubs = tomlkit.parse(tomlfile.read_text(encoding="utf-8")).get("publication", [])
    header = (
        "% Generated from publications.toml by tools/bibconvert.py — do not edit.\n"
        "% The TOML is the source of truth. Website-only fields (tags, code,\n"
        "% materials) are intentionally omitted here.\n\n"
    )
    bibfile.write_text(
        header + "\n\n".join(emit_entry(p) for p in pubs) + "\n", encoding="utf-8"
    )
    print(f"wrote {len(pubs)} entries -> {bibfile}")


# ------------------------------------------------------------------- to-toml
def load_bib_entries(bibfile: Path):
    parser = BibTexParser(common_strings=True)
    parser.customization = lambda r: split_author(convert_to_unicode(r))
    return bibtexparser.loads(
        bibfile.read_text(encoding="utf-8"), parser=parser
    ).entries


def entry_to_pub(entry):
    pub = {
        "key": entry["ID"],
        "type": entry.get("ENTRYTYPE", "misc"),
        "title": re.sub(r"\s+", " ", entry.get("title", "")).strip(),
        "authors": [full_name(a) for a in entry.get("author", [])],
    }
    if entry.get("year"):
        pub["year"] = int(entry["year"]) if entry["year"].isdigit() else entry["year"]
    for f in [
        "booktitle",
        "journal",
        "publisher",
        "address",
        "pages",
        "volume",
        "number",
        "issn",
        "isbn",
        "editor",
        "month",
    ]:
        if entry.get(f):
            pub[f] = re.sub(r"\s+", " ", entry[f]).strip()
    doi = clean_doi(entry.get("doi", ""))
    if doi:
        pub["doi"] = doi
    if entry.get("preprint"):
        pub["preprint"] = entry["preprint"].strip()
    return pub


def order_pub(pub):
    ordered = {k: pub[k] for k in TOML_ORDER if k in pub}
    for k in WEBSITE_ONLY:
        if k in pub:
            ordered[k] = pub[k]
    for k in pub:  # anything unexpected, keep it
        ordered.setdefault(k, pub[k])
    return ordered


def to_toml(
    bibfile: Path,
    tomlfile: Path,
):
    # One publication per bib entry, in file order. `preprint` is just a field.
    pubs = [entry_to_pub(e) for e in load_bib_entries(bibfile)]

    # preserve website-only fields from an existing TOML, matched by key
    prev = {}
    if tomlfile.exists():
        prev = {
            p.get("key"): p
            for p in tomlkit.loads(tomlfile.read_text(encoding="utf-8")).get(
                "publication", []
            )
        }
    for pub in pubs:
        for f in WEBSITE_ONLY:
            if f in prev.get(pub["key"], {}):
                pub[f] = prev[pub["key"]][f]
        pub.setdefault("tags", [])

    out = {"publication": [order_pub(p) for p in pubs]}
    tomlfile.write_bytes(tomlkit.dumps(out).encode("utf-8"))
    print(f"wrote {len(pubs)} publications -> {tomlfile}")
    if not any(p.get("tags") for p in pubs):
        print("note: no tags yet — add `tags = [...]` to each publication.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", type=Path, help=".toml or .bib file")
    args = parser.parse_args()

    tomlfile = Path("assets/publications.toml")
    bibfile = Path("assets/publications.bib")

    if args.file.suffix == ".toml":
        to_bib(tomlfile, bibfile)
    elif args.file.suffix == ".bib":
        to_toml(bibfile, tomlfile)
    else:
        raise NotImplementedError()
