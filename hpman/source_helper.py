class SourceHelper:
    """Helper class to format source code for debugging."""

    def __init__(self, source: str) -> None:
        """Create a SourceHelper given source code.

        :param source: source code to be parsed
        """
        self.source = source
        self.lines = source.split("\n")

    @classmethod
    def from_file(cls, path: str) -> "SourceHelper":
        """Create a SourceHelper given file path.

        :param path: file path of the source code
        """
        with open(path) as f:
            return cls(f.read())

    def format_lines(
        self, from_line: int, to_line: int, lineno: int, *, indent_spaces: int = 0
    ) -> str:
        """Format a range of lines of code.

        :param from_line: range start of lines to be formatted. one-based, closed-interval.
        :param to_line: range end of lines to be formatted. one-based, closed-interval.
        :param lineno: current line number, one-based, closed-interval.
        :param indent_spaces: number of spaces to be prepended at each line.

        :return: formatted string of source code
        """
        assert 1 <= from_line <= lineno <= to_line <= len(self.lines), (
            from_line,
            lineno,
            to_line,
            len(self.lines),
        )
        from_line -= 1
        to_line -= 1
        lineno -= 1

        lines = self.lines[from_line : to_line + 1]

        rows = []

        # a formatter template to align the widths of line numbers
        num_width = len(str(to_line))
        num_template = "{{:{}}}".format(num_width)

        lineno_rela = lineno - from_line

        for i, line in enumerate(lines):
            if i != lineno_rela:
                prompt = "    "
            else:
                prompt = "==> "

            num_str = num_template.format(from_line + i + 1)

            row = "{}{}: {}".format(prompt, num_str, line)
            rows.append(row)

        # add indentations
        rows = [" " * indent_spaces + row for row in rows]

        return "\n".join(rows)

    def format_line_with_context(
        self, lineno: int, before: int = 5, after: int = 5, **kwargs
    ) -> str:
        """One-Line-Of-Code-Centric formatting.

        :param lineno: line to be displayed
        :param before: number of lines before *lineno*
        :param after: number of lines after *lineno*

        :return: formatted string of source code
        """
        return self.format_lines(
            max(1, lineno - before),
            min(len(self.lines), lineno + after),
            lineno,
            **kwargs
        )

    def format_given_filename_and_lineno(
        self, filename: str, lineno: int, **kwargs
    ) -> str:
        return self.format_given_filename_and_source_and_lineno(
            filename, self.source, lineno, **kwargs
        )

    @classmethod
    def format_given_source_and_lineno(cls, source: str, lineno: int, **kwargs) -> str:
        """Akin to :meth:`.format_line_with_context`, but source is given.

        :param source: source code string
        :param lineno: line to be displayed

        :return: formatted string of source code
        """
        return cls(source).format_line_with_context(lineno, **kwargs)

    @classmethod
    def format_given_filename_and_source_and_lineno(
        cls,
        filename: str,
        source: str,
        lineno: int,
        *,
        indent_spaces: int = 0,
        **kwargs
    ) -> str:
        """Akin to :meth:`.format_given_source_and_lineno`, but filename is
            given, and will be formatted as well.

        :param filename: file name to be displayed. It has nothing to do with
            the content of the source code and is purely for display purpose.
        :param source: soure code to be parsed
        :param lineno: line to be displayed
        :param indent_spaces: number of spaces to be prepended at each line.

        :param filename: filename
        """
        prompt = " " * indent_spaces + "{}:{}".format(filename, lineno)
        src = cls.format_given_source_and_lineno(source, lineno)
        return prompt + "\n" + src

    @classmethod
    def format_given_filepath_and_lineno(cls, path: str, lineno: int, **kwargs) -> str:
        """Akin to :meth:`.format_given_source_and_lineno`, but source is read
        from given file.

        :param path: path to the source code
        :param lineno: line to be displayed
        """
        if path is None or path == "<unknown>":
            src = ""
        else:
            with open(path) as f:
                src = f.read()

        if lineno is None:
            lineno = 1

        return cls.format_given_filename_and_source_and_lineno(
            path, src, lineno, **kwargs
        )
