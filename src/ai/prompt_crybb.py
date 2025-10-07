BASE_PROMPT = (
  "change the clothes of the first character to the clothes of the character in the second image, "
  "if needed change his hair color, skin color, eyes color and tattoos in case they are different from the original image. "
  "keep the style consistent to the one in the first image. VERY IMPORTANT, always keep the tears."
)


def build_prompt() -> str:
    return BASE_PROMPT + " Keep the identity cues and overall composition from the second image."


