import py_compile
import sys
import os

def check_project():
    files = ["apitor_robot.py", "apitor_gui.py"]
    all_ok = True
    
    print("--- Pre-flight Check ---")
    for f in files:
        if not os.path.exists(f):
            print(f"[ERROR] Missing file: {f}")
            all_ok = False
            continue
            
        try:
            py_compile.compile(f, doraise=True)
            print(f"[OK] Syntax check passed: {f}")
        except py_compile.PyCompileError as e:
            print(f"[FAIL] Syntax error in {f}:")
            print(e)
            all_ok = False
            
    if all_ok:
        print("\nAll files are syntactically correct and ready to run.")
    else:
        print("\nFix the errors above before running.")
        sys.exit(1)

if __name__ == "__main__":
    check_project()
