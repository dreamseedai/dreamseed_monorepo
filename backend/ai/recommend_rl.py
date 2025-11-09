import random


class RecommenderAgent:
    def __init__(self):
        self.q_table = {}  # state:emotion → action:content

    def recommend(self, emotion: str):
        if emotion in self.q_table:
            return max(self.q_table[emotion], key=self.q_table[emotion].get)
        return random.choice(["봄날", "고백장면", "먹방"])

    def update(self, emotion: str, content: str, reward: float):
        if emotion not in self.q_table:
            self.q_table[emotion] = {}
        if content not in self.q_table[emotion]:
            self.q_table[emotion][content] = 0
        self.q_table[emotion][content] += reward
