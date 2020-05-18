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
APPLIST = sys.argv[4].split(",") #Parameter 4 us.zoom.xos
PROMPT = sys.argv[5].lower() # Parameter 5 prompt the user usually "true"
APPNAME = sys.argv[6]# Parameter 6 display name of the app in the dialog boxes, i.e. "Safari"
UPDATEPOLICY = sys.argv[7]# Parameter 7 the event trigger 
FORCEQUIT = sys.argv[8].lower() #Parameter 8 forcequit usually "false"
SIGNOFFMSG = sys.argv[9]# Parameter 9 eg "Your I.T. Department"
LOGOPATH = sys.argv[10]# Parameter 10 eg /Library/Application Support/JAMF/myorg/logonew.png
MESSAGEMAIN = """We would like to patch {0}. Please click on the "Update Now" button to continue, this will prompt you to quit your application and save your work.

You may click "Postpone" to delay this update and run it from Self Service at your convenience.

If you choose to update and quit, please wait until you receive confirmation that the app has been patched before reopening.
""".format(
    APPNAME
)
SYMBOL = u"\u2764\ufe0f" # heart emoji, because we love Snowflake!

# construct the message 
MESSAGE = """{0}
{1} {2}
""".format(
    MESSAGEMAIN, SYMBOL.encode("utf-8"), SIGNOFFMSG
)

# construct the force message
FORCEMSG = """Your {0} application is out of date

This is an emergency patch and the application will be quit to deploy security patches.

{1} {2}
""".format(
    APPNAME, SYMBOL.encode("utf-8"), SIGNOFFMSG
)


# message to notify the user upon completion
COMPLETE = """Thank You!

{0} has been patched on your system.  You may relaunch it now if you wish
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
        "Postpone",
        "-button2",
        "Update Now",
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
        return False
    if proc.returncode == 2:
        # user clicked cancel
        return True
    # if there is any other return print it
    else:
        print("Error: %s" % err)


def one_option_prompt(prompt):
    """jamf helper dialog to inform of the force quit"""
    # Custom branding icon path goes here for Force Quit work flows
    icon = "{}".format(LOGOPATH)    # test to see what icons are available on the file system
    # test to see what icons are available on the file system
    if not os.path.exists(icon):
        # default fail over icon in case our custom one does not exist
        icon = "/System/Library/CoreServices/Problem Reporter.app/Contents/Resources/ProblemReporter.icns"
    # build the jamf helper unix command in a list
    cmd1opt = [
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
        return False
    if proc.returncode == 2:
        # user clicked cancel
        return True
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
            run_update_policy(UPDATEPOLICY)
            sys.exit(0)
    # check to see if we are forcing the app to quit first, and take action
    if FORCEQUIT == "true":
        one_option_prompt(FORCEMSG)
        # loop through the bundle ID list
        for bid in APPLIST:
            # force quit the app and force the update via jamf policy
            force_quit_applicaiton(bid)
            run_update_policy(UPDATEPOLICY)
            user_prompt(COMPLETE)
        # if we are using the force we can exit here
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
                one_option_prompt(COMPLETE) #it's just a UX with one 
            if not answer:
                # if they click "Cancel" we will exit
                sys.exit(0)
        # if we pass the option to not prompt, just quit the app
        if check_if_running(bid) and PROMPT == "false":
            quit_application(bid)


# gotta have a main
if __name__ == "__main__":
    run()
