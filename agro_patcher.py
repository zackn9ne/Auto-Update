#!/usr/bin/python
"""
This script will silently patch any app by bundle ID, but only if the app itself is not running
you must supply the bundle ID of the app to check and the policy event manual trigger for jamf as
positional parameters 4 and 5

fork: zackn9ne use with caution
"""

# import modules
from Cocoa import NSRunningApplication
import sys
import subprocess


# global vars
# bundle ID of the app to check
# you may supply multiple bundle IDs by adding them comma separated as a parameter in jamf pro
# in the event a developer changes the bundle ID
#APPS = sys.argv[4].split(",")
APPS = "com.apple.Safari"
# update policy to run, supply the custom policy event name, i.e. install_app02
#POLICY = sys.argv[5]


# start functions


def check_if_running(bid):
    """Test to see if an app is running by bundle ID"""
    # macOS API to check if an app bundle is running or not
    app = NSRunningApplication.runningApplicationsWithBundleIdentifier_(bid)
    # return True if running, False if not
    if app:
        return True
    if not app:
        return False
    
def force_quit_applicaiton(bid):
    """force an application to quit for emergency workflows"""
    # use API to assign a variable for the running API so we can FORCE terminate it
    apps = NSRunningApplication.runningApplicationsWithBundleIdentifier_(bid)
    # API returns an array always, must iterate through it
    for app in apps:
        # terminate the app
        app.forceTerminate()



def run_update_policy(event):
    """run the updater policy for the app"""
    # unix command list
    cmd = ["/usr/local/bin/jamf", "policy", "-event", event]
    # execute the policy to the binary
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # grab stdout and stderr pipes and communicate them to the shell
    out, err = proc.communicate()
    # if we get a non zero response, print the error
    if proc.returncode != 0:
        print("Error: %s" % err)


def main():
    """main policy to run the jewels"""
    # iterate through bundle IDs for the edge case a developer changes a bundle ID
    # if the app is running, we will silently exit
    force_quit_applicaiton(APPS)
    #run_update_policy(POLICY)
    thing = subprocess.Popen("pwd", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print thing.communicate()



# run the main
if __name__ == "__main__":
    main()
