"""Conservative, content-specific map reveals; unknown/localized names fail closed."""
from pathlib import Path

FALLOUT2 = ("Arroyo", "Klamath", "The Den", "Den", "Modoc", "Vault City", "Gecko",
            "Redding", "Broken Hills", "New Reno", "NCR", "San Francisco")
ETTU = ("Vault 13", "Shady Sands", "Junktown", "The Hub", "Hub", "Necropolis",
        "Boneyard", "Adytum", "The Glow", "Glow", "The Brotherhood", "Brotherhood")


def write_locations(profile, content="fallout2"):
    dest = Path(profile) / "data/wasteland/locations.txt"
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Unlink first: profile assets may be hardlinks into a shared mod cache.
    if dest.exists() or dest.is_symlink():
        dest.unlink()
    dest.write_text("# Wasteland reveal whitelist: " + content + "\n" +
                    "\n".join(ETTU if content == "ettu" else FALLOUT2) + "\n")
    return dest
