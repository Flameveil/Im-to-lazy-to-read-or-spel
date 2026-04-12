import subprocess, platform

current_os = platform.system()
windows = True
if current_os == "Windows":
    pass
elif current_os == "Darwin":
    windows = False

# running processes
if not windows:
    print("You are on macOS.")
    subprocess.run(["open", "-W", "-a", "TextEdit"]) # -W means wait for app to close
else:
    print("You are on Windows. Opening notepad")
    subprocess.run(["notepad.exe"]) 

print("Sorry, I had to wait till the subprocess finished...")

# suppose I wanted to open a number of processes concurrently and not wait ...
for i in range(5):
    if not windows:
        subprocess.Popen(["open", "-n", "-a", "TextEdit"]) # -n means new app instance
    else:
        subprocess.Popen(["notepad.exe"])
    
subprocess.Popen(["python","timer.py"])
print("Done and I didn't have to wait!")