BASE_PROMPT = (
    "apply the clothes and character traits from the second image to the character in the first one, including animal features (fur color, animal type, animal traits, skin color), if needed make the second pfp similar in the style of the first one if there are too many traits to transpose. change the pose if needed to reflect the character position in the second imageALWAYS KEEP THE TEARS"
)

def build_prompt() -> str:
    return BASE_PROMPT + " Keep the identity cues and overall composition from the second image."