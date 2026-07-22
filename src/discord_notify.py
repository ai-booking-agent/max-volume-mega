import subprocess

from . import config

_COPY_IMAGE_SCRIPT = '''
set the clipboard to (read (POSIX file "{path}") as «class PNGf»)
'''

_NOTIFY_SCRIPT = '''
display notification "{body}" with title "Max Volume Mega" sound name "Glass"
'''


def prepare_manual_send(image_path, message):
    """Copies the screenshot to the clipboard and opens the target Discord
    channel so you can paste (Cmd+V) and send it yourself. Deliberately does
    NOT post anything programmatically — automating a personal Discord
    account to send messages violates Discord's Terms of Service, whether via
    the API or via browser automation. This only does the prep work; a human
    still has to press send.
    """
    copy_script = _COPY_IMAGE_SCRIPT.format(path=str(image_path))
    result = subprocess.run(["osascript", "-e", copy_script], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to copy screenshot to clipboard: {result.stderr.strip()}")

    subprocess.run(["open", config.DISCORD_CHANNEL_URL], check=True)

    notify_script = _NOTIFY_SCRIPT.format(
        body="Screenshot copied to clipboard — paste (Cmd+V) into the channel and hit Send"
    )
    subprocess.run(["osascript", "-e", notify_script], capture_output=True, text=True)
