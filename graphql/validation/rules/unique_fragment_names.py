from typing import Dict

from ...error import GraphQLError
from ...language import NameNode, FragmentDefinitionNode
from . import ASTValidationContext, ASTValidationRule

__all__ = ["UniqueFragmentNamesRule", "duplicate_fragment_name_message"]


def duplicate_fragment_name_message(frag_name):
    return "There can only be one fragment named '{}'.".format(frag_name)


class UniqueFragmentNamesRule(ASTValidationRule):
    """Unique fragment names

    A GraphQL document is only valid if all defined fragments have unique
    names.
    """

    def __init__(self, context):
        super(UniqueFragmentNamesRule, self).__init__(context)
        self.known_fragment_names = {}

    def enter_operation_definition(self, *_args):
        return self.SKIP

    def enter_fragment_definition(self, node, *_args):
        known_fragment_names = self.known_fragment_names
        fragment_name = node.name.value
        if fragment_name in known_fragment_names:
            self.report_error(
                GraphQLError(
                    duplicate_fragment_name_message(fragment_name),
                    [known_fragment_names[fragment_name], node.name],
                )
            )
        else:
            known_fragment_names[fragment_name] = node.name
        return self.SKIP
