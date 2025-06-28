import argparse
from enum import Enum
from multiprocessing import Pool
import zipfile
import os
from PIL import Image, ImageChops
import shutil
from tqdm import tqdm


class Device(Enum):
    kindle = (1246, 1648)  # kindle paperwhite 4
    kobo = (1072, 1448)  # kobo clara colour

    def __str__(self):
        return self.name


parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", type=str)
parser.add_argument("--device-width", type=int, default=1072)  # kindle: 1246
parser.add_argument("--device-height", type=int, default=1448)  # kindle: 1648
parser.add_argument("-w", "--workers", type=int, default=6)
parser.add_argument("-q", "--quality", type=int, default=50)
parser.add_argument("-d", "--device", type=str, choices=[d.name for d in Device])
args = parser.parse_args()

if args.device is not None:
    args.device_width, args.device_height = Device[args.device].value

# desired dimensions.
ratio = args.device_width / args.device_height
WIDTH = int(args.device_width * ratio)
HEIGHT = int(args.device_height * ratio)
QUALITY = args.quality


def trim(image: Image.Image) -> Image.Image:
    bg = Image.new(image.mode, image.size, "white")
    diff = ImageChops.difference(image, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()

    if bbox:
        return image.crop(bbox)
    return image


def process_file(root: str, file: str):
    filename, ext = os.path.splitext(file)
    if ext not in [".jpg", ".jpeg", ".png"]:
        # unsupported file type.
        return

    image = trim(Image.open(os.path.join(root, file)).convert("RGB"))
    width, height = image.size
    ratio = height / width

    image = image.resize((HEIGHT, int(HEIGHT * ratio)))
    width, height = image.size

    if height <= WIDTH:
        # nothing to do, original image already fits.
        return

    # remove original file.
    os.remove(os.path.join(root, file))

    # extract parts.
    top = image.crop((0, 0, HEIGHT, WIDTH))
    top.save(os.path.join(root, f"{filename}.1.jpg"), optimize=True, quality=QUALITY)

    middle = image.crop((0, (height - WIDTH) // 2, HEIGHT, (height + WIDTH) // 2))
    middle.save(os.path.join(root, f"{filename}.2.jpg"), optimize=True, quality=QUALITY)

    bottom = image.crop((0, height - WIDTH, HEIGHT, height))
    bottom.save(os.path.join(root, f"{filename}.3.jpg"), optimize=True, quality=QUALITY)


def zip_output(file: str):
    print("Creating archive...")
    suffix = "_processed"
    if args.device is not None:
        suffix = f"_{args.device}"

    filename, _ = os.path.splitext(file)
    shutil.make_archive(filename + suffix, "zip", "output")
    shutil.move(filename + suffix + ".zip", filename + suffix + ".cbz")
    shutil.rmtree("output")


def main():
    with zipfile.ZipFile(args.input, "r") as zipr:
        zipr.extractall("output")

    # remove __MACOSX directory if any.
    shutil.rmtree("output/__MACOSX", ignore_errors=True)

    all_files = []
    for root, _, files in os.walk("output"):
        for file in files:
            all_files.append((root, file))

    seen_first = False

    with tqdm(total=len(all_files)) as pbar:
        p = Pool(processes=args.workers)
        for root, file in sorted(all_files):
            # do not process the first file, it's the volume cover.
            if not seen_first:
                seen_first = True
                continue

            p.apply_async(
                process_file,
                (root, file),
                callback=lambda _: pbar.update(1),
                error_callback=lambda e: print(f"Error processing {file}: {e}"),
            )

        p.close()
        p.join()

    zip_output(args.input)


if __name__ == "__main__":
    main()
