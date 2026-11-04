"""Synthetic safety-classifier regressions; not clinical validation."""
import unittest

from therapybot.safety import classify


IMMEDIATE = [
    "I wrote goodbye notes and have a loaded gun beside me right now.",
    "I'm going to drive off the bridge tonight to end everything.",
    "I cut myself deeply and the bleeding will not stop.",
    "My partner took a huge overdose and can't stay awake.",
    "I am going to jump off a bridge today.",
    "I will jump in front of traffic tonight.",
    "I already swallowed forty tablets to die.",
    "I took enough pills to die twenty minutes ago.",
    "I am going to hurt my child tonight.",
    "I will kill my family tomorrow.",
    "I think my father will kill himself tonight.",
    "My boss plans to shoot everyone at work today.",
    "The voices tell me to jump out of the window right now, and I might do it.",
    "God commanded me to murder my family tonight, and I will obey.",
    "I think I'll end my life this weekend.",
    "I am going to disappear permanently tonight; I have the rope ready.",
    "I need help right now. I am going to cut my wrists.",
    "What if I kill myself tonight? I really might.",
    "I do not want to die, but I am going to shoot myself tonight.",
    "I have no plans to kill myself but I am going to jump off the roof today.",
    "I am writing a fictional story, and now I plan to kill myself tonight.",
    "I have a written suicide plan and I intend to use it tomorrow.",
    "I overdosed on purpose and I feel faint.",
    "My wife threatened to kill me tonight.",
    "A voice told me to attack the children and I think I will obey today.",
    "I decided to disappear for good tonight; the bridge is right here.",
    "My son has locked himself in a room with a gun and is saying goodbye.",
    "My spouse says they'll kill me tonight.",
    "I tried to hang myself yesterday and my throat hurts.",
]

CONCERN = [
    "I am thinking about ending it but I will not act today.",
    "I have slept 2 hours in 4 days and believe I can fly.",
    "I sometimes want to punch my partner.",
    "I sometimes wish I would never wake up.",
    "I feel like killing myself, but I have no plan.",
    "I keep hoping I will not wake up tomorrow.",
]

NORMAL = [
    "What does the phrase I want to die mean in a poem?",
    "I am not going to kill myself; I want to discuss prevention.",
    "I would never kill her.",
    "I will never kill him.",
    "I used to be suicidal in 2015, and I feel well now.",
    "Last year I said I would kill her, but I no longer feel that way.",
    "I'm writing a film about someone who wants to overdose.",
    "Please explain the grammar of 'I will kill myself'.",
    "My friend quoted the phrase I am going to kill myself in a classroom.",
    "I have no plans to kill myself.",
    "I do not want to kill myself.",
    "I was going to kill myself ten years ago, but I am safe now.",
    "I never actually intended to hurt myself.",
    "I swallowed my prescribed tablets with water this morning.",
    "I took several pills for a headache yesterday, as directed on the bottle.",
    "If my friend says they plan to kill themselves, how should I help?",
    "A friend said 'I will shoot myself tonight' in a play.",
]


class SafetyRegressionTests(unittest.TestCase):
    def test_immediate_synthetic_cases(self):
        for message in IMMEDIATE:
            with self.subTest(message=message):
                self.assertEqual("immediate", classify(message))

    def test_concern_synthetic_cases(self):
        for message in CONCERN:
            with self.subTest(message=message):
                self.assertEqual("concern", classify(message))

    def test_contextual_non_crisis_cases(self):
        for message in NORMAL:
            with self.subTest(message=message):
                self.assertEqual("normal", classify(message))

    def test_empty_string_is_normal(self):
        self.assertEqual("normal", classify(""))


if __name__ == "__main__":
    unittest.main()
