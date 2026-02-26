"""
Mapping of human-readable grammatical forms to Omorfi tags for uralicNLP.
"""

NOUN_CASES = {
    "Nominative": "+Nom",
    "Genitive": "+Gen",
    "Partitive": "+Par",
    "Inessive": "+Ine",
    "Elative": "+Ela",
    "Illative": "+Ill",
    "Adessive": "+Ade",
    "Ablative": "+Abl",
    "Allative": "+All",
    "Essive": "+Ess",
    "Translative": "+Tra"
}

NOUN_NUMBERS = {
    "Singular": "+Sg",
    "Plural": "+Pl"
}

VERB_TENSES_MOODS = {
    "Present": "+Ind+Prs",
    "Past": "+Ind+Prt",
    "Conditional": "+Cond+Prs"
}

VERB_PERSONS = {
    "1st Person Sg (I)": "+Sg1",
    "2nd Person Sg (You)": "+Sg2",
    "3rd Person Sg (He/She)": "+Sg3",
    "1st Person Pl (We)": "+Pl1",
    "2nd Person Pl (You)": "+Pl2",
    "3rd Person Pl (They)": "+Pl3",
    "Passive": "Passive" 
}

def get_noun_tag(case: str, number: str, pos: str = "N") -> str:
    """Returns the combined Omorfi tag for a noun or adjective."""
    return f"+{pos}{NOUN_NUMBERS.get(number, '+Sg')}{NOUN_CASES.get(case, '+Nom')}"

def get_verb_tag(tense_mood: str, person: str) -> str:
    """Returns the combined Omorfi tag for a verb."""
    if person == "Passive":
        # Passives are formed differently (e.g. +V+Pss+Ind+Prs+Pe4)
        return f"+V+Pss{VERB_TENSES_MOODS.get(tense_mood, '+Ind+Prs')}+Pe4"
    else:
        # Action verbs (e.g., +V+Act+Ind+Prs+Sg1)
        return f"+V+Act{VERB_TENSES_MOODS.get(tense_mood, '+Ind+Prs')}{VERB_PERSONS.get(person, '+Sg3')}"
