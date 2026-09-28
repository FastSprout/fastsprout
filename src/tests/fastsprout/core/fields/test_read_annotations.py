from fastsprout.core.fields.metaclass import read_annotations


def test_returns_annotations_dict_when_present():
    ns = {"__annotations__": {"x": int, "y": str}}
    assert read_annotations(ns) == {"x": int, "y": str}


def test_falls_back_to_annotate_func_pep749():
    def annotate(fmt: int) -> dict[str, type]:
        return {"x": int}

    ns = {"__annotate_func__": annotate}
    assert read_annotations(ns) == {"x": int}


def test_falls_back_to_annotate_attribute():
    def annotate(fmt: int) -> dict[str, type]:
        return {"y": str}

    ns = {"__annotate__": annotate}
    assert read_annotations(ns) == {"y": str}


def test_swallows_annotate_func_exceptions():
    def annotate(fmt: int) -> dict[str, type]:
        raise NameError("forward ref not resolvable yet")

    ns = {"__annotate_func__": annotate}
    assert read_annotations(ns) == {}


def test_returns_empty_when_nothing_present():
    assert read_annotations({}) == {}
