def generate_agent_reply(session):
    """
    Very simple agent v1:
    Responds differently based on what we already know.
    """

    intel = session["intelligence"]

    if not intel["upiIds"]:
        return "Okay… which bank is this for? I have two accounts."

    if not intel["phishingLinks"]:
        return "They sent me a message earlier. Can you resend the link?"

    return "I’m trying to open it but it’s loading very slowly."
