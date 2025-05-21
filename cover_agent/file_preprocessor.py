import ast
import textwrap


class FilePreprocessor:
    def __init__(self, path_to_file):
        self.path_to_file = path_to_file

        # List of rules/action key pair.
        # Add your new rule and how to process the text (function) here
        self.rules = [(self._is_python_file, self._process_if_python)]

    def process_file(self, text: str) -> str:
        """
        Process the text based on the internal rules.
        """
        for condition, action in self.rules:
            if condition():
                return action(text)
        return text  # Return the text unchanged if no rules apply

    def _is_python_file(self) -> bool:
        """
        Rule to check if the file is a Python file.
        """
        return self.path_to_file.endswith(".py")

    def _process_if_python(self, text: str) -> str:
        """
        Action to process Python files by checking for class definitions and indenting if found.
        """
        if self._contains_class_definition():
            return textwrap.indent(text, "    ")
        return text

    def _contains_class_definition(self) -> bool:
        """
        Check if the file contains a Python class definition using the ast module.
        """
        try:
            with open(self.path_to_file, "r") as file:
                content = file.read()
            parsed_ast = ast.parse(content)
            for node in ast.walk(parsed_ast):
                if isinstance(node, ast.ClassDef):
                    return True
        except SyntaxError as e:
            print(f"Syntax error when parsing the file: {e}")
        return False
