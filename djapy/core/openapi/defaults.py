from pathlib import Path

__all__ = ['REF_MODAL_TEMPLATE', 'ABS_TPL_PATH']
REF_MODAL_TEMPLATE = "#/components/schemas/{model}"
ABS_TPL_PATH = Path(__file__).parent.parent.parent / "templates/djapy/"
