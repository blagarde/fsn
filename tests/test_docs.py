"""The documentation must stay navigable: valid front matter, resolvable links and IDs, current indexes."""
import pytest

from htfbr_data import docs


def test_docs_validate_clean():
    errors = docs.validate()
    assert errors == [], "\n".join(errors)


def test_generated_indexes_are_current():
    # Without a database the material facts are left alone, so this checks indexes, used-by lists
    # and the claims page. Run `htfbr-data docs` to fix a failure.
    assert docs.generate(con=None, check=True) == []


def test_replace_block():
    text = "a\n<!-- BEGIN GENERATED x -->\nold\n<!-- END GENERATED -->\nb"
    assert docs.replace_block(text, "x", "new") == "a\n<!-- BEGIN GENERATED x -->\nnew\n<!-- END GENERATED -->\nb"
    with pytest.raises(ValueError):
        docs.replace_block(text, "y", "new")


def test_heading_slugs_match_github_style():
    assert docs._slug("Stage 2: figures of merit") == "stage-2-figures-of-merit"
    assert docs._slug("Mitigating the tube-wall risk") == "mitigating-the-tube-wall-risk"


def test_every_design_material_exists_and_is_linked_back():
    users = docs.used_by()
    material_ids = {m["id"] for _, m in docs.pages("materials")}
    assert set(users) <= material_ids
