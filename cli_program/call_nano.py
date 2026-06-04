import argparse
import os
import subprocess
import sys
import tempfile




def nano_editor(blueprint:str=None):
    """
    Opens Nano to edit temporal file with a format
    """
    # Create a temporal file
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w+", delete=False) as tf:
        #to init with a blue print
        if blueprint:
            tf.write(blueprint)
            tf.flush()
        ruta_temporal = tf.name

    try:
        #suspends python and opens nano
        resultado = subprocess.run(["nano", ruta_temporal])

        if resultado.returncode != 0:
            print(
                "Error: The editor nano did not close correctly.",
                file=sys.stderr,
            )
            return None

        # Read the modified content by the user
        with open(ruta_temporal, "r", encoding="utf-8") as f:
            texto_editado = f.read()

        return texto_editado

    finally:
        # delete the temporal file always
        if os.path.exists(ruta_temporal):
            os.remove(ruta_temporal)


def main():
    # Setting up argparse
    parser = argparse.ArgumentParser(
        description="CLI to edit text with nano."
    )

    # Define a subcomando or argument to activate the editor
    parser.add_argument(
        "--editar",
        action="store_true",
        help="Opens nano to capture the setlist",
    )

    args = parser.parse_args()

    if args.editar:
        print("Opening nano... Edit the text, save (Ctrl+O) and exit (Ctrl+X)")

        texto_final = nano_editor()

        if texto_final:
            print("\n--- Text captured successfully ---")
            print(texto_final)
        else:
            print("Operation canceled or empty.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()