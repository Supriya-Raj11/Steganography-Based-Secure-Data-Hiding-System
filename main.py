"""Hide text in image pixels, recover it, and measure image quality."""

import math
from pathlib import Path

try:
    from PIL import Image, ImageChops, ImageDraw, ImageOps, ImageStat
    from stegano import lsb
except ImportError:
    raise SystemExit("Install the libraries first: python -m pip install -r requirements.txt")

MARKER = "LSB1:"


def load_image(path):
    """Normalize image orientation and mode while preserving transparency."""
    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image)
        mode = "RGBA" if "A" in image.getbands() or "transparency" in image.info else "RGB"
        return image.convert(mode)


def extract_message(path):
    with load_image(path) as image:
        try:
            message = lsb.reveal(image, close_file=False)
        except (IndexError, ValueError):
            message = None
    if not message or not message.startswith(MARKER):
        raise ValueError("No readable message from this program was found.")
    return message[len(MARKER):]


def compare_images(original_path, hidden_path):
    """Calculate MSE and PSNR over the three 8-bit RGB channels."""
    with load_image(original_path) as first, load_image(hidden_path) as second:
        if first.size != second.size:
            raise ValueError("The images must have the same dimensions.")
        difference = ImageChops.difference(first.convert("RGB"), second.convert("RGB"))
        mse = sum(ImageStat.Stat(difference).sum2) / (first.width * first.height * 3)
    psnr = math.inf if mse == 0 else 10 * math.log10(255 ** 2 / mse)
    return mse, psnr


def save_comparison(original_path, hidden_path, comparison_path):
    """Save labeled previews; quality measurements use full-size images."""
    canvas = Image.new("RGB", (1000, 390), "white")
    draw = ImageDraw.Draw(canvas)
    for x, path, label in [(0, original_path, "Original"), (500, hidden_path, "Hidden message")]:
        with load_image(path) as image:
            preview = ImageOps.contain(image, (480, 340))
            canvas.paste(preview, (x + (500 - preview.width) // 2, 35),
                         preview if preview.mode == "RGBA" else None)
        draw.text((x + 15, 10), label, fill="black")
    with comparison_path.open("xb") as file:
        canvas.save(file, format="PNG")


def hide_message(original_path, message, output_path):
    original_path, output_path = Path(original_path), Path(output_path)
    if not message.strip():
        raise ValueError("Please enter a non-empty message.")
    if output_path.suffix.lower() != ".png":
        raise ValueError("The new image must have a .png extension.")
    if original_path.resolve() == output_path.resolve() or output_path.exists():
        raise ValueError("Choose a new output filename; existing files are kept unchanged.")
    payload = MARKER + message
    byte_count = len(payload.encode("utf-8"))
    # Stegano stores a byte count and ':' before the message.
    required_bits = (len(str(byte_count)) + 1 + byte_count) * 8
    with load_image(original_path) as image:
        if required_bits > image.width * image.height * 3:
            raise ValueError("The message is too large for this image. Use a larger image or shorter message.")
        hidden = lsb.hide(image, payload)
        with output_path.open("xb") as file:
            hidden.save(file, format="PNG")
        hidden.close()
    # Reopen the saved PNG so verification also checks file storage.
    if extract_message(output_path) != message:
        raise ValueError("The saved image failed message verification.")
    return compare_images(original_path, output_path)


def ask_path(prompt, default=None):
    value = input(prompt).strip().strip('"').strip("'")
    if not value and default is None:
        raise ValueError("Please enter an image path.")
    return Path(value).expanduser() if value else default


def show_quality(mse, psnr):
    print(f"MSE: {mse:.8f}")
    print("PSNR: infinity (identical RGB pixels)" if math.isinf(psnr) else f"PSNR: {psnr:.2f} dB")
    print("Higher PSNR means less pixel distortion; it does not measure secrecy.")


def main():
    print("LSB Image Steganography")
    while True:
        print("\n1. Hide a message\n2. Extract a message\n3. Compare images (PSNR)\n4. Exit")
        choice = input("Choose 1-4: ").strip()
        try:
            if choice == "1":
                original = ask_path("Original image path: ")
                message = input("Message to hide: ")
                default = original.with_name(original.stem + "_hidden.png")
                output = ask_path(f"New PNG path [Enter for {default}]: ", default)
                mse, psnr = hide_message(original, message, output)
                print(f"\nSaved image: {output.resolve()}")
                print(f"Message size: {len(message.encode('utf-8'))} bytes")
                print("Verification: saved image contains the exact original message.")
                show_quality(mse, psnr)
                comparison = output.with_name(output.stem + "_comparison.png")
                try:
                    save_comparison(original, output, comparison)
                    print(f"Visual comparison: {comparison.resolve()}")
                except OSError as error:
                    print(f"Could not save the optional comparison preview: {error}")
            elif choice == "2":
                path = ask_path("Image containing the hidden message: ")
                print("\nRecovered message:")
                print(extract_message(path))
            elif choice == "3":
                original = ask_path("Original image path: ")
                hidden = ask_path("Modified image path: ")
                show_quality(*compare_images(original, hidden))
            elif choice == "4":
                break
            else:
                print("Please choose 1, 2, 3, or 4.")
        except (OSError, ValueError, Image.DecompressionBombError) as error:
            print(f"Error: {error}")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nProgram closed.")
