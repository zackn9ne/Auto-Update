#!/usr/bin/python

"""
This script will prompt end users to quit apps, or force quit apps depending on the options passed
in the positional parameters
"""


# import modules
from Cocoa import NSRunningApplication
import sys
import subprocess
import os
import time

# jss side variables
APPLIST = sys.argv[4].split(",") #Parameter com.apple.InstallAssistant.Catalina
PROMPT = sys.argv[5].lower() # Parameter 5 prompt usually "true"
APPNAME = sys.argv[6]# Parameter 6 display name: macOS
UPDATEPOLICY = sys.argv[7]# Parameter 7 the event trigger 
SIGNOFFMSG = sys.argv[8]# Parameter 9 eg "Your I.T. Department"
LOGOPATH = sys.argv[9]# Parameter 10 eg "/Library/ADVisory/logonew.png"
README = sys.argv[10]# update or upgrade

SYMBOL = u"\u2764\ufe0f" # heart emoji, because we love Snowflake!
# signing off message

# message to prompt the user to quit and update an app
MESSAGE = """Your {0} is out of date

{1}

{2} {3}
""".format(
    APPNAME, README, SYMBOL.encode("utf-8"), SIGNOFFMSG
)


# message to notify the user upon completion
COMPLETE = """Step 2of3

{0} update has been successfully queued
""".format(
    APPNAME
)


# start functions
# this chunk for in case user info
from SystemConfiguration import SCDynamicStoreCopyConsoleUser
from Foundation import NSHomeDirectoryForUser
# grab current user info, in case we need it
USER, UID, GID = SCDynamicStoreCopyConsoleUser(None, None, None)

def check_if_running(bid):
    """Test to see if an app is running by bundle ID"""
    # macOS API to check if an app bundle is running or not
    app = NSRunningApplication.runningApplicationsWithBundleIdentifier_(bid)
    # return True if running, False if not
    if app:
        return True
    if not app:
        return False


def user_prompt(prompt):
    """simple jamf helper dialog box"""
    # set the path to your custom branding, it will default to the warning sign if your branding is not found
    icon = "{}".format(LOGOPATH)    # test to see what icons are available on the file system
    if not os.path.exists(icon):
        # default fail over icon in case our custom one does not exist
        icon = "/System/Library/CoreServices/Problem Reporter.app/Contents/Resources/ProblemReporter.icns"
    # build the jamf helper unix command in a list
    cmd = [
        "/Library/Application Support/JAMF/bin/jamfHelper.app/Contents/MacOS/jamfHelper",
        "-windowType",
        "utility",
        "-title",
        "Quit Applications",
        "-description",
        prompt,
        "-icon",
        icon,
        "-button1",
        "OK",
        "-button2",
        "Cancel",
        "-defaultbutton",
        "1",
    ]
    # call the command via subprocess
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # get stdout and stderr
    out, err = proc.communicate()
    # check for exit status for button clicked, 0 = OK 2 = Cancel
    if proc.returncode == 0:
        # user clicked OK
        return True
    if proc.returncode == 2:
        # user clicked cancel
        return False
    # if there is any other return print it
    else:
        print("Error: %s" % err)




def quit_application(bid):
    """quits apps using NSRunningApplication"""
    # use API to assign a variable for the running API so we can terminate it
    apps = NSRunningApplication.runningApplicationsWithBundleIdentifier_(bid)
    # API returns an array always, must iterate through it
    for app in apps:
        # terminate the app
        app.terminate()
        # if the app does not terminate in 3 seconds gracefully force it
        time.sleep(3)
        if not app.isTerminated():
            app.forceTerminate()


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
    # if you don't need to run an update policy, set to "false" to skip this
    if event == "false":
        pass
    # unix command list
    cmd = ["/usr/local/bin/jamf", "policy", "-event", event]
    # execute the policy to the binary
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # grab stdout and stderr pipes and communicate them to the shell
    out, err = proc.communicate()
    # if we get a non zero response, print the error
    if proc.returncode != 0:
        print("Error: %s" % err)


def notify_on_completion():
    """notification that the patch is complete"""
    # probably do not need this, can most likely reuse prior dialog box function
    # this is just a place holder for now
    pass


def run():
    """runs the workflow of the script"""
    # check to see if the app is not running, if it is not we are in luck we can update now!
    for app in APPLIST:
        if not check_if_running(app):
            answer = user_prompt(MESSAGE)
            # if they click OK, will return True value
            if answer:
                # quit the app, run the update, prompt to notify when complete
                #quit_application(bid)
                run_update_policy(UPDATEPOLICY)
                user_prompt(COMPLETE)
            if not answer:
                # if they click "Cancel" we will exit
                sys.exit(0)
    # use the bundle ID or IDs from parameter 4 and iterate through them
    for bid in APPLIST:
        # check if the app is running by bundle ID and we are choosing to prompt from parameter 5
        if check_if_running(bid) and PROMPT == "true":
            # prompt the user
            answer = user_prompt(MESSAGE)
            # if they click OK, will return True value
            if answer:
                # quit the app, run the update, prompt to notify when complete
                quit_application(bid)
                run_update_policy(UPDATEPOLICY)
                user_prompt(COMPLETE)
            if not answer:
                # if they click "Cancel" we will exit
                sys.exit(0)
        # if we pass the option to not prompt, just quit the app
        if check_if_running(bid) and PROMPT == "false":
            quit_application(bid)


# gotta have a main
if __name__ == "__main__":
    run()