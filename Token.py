class Token:
    def __init__(
        self,
        indices,
        syntax_node,
        token_id,
        source: str,
        changed=False,
        last_edited=None,
    ):
        self.start, self.end = indices
        self.syntax_node = syntax_node
        self.id = token_id
        self.changed = changed
        self.source = source
        self.last_edited = last_edited

    @staticmethod
    def from_capture_tuple(capture, source, token_id=None):
        (start, end), syntax_node = capture
        return Token((start, end), syntax_node, token_id, source)

    def range(self):
        return (self.start, self.end)

    def shift(self, n=0):
        return Token(
            (self.start + n, self.end + n),
            self.syntax_node,
            self.id,
            self.source,
            changed=self.changed,
            last_edited=self.last_edited,
        )

    def __repr__(self,):
        return f"range: [{self.start}, {self.end}], syntax_node: {self.syntax_node}, id: {self.id}, changed: {self.changed}"

    def overlaps(self, range_or_int):
        if isinstance(range_or_int, (tuple, list)):
            assert (
                len(range_or_int) == 2
            ), "Token.overlaps: range must be a tuple/list of length 2"
            start, end = range_or_int
            if self.start >= start and self.start < end:
                return True
            if self.end > start and self.end <= end:
                return True
        elif isinstance(range_or_int, int):
            if range_or_int >= self.start and range_or_int < self.end:
                return True
        return False

    def text(self):
        return self.source[self.start : self.end]

