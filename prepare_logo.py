from pathlib import Path

from PIL import Image


BASE_DIR = Path(__file__).resolve().parent
SOURCE = BASE_DIR / "static" / "maaden-logo.png"
OUTPUT = BASE_DIR / "static" / "maaden-logo-centered.png"


def main():
    if not SOURCE.exists():
        raise FileNotFoundError(
            f"Logo not found: {SOURCE}"
        )

    image = Image.open(SOURCE).convert("RGBA")
    cleaned = Image.new("RGBA", image.size, (0, 0, 0, 0))

    source_pixels = image.load()
    cleaned_pixels = cleaned.load()

    for y in range(image.height):
        for x in range(image.width):
            red, green, blue, alpha = source_pixels[x, y]

            is_gold = (
                alpha > 0
                and red > 80
                and green > 60
                and red > blue * 1.15
                and green > blue * 1.05
            )

            if is_gold:
                cleaned_pixels[x, y] = (
                    red,
                    green,
                    blue,
                    alpha,
                )

    bounding_box = cleaned.getchannel("A").getbbox()

    if bounding_box is None:
        raise ValueError(
            "No gold pixels were detected in the logo."
        )

    cropped = cleaned.crop(bounding_box)
    padding = 18

    final_image = Image.new(
        "RGBA",
        (
            cropped.width + padding * 2,
            cropped.height + padding * 2,
        ),
        (0, 0, 0, 0),
    )

    final_image.paste(
        cropped,
        (padding, padding),
        cropped,
    )

    final_image.save(OUTPUT)

    print("Logo prepared successfully.")
    print(f"Original size: {image.size}")
    print(f"Final size: {final_image.size}")
    print(f"Saved to: {OUTPUT}")


if __name__ == "__main__":
    main()