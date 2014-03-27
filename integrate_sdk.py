import os, sys
from lxml import etree
import re
import urllib, zipfile, shutil

from file_utils import PatchFile

SDK_URL = "https://www.vessel.io/static/files/vesselsdk.zip"
TEMP_PATH = "/opt/tmp"
PROJECT_PATH = "/opt/projects2/testapp1"
SECRET_KEY = "adjasdu8asd7u89asdy89dy9adsady9as"

ns_android = '{http://schemas.android.com/apk/res/android}'


# 1
print "1. Updating manifest"
manifest_path = os.path.join(PROJECT_PATH, "AndroidManifest.xml")
manifest_tree = etree.parse(manifest_path)

activity = manifest_tree.xpath("//manifest/application/activity")[0]
name = activity.attrib['%sname' % ns_android]
act_name = name.split(".")[-1]

name = name.replace(".", "/") + ".java"
act_path = os.path.join(PROJECT_PATH, "src", name)

# update permissions

permission_el = etree.Element("uses-permission")
permission_el.attrib["%sname" % ns_android] = "android.permission.INTERNET"
manifest_el = manifest_tree.xpath("//manifest")[0]
manifest_el.append(permission_el)
del(permission_el)
permission_el = etree.Element("uses-permission")
permission_el.attrib["%sname" % ns_android] = "android.permission.ACCESS_NETWORK_STATE"
manifest_el.append(permission_el)

service_el = etree.Element("service")
service_el.attrib["%sname" % ns_android] = "com.vessel.service.VesselService"
manifest_el.append(service_el)

old_manifest_path = os.path.join(PROJECT_PATH, "AndroidManifest.xml.old")
os.rename(manifest_path, old_manifest_path)
new_manifest = open(manifest_path, "w")
new_manifest.write(etree.tostring(manifest_tree))
new_manifest.close()

# 2
print "2. Parsing and updating source"

patch = PatchFile(act_path)
patch.insert("public class %s.*?onCreate.*?{" % act_name,
            '\n        VesselSDK.initialize(getApplicationContext(), "%s");' % SECRET_KEY,
            is_regexp=True)

patch.insert("import ",
            "import com.vessel.VesselSDK;\n",
            before=True)
patch.save()

# 3
print "3. Downloading and adding SDK lib"
sdkzip_path = TEMP_PATH + "/vesselsdk.zip"
urllib.urlretrieve(SDK_URL, sdkzip_path)
with zipfile.ZipFile(sdkzip_path, "r") as z:
    z.extractall(TEMP_PATH)

for name in os.listdir(TEMP_PATH):
    dir_path = os.path.join(TEMP_PATH, name)
    if name.startswith("VesselSDK") and os.path.isdir(dir_path):
        break

dest_file = os.path.join(PROJECT_PATH, 'libs', 'vesselsdk.jar')
shutil.copy(os.path.join(dir_path, 'vesselsdk.jar'), dest_file)

# 4
print "4. Convert to aspectJ project"

dot_project_path = os.path.join(PROJECT_PATH, ".project")
patch = PatchFile(dot_project_path)
build_command = """             <buildCommand>
                        <name>org.eclipse.ajdt.core.ajbuilder</name>
                        <arguments>
                        </arguments>
                </buildCommand>\n"""
patch.insert("</buildSpec>",
             build_command,
             before=True)

patch.insert("<natures>",
             "\n\t\t\t<nature>org.eclipse.ajdt.ui.ajnature</nature>")
patch.save()

# classpath
dot_class_path = os.path.join(PROJECT_PATH, ".classpath")
patch = PatchFile(dot_class_path)
patch.insert("</classpath>",
             '<classpathentry kind="con" path="org.eclipse.ajdt.core.ASPECTJRT_CONTAINER"/>\n',
             before=True)
patch.save()

