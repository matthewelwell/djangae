import os
import stat
import subprocess
import shutil

from StringIO import StringIO
from zipfile import ZipFile
from urllib import urlopen


PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
REQUIREMENTS_FILE = os.path.join(PROJECT_DIR, "requirements.txt")
TARGET_DIR = os.path.join(PROJECT_DIR, "libs")

APPENGINE_TARGET_DIR = os.path.join(TARGET_DIR, "google_appengine")

APPENGINE_SDK_VERSION = "1.9.22"
APPENGINE_SDK_FILENAME = "google_appengine_%s.zip" % APPENGINE_SDK_VERSION

# Google move versions from 'featured' to 'deprecated' when they bring
# out new releases
FEATURED_SDK_REPO = "https://storage.googleapis.com/appengine-sdks/featured/"
DEPRECATED_SDK_REPO = "https://storage.googleapis.com/appengine-sdks/deprecated/%s/" % APPENGINE_SDK_VERSION.replace('.', '')

DJANGO_VERSION = os.environ.get("DJANGO_VERSION", "1.6")
NEXT_DJANGO_VERSION = {
    "1.5": "1.6",
    "1.6": "1.7",
    "1.7": "1.8",
    "1.8": "1.9",
    "1.9": "2.0",
    "2.0": "2.1",
}

if DJANGO_VERSION != "master":
    DJANGO_FOR_PIP = "https://github.com/django/django/archive/stable/{}.x.tar.gz".format(DJANGO_VERSION)
    DJANGO_TESTS_URL = "https://github.com/django/django/archive/stable/{}.x.zip".format(DJANGO_VERSION)
else:
    DJANGO_FOR_PIP = "https://github.com/django/django/archive/master.tar.gz"
    DJANGO_TESTS_URL = "https://github.com/django/django/archive/master.zip"

if __name__ == '__main__':

    if os.path.exists(TARGET_DIR):
        shutil.rmtree(TARGET_DIR)

    if not os.path.exists(APPENGINE_TARGET_DIR):
        print('Downloading the AppEngine SDK...')

        #First try and get it from the 'featured' folder
        sdk_file = urlopen(FEATURED_SDK_REPO + APPENGINE_SDK_FILENAME)
        if sdk_file.getcode() == 404:
            #Failing that, 'deprecated'
            sdk_file = urlopen(DEPRECATED_SDK_REPO + APPENGINE_SDK_FILENAME)

        #Handle other errors
        if sdk_file.getcode() >= 299:
            raise Exception('App Engine SDK could not be found. {} returned code {}.'.format(sdk_file.geturl(), sdk_file.getcode()))

        zipfile = ZipFile(StringIO(sdk_file.read()))
        zipfile.extractall(TARGET_DIR)

        #Make sure the dev_appserver and appcfg are executable
        for module in ("dev_appserver.py", "appcfg.py"):
            app = os.path.join(APPENGINE_TARGET_DIR, module)
            st = os.stat(app)
            os.chmod(app, st.st_mode | stat.S_IEXEC)
    else:
        print('Not updating SDK as it exists. Remove {} and re-run to get the latest SDK'.format(APPENGINE_TARGET_DIR))

    print("Running pip...")
    args = ["pip", "install", "--no-deps", "-r", REQUIREMENTS_FILE, "-t", TARGET_DIR, "-I"]
    p = subprocess.Popen(args)
    p.wait()

    print("Installing Django {}".format(DJANGO_VERSION))
    args = ["pip", "install", "--no-deps", DJANGO_FOR_PIP, "-t", TARGET_DIR, "-I", "--no-use-wheel"]
    p = subprocess.Popen(args)
    p.wait()

    print("Installing Django tests from {}".format(DJANGO_VERSION))
    django_zip = urlopen(DJANGO_TESTS_URL)
    zipfile = ZipFile(StringIO(django_zip.read()))
    for filename in zipfile.namelist():
        if filename.startswith("django-stable-{}.x/tests/".format(DJANGO_VERSION)) or filename.startswith("django-master/tests/"):
            zipfile.extract(filename, os.path.join(TARGET_DIR))
