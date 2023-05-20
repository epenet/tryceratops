import ast
import typing as t

from tryceratops.violations import codes

from .base import BaseAnalyzer, visit_error_handler


class NonPickableAnalyzer(BaseAnalyzer):
    violation_code = codes.NON_PICKABLE_CLASS

    def _find_method(self, node: ast.ClassDef, name: str) -> t.Optional[ast.FunctionDef]:
        for method in node.body:
            if isinstance(method, ast.FunctionDef) and method.name == name:
                return method

        return None

    @visit_error_handler
    def visit_ClassDef(self, node: ast.ClassDef) -> t.Any:
        is_exc = any([base for base in node.bases if getattr(base, "id") == "Exception"])
        if is_exc is False:
            return self.generic_visit(node)

        init_method = self._find_method(node, "__init__")
        if init_method is None:
            return self.generic_visit(node)

        reduce_method = self._find_method(node, "__reduce__")
        if reduce_method is not None:
            # Good enough to say this is not a violation
            return self.generic_visit(node)

        # First arg would be self
        has_more_than_one_arg = len(init_method.args.args) > 1
        if has_more_than_one_arg is False:
            return self.generic_visit(node)

        _, second_arg, *remaining_args = init_method.args.args
        if (
            len(remaining_args) > 0
            or second_arg.annotation
            and getattr(second_arg.annotation, "id") != "str"
        ):
            # Pickle would break for non string args or for more than 1 arg
            self._mark_violation(node)
