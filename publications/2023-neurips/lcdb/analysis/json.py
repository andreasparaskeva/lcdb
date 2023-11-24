from typing import List, Any

import jmespath


class JsonQuery:
    def __init__(self, expression: str) -> None:
        self.expression = jmespath.compile(expression)

    def apply(self, x: dict):
        """Extract a metric from a dict (json-like) object."""
        out = self.expression.search(x)
        return out

    def __call__(self, x) -> Any:
        return self.apply(x)


class QueryAnchorValues(JsonQuery):
    """Extract the anchor values."""

    def __init__(self):
        super().__init__(
            f"children[?tag == 'build_curves'] | [0]"
            f".children[?tag == 'anchor'] | []"
            f".metadata.value"
        )


class QueryAnchorsChildren(JsonQuery):
    """Extract children data from all anchors."""

    def __init__(self):
        super().__init__(
            f"children[?tag == 'build_curves'] | [0]"
            f".children[?tag == 'anchor'] | [*]"
            f".children"
        )


class QueryMetricValuesFromAnchors(JsonQuery):
    """Extract a metric for all anchors."""

    def __init__(self, metric_name: str, split_name: str = "val"):
        super().__init__(
            f"children[? tag == 'build_curves'] | [0]"  # here we replace sublists by the first element
            f".children[? tag == 'anchor'] | []"  # here we keep all elements of the list
            f".children[? tag == 'metrics'] | []"
            f".children[? tag == '{split_name}'] | []"
            f".children[? tag == '{metric_name}'] | []"
            f".metadata.value"
        )


class QueryEpochValues(JsonQuery):
    """Extract the epoch values for all anchors."""

    def __init__(self, with_epoch_test: bool = True):
        if with_epoch_test:
            super().__init__(
                f"children[? tag == 'build_curves'] | [0]"
                f".children[? tag == 'anchor'] | [*]"
                f".children[? tag == 'fit'] | [*][0]"
                f".children[? tag == 'epoch_train'] | [*][0]"
                f".children[? tag == 'epoch'] | [*][?children]"
                f".metadata.value"
            )
        else:
            super().__init__(
                f"children[? tag == 'build_curves'] | [0]"
                f".children[? tag == 'anchor'] | [*]"
                f".children[? tag == 'fit'] | [*][0]"
                f".children[? tag == 'epoch_train'] | [*][0]"
                f".children[? tag == 'epoch'] | [*][*]"
                f".metadata.value"
            )


class QueryMetricValuesFromEpochs(JsonQuery):
    """Extract the anchor children."""

    def __init__(self, metric_name: str, split_name: str = "val"):
        super().__init__(
            f"children[? tag == 'build_curves'] | [0]"
            f".children[? tag == 'anchor'] | [*]"
            f".children[? tag == 'fit'] | [*][0]"
            f".children[? tag == 'epoch_train'] | [*][0]"
            f".children[? tag == 'epoch'] | [*][*]"
            f".children[? tag == 'epoch_test'] | [*][*][0]"
            f".children[? tag == 'metrics'] | [*][*][0]"
            f".children[? tag == '{split_name}'] | [*][*][0]"
            f".children[? tag == '{metric_name}'] | [*][*][0]"
            f".metadata.value"
        )
