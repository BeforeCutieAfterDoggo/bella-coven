PREFIX = """
The following is an excerpt from a world-class tarot reading. The client has asked the question:
"""


def q1_prefix(card):

    return f"""
"The first card I will pull represents the past."

"Ah. **{card}**. This shows me that you"""


def q2_prefix(card):

    return f"""
"The second card I will pull represents the present."

"Hmmm. Interesting. **{card}** reveals itself. This means that right now you are"""


def q3_prefix(card):

    return f"""
"Finally, the third card I will pull represents the future."

"Oh! **{card}**. How interesting. In your future, I forsee"""