import json
from typing import Optional
from langfuse import observe
from src.services.auth_service import AuthService
from src.db.client import supabase
from datetime import date


class UserChecker:
    """Check users and suggest AI-based replacements."""

    def __init__(self, auth: AuthService):
        self.user_id = auth.get_user_id()
        self.users = supabase.table("users").select('*').eq('user_id', self.user_id).execute() if hasattr(supabase, "table") else None

    def identify_user(self) -> Optional[str]:
        """
        Generate a human-readable summary string for one or more user records.
        The method inspects self.users (which may be a Supabase-style response or an iterable of
        rows) and builds a comma-separated string containing Name, Gender, and Age for each row.
        Behavior:
        - If self.users is falsy, returns the empty string.
        - If self.users has a `.data` attribute, that attribute is used as the list of rows.
        - If self.users is a dict with a "data" key, that value is used as the list of rows.
        - Otherwise, self.users itself is treated as the iterable of rows.
        - If the resolved rows collection is empty or falsy, returns the empty string.
        - For each row (expected to be a dict-like object), the implementation tries to read:
            - "full_name" -> used for the Name field
            - "gender" -> used for the Gender field
            - "birth_date" -> parsed as "YYYY-MM-DD" and used to compute Age as
              date.today().year - birth_year (note: this is a simple year-difference and does not
              account for whether the birthday has occurred this year)
        - If no "full_name" is present, the row is fall-backed to a string via json.dumps(row)
          (or str(row) if json.dumps raises).
        - For each present piece of information, a fragment is added:
            "Name: {name}", "Gender: {gender}", "Age: {age}"
          All fragments for all rows are then joined with ", " and returned.
        - The method returns an empty string when there is no usable data; otherwise it returns the
          assembled comma-separated summary. Although the signature is Optional[str], the function
          uses the empty string to indicate "no result" rather than None.
        Dependencies / assumptions:
        - Uses date.today() (from datetime.date) for age computation.
        - Expects birth_date, when present, to be in "YYYY-MM-DD" format.
        - Rows are expected to be mapping-like (supporting .get); non-mapping rows will be stringified.
        """
        # Build a friendly string of all pantry items and their quantities.
        if not self.users:
            return ""

        # Normalize supabase response (it may be a dict with "data" or an object with .data)
        if hasattr(self.users, "data"):
            rows = self.users.data
        elif isinstance(self.users, dict) and "data" in self.users:
            rows = self.users["data"]
        else:
            rows = self.users

        if not rows:
            return ""

        parts = []
        for r in rows:
            # try common field names for ingredient name and quantity
            name = r.get("full_name")
            gender = r.get("gender")
            birth_date = r.get("birth_date")
            age = date.today().year - int(birth_date.split("-")[0]) if birth_date else None

            if name is None:
            # fallback: stringify the row if no identifiable name
                try:
                    name = json.dumps(r)
                except Exception:
                    name = str(r)

            if name is not None:
                parts.append(f"Name: {name}")
            if gender is not None:
                parts.append(f"Gender: {gender}")
            if age is not None:
                parts.append(f"Age: {age}")

        return ", ".join(parts)

    def preferences(self) -> Optional[str]:
        """
        Return a human-readable summary of user preferences aggregated from self.users.
        This method normalizes common Supabase response shapes and builds a comma-separated
        string containing identified preference fields for each user row.
        Behavior:
        - If self.users is falsy or contains no rows, returns an empty string.
        - If self.users has a .data attribute or is a dict with a "data" key, that value
            is used as the iterable collection of rows. Otherwise, self.users itself is
            treated as the collection of rows.
        - For each row (expected to be a mapping), the following keys are inspected:
                - "household_number"
                - "allergies"
                - "intolerances"
                - "restrictions"
                - "diet_type"
            If a key is present and its value is not None, a fragment like
            "Field Name: value" is appended to the output. Values are stringified.
        - If no identifiable name/value for a row can be produced and a fallback is needed,
            the implementation will attempt to JSON-serialize the row and fall back to str(row)
            if JSON serialization fails.
        - All fragments from all rows are joined with ", " and returned.
        Returns:
        - str: A comma-separated summary of preferences (may be an empty string if no data).
        Examples:
        - "Household Number: 2, Allergies: peanuts, Intolerances: lactose, Diet Type: vegan"
        - ""  (if there are no users or no rows)

        """

        # Build a friendly string of all pantry items and their quantities.
        if not self.users:
            return ""

        # Normalize supabase response (it may be a dict with "data" or an object with .data)
        if hasattr(self.users, "data"):
            rows = self.users.data
        elif isinstance(self.users, dict) and "data" in self.users:
            rows = self.users["data"]
        else:
            rows = self.users

        if not rows:
            return ""

        parts = []
        for r in rows:
            # try common field names for ingredient name and quantity
            household_number = r.get("household_number")
            allergies = r.get("allergies")
            intolerances = r.get("intolerances")
            restrictions = r.get("restrictions")
            diet_type = r.get("diet_type")

            if name is None:
            # fallback: stringify the row if no identifiable name
                try:
                    name = json.dumps(r)
                except Exception:
                    name = str(r)

            if household_number is not None:
                parts.append(f"Household Number: {household_number}")
            if allergies is not None:
                parts.append(f"Allergies: {allergies}")
            if intolerances is not None:
                parts.append(f"Intolerances: {intolerances}")
            if restrictions is not None:
                parts.append(f"Restrictions: {restrictions}")
            if diet_type is not None:
                parts.append(f"Diet Type: {diet_type}")
            
        return ", ".join(parts)
