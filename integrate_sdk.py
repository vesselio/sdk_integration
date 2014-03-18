import os, sys
from lxml import etree
import re
import urllib, zipfile, shutil

SDK_URL = "https://www.vessel.io/static/files/vesselsdk.zip"
TEMP_PATH = "/opt/tmp"
PROJECT_PATH = "/opt/projects2/testapp1"
SECRET_KEY = "adjasdu8asd7u89asdy89dy9adsady9as"

ns_android = '{http://schemas.android.com/apk/res/android}'


# 1
print "1. Parsing and updating manifest"
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
act_src_file = open(act_path)
act_source = act_src_file.read()
act_src_file.close()

re_oncreate = re.compile("public class %s.*?onCreate.*?{" % act_name, re.DOTALL)
m = re_oncreate.search(act_source)
end_pos = m.end()
init_str = '\n        VesselSDK.initialize(getApplicationContext(), "%s");' % SECRET_KEY;
act_source = act_source[:end_pos] + init_str + act_source[end_pos:]

import_pos = act_source.find("import ")
import_str = "import com.vessel.VesselSDK;\n"
act_source = act_source[:import_pos] + import_str + act_source[import_pos:]

os.rename(act_path, act_path + ".old")
new_src_file = open(act_path, "w")
new_src_file.write(act_source)
new_src_file.close()

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
dot_project_file = open(dot_project_path)
dot_project = dot_project_file.read()
dot_project_file.close()

#dot_project_tree = etree.parse(dot_project_path)
#build_el = dot_project_tree.xpath("//buildSpec")[0]
#permission_el = etree.Element("buildCommand")

build_pos = dot_project.find("</buildSpec>")
build_command = """             <buildCommand>
                        <name>org.eclipse.ajdt.core.ajbuilder</name>
                        <arguments>
                        </arguments>
                </buildCommand>\n"""
dot_project = dot_project[:build_pos] + build_command + dot_project[build_pos:]

natures_str = "<natures>"
natures_pos = dot_project.find(natures_str) + len(natures_str)
nature_str = "\n\t\t\t<nature>org.eclipse.ajdt.ui.ajnature</nature>"

dot_project = dot_project[:natures_pos] + nature_str + dot_project[natures_pos:]
dot_project_file = open(dot_project_path, 'w')
dot_project_file.write(dot_project)
dot_project_file.close()

# classpath
dot_class_path = os.path.join(PROJECT_PATH, ".classpath")
dot_class_file = open(dot_class_path)
dot_class = dot_class_file.read()
dot_class_file.close()

classpath_str = "</classpath>"
classpath_pos = dot_class.find(classpath_str)
entry_str = '<classpathentry kind="con" path="org.eclipse.ajdt.core.ASPECTJRT_CONTAINER"/>\n'
dot_class = dot_class[:classpath_pos] + entry_str + dot_class[classpath_pos:]

dot_class_file = open(dot_class_path, 'w')
dot_class_file.write(dot_class)
dot_class_file.close()
