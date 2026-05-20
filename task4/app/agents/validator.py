import sqlparse
from typing import Tuple


class Validator:
    FORBIDDEN = {"drop", "delete", "update", "insert", "alter", "truncate"}

    def validate(self, sql: str) -> Tuple[bool, str]:
        """Return (is_valid, error_message). Ensures single-read-only SELECT statement."""
        if not sql or not sql.strip():
            return False, "Empty SQL"

        parsed = sqlparse.parse(sql)
        if len(parsed) == 0:
            return False, "Could not parse SQL"

        # ensure only SELECT statements
        for stmt in parsed:
            first_token = stmt.token_first(skip_cm=True)
            if not first_token:
                return False, "Malformed SQL"
            t = first_token.normalized.lower()
            if t != "select":
                return False, "Only SELECT statements are allowed"

        # check forbidden keywords anywhere
        lowered = sql.lower()
        for f in self.FORBIDDEN:
            if f in lowered:
                return False, f"Forbidden keyword detected: {f}"

        return True, "OK"
