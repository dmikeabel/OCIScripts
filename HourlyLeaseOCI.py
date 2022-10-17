import oci
import datetime
import pytz

##########################################################################
# Print header centered
##########################################################################
def print_header(name, category):
    options = {0: 120, 1: 100, 2: 90, 3: 85}
    chars = int(options[category])
    print("")
    print('#' * chars)
    print("#" + name.center(chars - 2, " ") + "#")
    print('#' * chars)

# Dictionary for OCI configuration.
config = {
    "user": 'ocid1.user.oc1..lkadks...',
    "key_file": r'C:\temp\PythonDev\testadmin.pem',
    "fingerprint": '5a:04:e7:62:9a:57:7b:30:19:18:ff:3e:d9:40:53:f4',
    "tenancy": 'ocid1.tenancy.oc1..aaaaaaaa....',
    "region": 'us-ashburn-1'
}

#Validate the OCI config to be usable by the API

oci.config.validate_config(config)

def generate_signer_from_config(config):
    # Generate the signer for the API calls using the info from the config file
    signer = oci.signer.Signer(
        tenancy=config["tenancy"],
        user=config["user"],
        fingerprint=config["fingerprint"],
        private_key_file_location=config.get("key_file"),
        # pass_phrase is optional and can be None
        pass_phrase=oci.config.get_config_value_or_default(
            config, "pass_phrase"),
        # private_key_content is optional and can be None
        private_key_content=config.get("key_content")
    )
    return signer

signer = generate_signer_from_config(config)

#

identity = oci.identity.IdentityClient(config, signer=signer)

policyobj = None

tenancy = identity.get_tenancy(config["tenancy"]).data
print_header("Tenancy being updated: " + tenancy.name,0)
print(tenancy)
policies = oci.pagination.list_call_get_all_results(
            identity.list_policies,
            tenancy.id,
            retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY
        ).data

endtime = (datetime.datetime.now(pytz.utc) + datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")

skyadminlrule = "allow group SkyLease to manage all-resources in tenancy where request.utc-timestamp before '" + endtime + "'"
policystate = [skyadminlrule]

for policy in policies:
    if policy.name == 'OCISkyAdminLease':
        policyobj = policy
    
if(policyobj):
    print_header("Updating the current policy with the latest lease time",0)
    targetpolicyid = policyobj.id
    updatepolicy = oci.identity.models.UpdatePolicyDetails(statements=policystate)
    updateleasepolicy = identity.update_policy(policy_id=targetpolicyid,update_policy_details=updatepolicy)
    print(updateleasepolicy.data)
elif(policyobj == None):
    print_header("No policy found.. Creating a new policy for OCISkyAdminLease",0)
    leasepolicy = oci.identity.models.CreatePolicyDetails(compartment_id=tenancy.id,description="OCI SkyAdmin Policy",name="OCISkyAdminLease",statements=policystate)
    createleasepolicy = identity.create_policy(create_policy_details=leasepolicy)
    print(createleasepolicy.data)
