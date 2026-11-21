# Steganography-based Secure Data Hiding System

Project No. 12. A small Python terminal program that hides a text message in an
image using least significant bits (LSB), extracts it, and compares image quality.

## Start the program

You need Python 3.10 or newer. On Windows, double-click **run.bat**. The first run
creates a local Python environment and installs the libraries, so internet access
is required during setup. Later runs use that environment. If Windows opens the
Microsoft Store instead of Python, install Python from https://www.python.org/
and enable its PATH option.

Alternatively, open a terminal in this folder and run:

```text
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python main.py
```

On macOS/Linux, use `python3 -m venv .venv` and `.venv/bin/python` for the last two
commands. Relative image paths are relative to the terminal's current folder;
full paths work too, including paths with spaces or surrounding quotes.

## Input and output

| Operation | Your input | Program output |
| --- | --- | --- |
| Hide a message | Original image path, one line of text, new `.png` path | New image, exact recovery check, MSE, PSNR, labeled comparison preview |
| Extract a message | Path to a hidden PNG made by this program | Original text, without needing the cover image |
| Compare images | Original image path and modified image path | MSE and PSNR; dimensions must match |

PNG, JPEG, BMP, and other static formats readable by Pillow can be used as the
original. Output is always a PNG so the pixel bits survive saving. For animated
images, only the first frame is used. The original is kept unchanged. Existing
output files are rejected; choose a different name when repeating a run.

The message prompt accepts one line, including Unicode characters and spaces.
It rejects an empty or whitespace-only message. Entering a filename such as
`message.txt` at that prompt hides the literal filename, not the file contents.

## Try the included example

Choose option `1` and enter:

```text
Original image path: examples/sample_cover.png
Message to hide: Meet me at the library at 5 PM.
New PNG path: examples/my_hidden.png
```

You may leave the new PNG path blank to use `<original_name>_hidden.png` beside
the original. The preview is named `<new_name>_comparison.png`. For this example,
the result is:

```text
Saved image: .../examples/my_hidden.png
Message size: 31 bytes
Verification: saved image contains the exact original message.
MSE: 0.00017578
PSNR: 85.68 dB
Higher PSNR means less pixel distortion; it does not measure secrecy.
Visual comparison: .../examples/my_hidden_comparison.png
```

Then choose option `2` and enter `examples/my_hidden.png`:

```text
Recovered message:
Meet me at the library at 5 PM.
```

The `examples` folder already contains `sample_hidden.png` and
`sample_comparison.png` from a verified run with the same message. You can extract
from `sample_hidden.png` immediately. Extract from the hidden PNG, not the
comparison preview: the preview is resized for viewing and does not preserve the
message. Resizing, cropping, filters, or JPEG conversion can destroy hidden data.

## How it works

An RGB pixel has red, green, and blue values from 0 to 255. LSB embedding replaces
the final binary bit of a channel with one message bit. For example, replacing
the final bit of `10010110` with `1` produces `10010111`: the value changes from
150 to 151. That small change is usually difficult to see.

1. Pillow loads the cover, normalizes its orientation, and converts it to RGB or
   RGBA. Transparency is retained and alpha values are not used for hiding.
2. The program adds the `LSB1:` identifier to recognize its own messages.
3. Stegano encodes the text as UTF-8, adds its byte-length prefix and `:`, and
   writes one bit in each red, green, and blue channel in pixel order.
4. The program saves the result as PNG, reopens it, and checks that extraction
   returns the exact original message.
5. It compares the full-resolution RGB pixels and saves a separate visual preview.

Raw capacity is `width × height × 3` bits. The identifier and length prefix use
some space, so usable text capacity is slightly smaller. UTF-8 characters can use
multiple bytes. The size check counts bytes, not just visible characters.

## Image quality and security verification

For equal-sized 8-bit RGB images, let `N = width × height × 3`:

```text
MSE  = sum((original_channel - modified_channel)^2) / N
PSNR = 10 × log10(255^2 / MSE) dB
```

Lower MSE and higher PSNR indicate less pixel distortion. Identical RGB pixels
give MSE = 0 and PSNR = infinity. The program uses decoded, orientation-corrected
RGB pixels as the reference, including when the input is JPEG or grayscale.
Alpha and file-size differences are not included in this metric. The comparison
preview uses resized images; measurements use the full-resolution originals.

For a demonstration, show the original and hidden image, report PSNR, then
extract the exact message from the saved PNG. This demonstrates concealment and
successful recovery. **LSB is not encryption.** Anyone who knows the method can
try extracting the message; the identifier is not a password or authentication
check. A high PSNR does not prove that hidden data is undetectable or confidential.

## Code guide

The application is in one file, `main.py`:

- `load_image`: opens and normalizes an image.
- `hide_message`: checks inputs, hides text, saves PNG, and verifies recovery.
- `extract_message`: reads the hidden text and checks the identifier.
- `compare_images`: calculates MSE and PSNR.
- `save_comparison`: creates the labeled side-by-side preview.
- `main`: runs the four-option menu.

Pillow handles image operations; Stegano handles LSB encoding and decoding.
Python's standard library supplies paths and logarithms. Stegano's package
installer also installs its own dependencies; those are managed automatically.

References: [Stegano](https://pypi.org/project/stegano/),
[Pillow documentation](https://pillow.readthedocs.io/en/stable/).
