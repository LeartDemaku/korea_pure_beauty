"""
Krijo_Ikone_Desktop.py
Skript per krijimin e shortcut te Korea Pure Beauty ne Desktop.
Ekzekuto kete skript nje here per te vendosur ikonën.
"""
import os
import sys
import win32com.client

def get_project_dir():
    return os.path.dirname(os.path.abspath(__file__))

def create_desktop_shortcut():
    project_dir = get_project_dir()
    vbs_launcher = os.path.join(project_dir, 'launch_client.vbs')
    
    if not os.path.exists(vbs_launcher):
        print(f"GABIM: Skedari launch_client.vbs nuk u gjet ne: {vbs_launcher}")
        return False

    try:
        shell = win32com.client.Dispatch('WScript.Shell')
        desktop_folder = shell.SpecialFolders('Desktop')
        shortcut_path = os.path.join(desktop_folder, 'Korea Pure Beauty.lnk')
        
        shortcut = shell.CreateShortcut(shortcut_path)
        shortcut.TargetPath = vbs_launcher
        shortcut.WorkingDirectory = project_dir
        shortcut.Description = 'Korea Pure Beauty - Dyqani dhe Shporta per Kliente'
        # Perdor ikonen zyrtare te Korea Pure Beauty
        icon_path = os.path.join(project_dir, 'assets', 'app_icon.ico')
        if os.path.exists(icon_path):
            shortcut.IconLocation = f"{icon_path},0"
        else:
            shortcut.IconLocation = sys.executable + ',0'
        shortcut.Save()
        
        print(f"OK Shortcut u krijua me sukses ne Desktop:")
        print(f"   {shortcut_path}")
        print()
        print("INFO Tani mund te klikoni dy here mbi 'Korea Pure Beauty' ne Desktop")
        print("     per te hapur drejtperdrejt Dyqanin per Klientet!")
        return True
    except Exception as e:
        print(f"GABIM gjate krijimit te shortcut: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("   Korea Pure Beauty - Desktop Shortcut Creator")
    print("=" * 60)
    print()
    create_desktop_shortcut()
    print()
    input("Shtypni ENTER per te mbyllur...")
