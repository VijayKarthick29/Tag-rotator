import os
import sys
import subprocess

STARTUP_DIR = os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_VBS = os.path.join(SCRIPT_DIR, "run_badge_rotator_background.vbs")
SHORTCUT_PATH = os.path.join(STARTUP_DIR, "DiscordServerTagRotator.lnk")


def install():
    print("=" * 60)
    print("Installing 24/7 Permanent Auto-Start on Windows...")
    print("=" * 60)

    # Use WScript.Shell to create shortcut in Startup folder
    vbs_script = f'''
Set sh = CreateObject("WScript.Shell")
Set sc = sh.CreateShortcut("{SHORTCUT_PATH.replace(chr(92), chr(92)+chr(92))}")
sc.TargetPath = "wscript.exe"
sc.Arguments = """{TARGET_VBS.replace(chr(92), chr(92)+chr(92))}"""
sc.WorkingDirectory = """{SCRIPT_DIR.replace(chr(92), chr(92)+chr(92))}"""
sc.Save
'''
    temp_vbs = os.path.join(SCRIPT_DIR, "temp_create_shortcut.vbs")
    with open(temp_vbs, "w", encoding="utf-8") as f:
        f.write(vbs_script)

    os.system(f'cscript //nologo "{temp_vbs}"')
    if os.path.exists(temp_vbs):
        os.remove(temp_vbs)

    if os.path.exists(SHORTCUT_PATH):
        print("\n[SUCCESS] Installed to Windows Startup!")
        print(f"Location: {SHORTCUT_PATH}")
        print("\n[INFO] Starting the bot silently in background right now...")
        os.system(f'wscript.exe "{TARGET_VBS}"')
        print("[SUCCESS] Bot is now permanently running in the background!")
        print("You can close any windows. The bot will automatically start every time your PC turns on.")
    else:
        print("[ERROR] Failed to create shortcut in Startup folder.")


def uninstall():
    print("=" * 60)
    print("Uninstalling 24/7 Auto-Start...")
    print("=" * 60)
    if os.path.exists(SHORTCUT_PATH):
        os.remove(SHORTCUT_PATH)
        print("[SUCCESS] Removed from Windows Startup.")
    else:
        print("[INFO] Not found in Startup.")

    os.system("taskkill /F /IM pythonw.exe >nul 2>&1")
    print("[SUCCESS] Stopped any running background bots.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "uninstall":
        uninstall()
    else:
        install()
