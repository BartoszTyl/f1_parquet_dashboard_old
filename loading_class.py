class Session():

    SESSION_MAP = {
        "race": "Race", "r": "Race",
        "qualifying": "Qualifying", "q": "Qualifying", "quali": "Qualifying",
        "sprint": "Sprint", "s": "Sprint",
        "sprint_qualifying": "Sprint Qualifying","sprint_qualifying": "Sprint Quali",
        "practice_1": "Practice 1", "fp1": "Practice 1", "p1": "Practice 1",
        "practice_2": "Practice 2", "fp2": "Practice 2", "p2": "Practice 2",
        "practice_3": "Practice 3", "fp3": "Practice 3", "p3": "Practice 3",
    }

    EVENT_CHOICES = {

    }

    def __init__(self, year: int, event: str, session: str):
        self.year = year
        # self.event = 
        self.session = self._normalize_session_type(session)

    def _event_fuzzy_matching(self, event: str, event_choice: str = EVENT_CHOICES):
        
        from rapidfuzz import process as rfp
        rfp.extractOne(event, event_choice)


    def _normalize_session_type(self, session: str) -> str:
        """
        Standardizes session type input.

        Arguments:
        - session (str): session which name will be normalized

        Return:
        - Normalized session name (str)
        """

        key = session.strip().lower()
        if key in self.SESSION_MAP:
            return self.SESSION_MAP[key]
        raise ValueError
        

    def __str__(self):
        pass
