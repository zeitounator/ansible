#!powershell
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#AnsibleRequires -PowerShell ..module_utils.validate

$module = [Ansible.Basic.AnsibleModule]::Create($args, @{})
$module.ExitJson()
